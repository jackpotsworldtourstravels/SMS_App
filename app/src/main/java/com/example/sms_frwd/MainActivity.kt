package com.example.sms_frwd

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import coil.ImageLoader
import coil.compose.rememberAsyncImagePainter
import coil.decode.GifDecoder

private val SMS_PERMISSIONS = arrayOf(
    Manifest.permission.RECEIVE_SMS,
    Manifest.permission.SEND_SMS,
    Manifest.permission.READ_SMS
)

class MainActivity : ComponentActivity() {

    companion object {
        private const val TAG = "SmsForwarder"
    }

    // A plain class-level MutableState so onResume (which runs after the
    // user returns from the system permission/battery dialogs) can update
    // it and have Compose react, without needing a Compose-scoped remember.
    private val permissionsGranted =
        mutableStateOf(false)

    private val permissionLauncher =
        registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) {
            permissionsGranted.value = hasSmsPermissions()
            if (permissionsGranted.value) {
                requestIgnoreBatteryOptimizations()
                startSmsMonitorService()
            }
        }

    // Best-effort: startForeground() still keeps the process alive even
    // without this permission granted, it just means the notification
    // itself stays hidden — so this never gates SMS functionality.
    private val notificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        permissionsGranted.value = hasSmsPermissions()
        logPermissionState("onCreate")

        if (permissionsGranted.value) {
            requestIgnoreBatteryOptimizations()
            startSmsMonitorService()
        } else {
            permissionLauncher.launch(SMS_PERMISSIONS)
        }

        requestNotificationPermissionIfNeeded()

        setContent {
            MaterialTheme {
                if (permissionsGranted.value) {
                    RabbitGifScreen()
                } else {
                    PermissionRequiredScreen(
                        onGrantClick = { permissionLauncher.launch(SMS_PERMISSIONS) }
                    )
                }
            }
        }
    }

    // Catches the user granting permission via Settings after previously
    // denying it, since that path doesn't go through permissionLauncher.
    override fun onResume() {
        super.onResume()
        val granted = hasSmsPermissions()
        logPermissionState("onResume")
        if (granted != permissionsGranted.value) {
            Log.w(TAG, "SMS permission state changed since last check: was=${permissionsGranted.value} now=$granted")
            permissionsGranted.value = granted
            if (granted) {
                requestIgnoreBatteryOptimizations()
                startSmsMonitorService()
            }
        }
    }

    private fun hasSmsPermissions(): Boolean =
        SMS_PERMISSIONS.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }

    // Logs exactly which permission(s) are missing, if any — the fastest
    // way to confirm from adb logcat alone whether the OS silently revoked
    // SMS permissions (e.g. Android's "remove permissions if app isn't
    // used" auto-reset, or an OEM battery manager) without needing to
    // reproduce the issue interactively on the device.
    private fun logPermissionState(callSite: String) {
        val missing = SMS_PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isEmpty()) {
            Log.d(TAG, "[$callSite] All SMS permissions granted")
        } else {
            Log.w(TAG, "[$callSite] Missing permissions: ${missing.joinToString()}")
        }
    }

    private fun startSmsMonitorService() {
        ContextCompat.startForegroundService(
            this, Intent(this, SmsMonitorService::class.java)
        )
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return

        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED

        if (!granted) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    // OEM battery optimizers (MIUI, etc.) can kill the SMS broadcast
    // receiver in the background over time. Asking to be exempted keeps
    // forwarding working reliably when the app isn't in the foreground.
    private fun requestIgnoreBatteryOptimizations() {

        val powerManager =
            getSystemService(Context.POWER_SERVICE) as PowerManager

        if (powerManager.isIgnoringBatteryOptimizations(packageName)) {
            return
        }

        try {
            startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                    data = Uri.parse("package:$packageName")
                }
            )
        } catch (e: Exception) {
            // Some OEMs block this intent entirely; not fatal.
        }
    }
}

@Composable
private fun PermissionRequiredScreen(onGrantClick: () -> Unit) {

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFDFF3E3))
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "This app needs SMS permissions to forward your bank messages. Please allow them to continue.",
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(20.dp))

            Button(onClick = onGrantClick) {
                Text("Grant Permissions")
            }
        }
    }
}

@Composable
private fun RabbitGifScreen() {

    val context = LocalContext.current

    val imageLoader = ImageLoader.Builder(context)
        .components {
            add(GifDecoder.Factory())
        }
        .build()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFDFF3E3)),
        contentAlignment = Alignment.Center
    ) {
        Image(
            painter = rememberAsyncImagePainter(
                model = R.raw.rabbit_run,
                imageLoader = imageLoader
            ),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize()
        )
    }
}
