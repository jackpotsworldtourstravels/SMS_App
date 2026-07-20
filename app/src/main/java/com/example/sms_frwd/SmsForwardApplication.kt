package com.example.sms_frwd

import android.Manifest
import android.app.Application
import android.content.Intent
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
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

        startSmsMonitorServiceIfPermitted()

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

    // Only meaningful once RECEIVE_SMS is granted (first app launch hasn't
    // asked yet). MainActivity starts the service directly the moment
    // permission is granted, so this covers every later process restart.
    fun startSmsMonitorServiceIfPermitted() {
        val hasSmsPermission = ContextCompat.checkSelfPermission(
            this, Manifest.permission.RECEIVE_SMS
        ) == PackageManager.PERMISSION_GRANTED

        if (hasSmsPermission) {
            ContextCompat.startForegroundService(
                this, Intent(this, SmsMonitorService::class.java)
            )
        }
    }
}
