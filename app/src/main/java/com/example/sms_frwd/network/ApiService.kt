package com.example.sms_frwd.network

import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST

@Serializable
data class RegisterDeviceRequest(
    val device_id: String,
    val device_name: String? = null,
    val manufacturer: String? = null,
    val model: String? = null,
    val android_version: String? = null,
    val app_version_name: String? = null,
    val app_version_code: Int? = null
)

@Serializable
data class RegisterDeviceResponse(
    val device_id: String,
    val api_token: String,
    val heartbeat_interval_seconds: Int,
    val server_time: String
)

@Serializable
data class HeartbeatRequest(
    val app_version_name: String? = null,
    val app_version_code: Int? = null
)

@Serializable
data class HeartbeatResponse(
    val status: String,
    val server_time: String,
    val heartbeat_interval_seconds: Int
)

@Serializable
data class MessageItem(
    val client_message_id: String,
    val sender_raw: String,
    val sender_matched: String,
    val body: String,
    val received_at: String
)

@Serializable
data class MessagesRequest(
    val messages: List<MessageItem>
)

@Serializable
data class MessageResult(
    val client_message_id: String,
    val status: String,
    val category: String,
    val message_id: Long? = null
)

@Serializable
data class MessagesResponse(
    val accepted: Int,
    val duplicates: Int,
    val rejected: Int,
    val results: List<MessageResult>
)

@Serializable
data class DeviceConfigResponse(
    val heartbeat_interval_seconds: Int,
    val bank_sender_ids: List<String>,
    val min_app_version_code: Int
)

interface ApiService {

    @POST("api/v1/register-device")
    suspend fun registerDevice(
        @Body request: RegisterDeviceRequest
    ): Response<RegisterDeviceResponse>

    @POST("api/v1/heartbeat")
    suspend fun heartbeat(
        @Header("Authorization") authorization: String,
        @Body request: HeartbeatRequest
    ): Response<HeartbeatResponse>

    @POST("api/v1/messages")
    suspend fun uploadMessages(
        @Header("Authorization") authorization: String,
        @Body request: MessagesRequest
    ): Response<MessagesResponse>

    @GET("api/v1/device-config")
    suspend fun deviceConfig(
        @Header("Authorization") authorization: String
    ): Response<DeviceConfigResponse>
}
