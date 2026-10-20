/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/data/SyndicateRepository.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.data

import com.mrbacco.syndicate.data.model.GameRules
import com.mrbacco.syndicate.data.model.LineNumbers
import com.mrbacco.syndicate.data.model.LinesScreen
import com.mrbacco.syndicate.data.model.MemberChanges
import com.mrbacco.syndicate.data.model.MembersScreen
import com.mrbacco.syndicate.data.model.NewMember
import com.mrbacco.syndicate.data.model.NewSyndicate
import com.mrbacco.syndicate.data.model.ResultsScreen
import com.mrbacco.syndicate.data.model.SyndicateListScreen
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonNamingStrategy
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

/** A failed call, with a message that can be shown to the user as it is. */
class ApiException(message: String, cause: Throwable? = null) : Exception(message, cause)

/**
 * The single entry point the screens use for data. Every call goes to the backend, which does
 * all the working out; failures come back as [ApiException].
 */
class SyndicateRepository(private val api: SyndicateApi) {

    suspend fun syndicateList(): SyndicateListScreen = call { api.syndicateList() }
    suspend fun membersScreen(syndicateId: String): MembersScreen = call { api.membersScreen(syndicateId) }
    suspend fun linesScreen(syndicateId: String): LinesScreen = call { api.linesScreen(syndicateId) }
    suspend fun resultsScreen(syndicateId: String): ResultsScreen = call { api.resultsScreen(syndicateId) }
    suspend fun rules(): GameRules = call { api.rules() }

    suspend fun addSyndicate(name: String, weeklyCostCents: Int) =
        call { api.addSyndicate(NewSyndicate(name.trim(), weeklyCostCents)) }

    suspend fun addMember(syndicateId: String, name: String, phone: String?) =
        call { api.addMember(syndicateId, NewMember(name.trim(), phone?.trim()?.ifEmpty { null })) }

    /** A null or empty [phone] removes the member's number. */
    suspend fun updateMember(memberId: String, name: String, phone: String?) =
        call { api.updateMember(memberId, MemberChanges(name.trim(), phone?.trim().orEmpty())) }

    suspend fun deleteMember(memberId: String) = call { api.deleteMember(memberId) }

    suspend fun setPaid(memberId: String, weekStart: String, paid: Boolean) = call {
        if (paid) api.markPaid(memberId, weekStart) else api.markUnpaid(memberId, weekStart)
    }

    suspend fun addLine(syndicateId: String, numbers: List<Int>) =
        call { api.addLine(syndicateId, LineNumbers(numbers)) }

    suspend fun updateLine(lineId: String, numbers: List<Int>) = call { api.updateLine(lineId, LineNumbers(numbers)) }

    suspend fun deleteLine(lineId: String) = call { api.deleteLine(lineId) }

    private suspend fun <T> call(block: suspend () -> T): T = try {
        block()
    } catch (e: IOException) {
        throw ApiException("Can't reach the server. Check that it's running, then try again.", e)
    } catch (e: HttpException) {
        throw ApiException(serverMessage(e) ?: "The server had a problem (error ${e.code()}).", e)
    }

    companion object {
        @OptIn(ExperimentalSerializationApi::class)
        val json = Json {
            ignoreUnknownKeys = true // the server may add fields before the app knows them
            namingStrategy = JsonNamingStrategy.SnakeCase
            explicitNulls = false
        }

        fun create(baseUrl: String): SyndicateRepository {
            val client = OkHttpClient.Builder()
                .connectTimeout(5, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .build()
            val retrofit = Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
                .build()
            return SyndicateRepository(retrofit.create(SyndicateApi::class.java))
        }

        /** FastAPI errors are {"detail": "text"} or {"detail": [{"msg": "text"}, ...]}. */
        internal fun serverMessage(e: HttpException): String? = runCatching {
            val body = e.response()?.errorBody()?.string() ?: return null
            when (val detail = json.parseToJsonElement(body).jsonObject["detail"]) {
                is JsonPrimitive -> detail.contentOrNull
                is JsonArray -> (detail.firstOrNull() as? JsonObject)?.get("msg")
                    ?.let { (it as? JsonPrimitive)?.contentOrNull }
                    ?.removePrefix("Value error, ")
                else -> null
            }
        }.getOrNull()
    }
}
