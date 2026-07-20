package com.example.sms_frwd

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

// MIUI (and other OEM battery managers) kill this app's process aggressively
// even with Autostart/background-start permissions granted, which prevents
// SmsReceiver's manifest-registered broadcast receiver from ever being woken
// to catch an incoming SMS. Keeping a foreground service alive sidesteps
// that: the process is never fully stopped, so the broadcast reaches
// SmsReceiver immediately instead of depending on the OS to relaunch a dead
// process for it.
class SmsMonitorService : Service() {

    companion object {
        private const val CHANNEL_ID = "sms_monitor_channel"
        private const val NOTIFICATION_ID = 1001
    }

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // START_STICKY: if the OS still kills this process under memory
        // pressure, it recreates the service (without redelivering the
        // last intent) as soon as resources allow.
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "SMS Monitoring",
                NotificationManager.IMPORTANCE_MIN
            ).apply {
                description = "Keeps Transaction SMS running to forward bank messages"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java)
                .createNotificationChannel(channel)
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText("Monitoring for bank transaction SMS")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
    }
}
