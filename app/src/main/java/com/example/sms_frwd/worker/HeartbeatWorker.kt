package com.example.sms_frwd.worker

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.sms_frwd.BuildConfig
import com.example.sms_frwd.data.TokenStore
import com.example.sms_frwd.network.HeartbeatRequest
import com.example.sms_frwd.network.RetrofitClient

class HeartbeatWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    companion object {
        const val UNIQUE_WORK_NAME = "heartbeat"
        private const val TAG = "HeartbeatWorker"
    }

    override suspend fun doWork(): Result {
        val tokenStore = TokenStore(applicationContext)
        val token = tokenStore.getApiTokenOnce()
            ?: return Result.retry() // not registered yet, try again next cycle

        return try {
            val response = RetrofitClient.apiService.heartbeat(
                authorization = "Bearer $token",
                request = HeartbeatRequest(
                    app_version_name = BuildConfig.VERSION_NAME,
                    app_version_code = BuildConfig.VERSION_CODE
                )
            )

            if (response.isSuccessful) {
                Log.d(TAG, "Heartbeat sent successfully: HTTP ${response.code()}")
                Result.success()
            } else if (response.code() == 401) {
                // Token revoked or invalid — re-registering requires a
                // fresh RegisterDeviceWorker enqueue, which the app's
                // startup path handles; nothing more this worker can do.
                Log.w(TAG, "Heartbeat rejected: token invalid/revoked")
                Result.failure()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Heartbeat failed, will retry", e)
            Result.retry()
        }
    }
}
