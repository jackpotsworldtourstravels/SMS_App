package com.example.sms_frwd

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
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
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        permissionsGranted.value = hasSmsPermissions()

        if (permissionsGranted.value) {
            requestIgnoreBatteryOptimizations()
        } else {
            permissionLauncher.launch(SMS_PERMISSIONS)
        }

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
        if (granted != permissionsGranted.value) {
            permissionsGranted.value = granted
            if (granted) {
                requestIgnoreBatteryOptimizations()
            }
        }
    }

    private fun hasSmsPermissions(): Boolean =
        SMS_PERMISSIONS.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
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
