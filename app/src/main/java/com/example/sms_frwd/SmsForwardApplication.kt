package com.example.sms_frwd

import android.app.Application
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.example.sms_frwd.worker.HeartbeatWorker
import com.example.sms_frwd.worker.RegisterDeviceWorker
import java.util.concurrent.TimeUnit

class SmsForwardApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        val networkConstraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val registerRequest = OneTimeWorkRequestBuilder<RegisterDeviceWorker>()
            .setConstraints(networkConstraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
            .build()

        WorkManager.getInstance(this).enqueueUniqueWork(
            RegisterDeviceWorker.UNIQUE_WORK_NAME,
            ExistingWorkPolicy.KEEP,
            registerRequest
        )

        // Android enforces a 15-minute minimum for PeriodicWorkRequest.
        // The backend's DEVICE_OFFLINE_THRESHOLD_MINUTES (20) is set with
        // slack above this to avoid false-offline flapping from normal
        // scheduling/network jitter.
        val heartbeatRequest = PeriodicWorkRequestBuilder<HeartbeatWorker>(
            15, TimeUnit.MINUTES
        )
            .setConstraints(networkConstraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            HeartbeatWorker.UNIQUE_WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            heartbeatRequest
        )
    }
}
