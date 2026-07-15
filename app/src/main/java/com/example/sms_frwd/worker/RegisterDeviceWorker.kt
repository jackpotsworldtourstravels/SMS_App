package com.example.sms_frwd.worker

import android.content.Context
import android.os.Build
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.sms_frwd.BuildConfig
import com.example.sms_frwd.data.TokenStore
import com.example.sms_frwd.network.RegisterDeviceRequest
import com.example.sms_frwd.network.RetrofitClient
import java.util.UUID

class RegisterDeviceWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    companion object {
        const val UNIQUE_WORK_NAME = "register-device"
        private const val TAG = "RegisterDeviceWorker"
    }

    override suspend fun doWork(): Result {
        val tokenStore = TokenStore(applicationContext)

        // Already registered — nothing to do. (RegisterDeviceWorker is
        // enqueued with ExistingWorkPolicy.KEEP, but this guards against
        // a stray manual re-run too.)
        if (tokenStore.getApiTokenOnce() != null) {
            return Result.success()
        }

        val deviceId = tokenStore.getDeviceIdOnce() ?: UUID.randomUUID().toString()

        return try {
            val response = RetrofitClient.apiService.registerDevice(
                RegisterDeviceRequest(
                    device_id = deviceId,
                    device_name = "${Build.MANUFACTURER} ${Build.MODEL}",
                    manufacturer = Build.MANUFACTURER,
                    model = Build.MODEL,
                    android_version = Build.VERSION.RELEASE,
                    app_version_name = BuildConfig.VERSION_NAME,
                    app_version_code = BuildConfig.VERSION_CODE
                )
            )

            val body = response.body()
            if (response.isSuccessful && body != null) {
                tokenStore.save(body.device_id, body.api_token)
                Log.d(TAG, "Device registered: ${body.device_id}")
                Result.success()
            } else if (response.code() in 400..499) {
                // Bad request / device revoked — retrying won't help.
                Log.e(TAG, "Registration rejected: HTTP ${response.code()}")
                Result.failure()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Registration failed, will retry", e)
            Result.retry()
        }
    }
}
