/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/data/SyndicateApi.kt
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
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path

/** The backend's HTTP API (backend/README.md). */
interface SyndicateApi {

    @GET("screens/syndicates")
    suspend fun syndicateList(): SyndicateListScreen

    @GET("screens/syndicates/{id}/members")
    suspend fun membersScreen(@Path("id") syndicateId: String): MembersScreen

    @GET("screens/syndicates/{id}/lines")
    suspend fun linesScreen(@Path("id") syndicateId: String): LinesScreen

    @GET("screens/syndicates/{id}/results")
    suspend fun resultsScreen(@Path("id") syndicateId: String): ResultsScreen

    @GET("rules")
    suspend fun rules(): GameRules

    @POST("syndicates")
    suspend fun addSyndicate(@Body body: NewSyndicate)

    @POST("syndicates/{id}/members")
    suspend fun addMember(@Path("id") syndicateId: String, @Body body: NewMember)

    @PATCH("members/{id}")
    suspend fun updateMember(@Path("id") memberId: String, @Body body: MemberChanges)

    @DELETE("members/{id}")
    suspend fun deleteMember(@Path("id") memberId: String)

    @PUT("members/{id}/payments/{week}")
    suspend fun markPaid(@Path("id") memberId: String, @Path("week") weekStart: String)

    @DELETE("members/{id}/payments/{week}")
    suspend fun markUnpaid(@Path("id") memberId: String, @Path("week") weekStart: String)

    @POST("syndicates/{id}/lines")
    suspend fun addLine(@Path("id") syndicateId: String, @Body body: LineNumbers)

    @PUT("lines/{id}")
    suspend fun updateLine(@Path("id") lineId: String, @Body body: LineNumbers)

    @DELETE("lines/{id}")
    suspend fun deleteLine(@Path("id") lineId: String)
}
