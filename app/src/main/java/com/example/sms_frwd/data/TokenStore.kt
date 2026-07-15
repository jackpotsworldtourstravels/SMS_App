package com.example.sms_frwd.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(
    name = "sms_frwd_tokens"
)

class TokenStore(private val context: Context) {

    companion object {
        private val KEY_DEVICE_ID = stringPreferencesKey("device_id")
        private val KEY_API_TOKEN = stringPreferencesKey("api_token")
    }

    val deviceId: Flow<String?> = context.dataStore.data.map { it[KEY_DEVICE_ID] }
    val apiToken: Flow<String?> = context.dataStore.data.map { it[KEY_API_TOKEN] }

    suspend fun getDeviceIdOnce(): String? = deviceId.first()
    suspend fun getApiTokenOnce(): String? = apiToken.first()

    suspend fun save(deviceId: String, apiToken: String) {
        context.dataStore.edit { prefs ->
            prefs[KEY_DEVICE_ID] = deviceId
            prefs[KEY_API_TOKEN] = apiToken
        }
    }
}
