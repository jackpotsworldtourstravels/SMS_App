package com.example.sms_frwd.worker

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.sms_frwd.data.TokenStore
import com.example.sms_frwd.network.MessageItem
import com.example.sms_frwd.network.MessagesRequest
import com.example.sms_frwd.network.RetrofitClient
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class UploadMessageWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    companion object {
        private const val TAG = "UploadMessageWorker"

        const val KEY_CLIENT_MESSAGE_ID = "client_message_id"
        const val KEY_SENDER_RAW = "sender_raw"
        const val KEY_SENDER_MATCHED = "sender_matched"
        const val KEY_BODY = "body"
        const val KEY_RECEIVED_AT_MILLIS = "received_at_millis"

        fun isoFromMillis(epochMillis: Long): String {
            val format = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
            format.timeZone = TimeZone.getTimeZone("UTC")
            return format.format(Date(epochMillis))
        }
    }

    override suspend fun doWork(): Result {
        val tokenStore = TokenStore(applicationContext)
        val token = tokenStore.getApiTokenOnce() ?: return Result.retry()

        val clientMessageId = inputData.getString(KEY_CLIENT_MESSAGE_ID) ?: return Result.failure()
        val senderRaw = inputData.getString(KEY_SENDER_RAW) ?: return Result.failure()
        val senderMatched = inputData.getString(KEY_SENDER_MATCHED) ?: return Result.failure()
        val body = inputData.getString(KEY_BODY) ?: return Result.failure()
        val receivedAtMillis = inputData.getLong(KEY_RECEIVED_AT_MILLIS, -1L)
        if (receivedAtMillis < 0) return Result.failure()

        return try {
            val response = RetrofitClient.apiService.uploadMessages(
                authorization = "Bearer $token",
                request = MessagesRequest(
                    messages = listOf(
                        MessageItem(
                            client_message_id = clientMessageId,
                            sender_raw = senderRaw,
                            sender_matched = senderMatched,
                            body = body,
                            received_at = isoFromMillis(receivedAtMillis)
                        )
                    )
                )
            )

            if (response.isSuccessful) {
                Log.d(TAG, "Uploaded message $clientMessageId: ${response.body()}")
                Result.success()
            } else if (response.code() == 401) {
                Log.w(TAG, "Upload rejected: token invalid/revoked")
                Result.failure()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Upload failed, will retry", e)
            Result.retry()
        }
    }
}
