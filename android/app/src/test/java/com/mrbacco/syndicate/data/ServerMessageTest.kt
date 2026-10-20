/*
 * File:     android/app/src/test/java/com/mrbacco/syndicate/data/ServerMessageTest.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.data

import com.mrbacco.syndicate.data.model.MembersScreen
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response

class ServerMessageTest {

    private fun error(code: Int, body: String) =
        HttpException(Response.error<Any>(code, body.toResponseBody("application/json".toMediaType())))

    @Test
    fun readsPlainDetail() {
        assertEquals("Numbers must be from 1 to 45.", SyndicateRepository.serverMessage(error(422, """{"detail":"Numbers must be from 1 to 45."}""")))
    }

    @Test
    fun readsValidationErrors() {
        val body = """{"detail":[{"type":"value_error","loc":["body","phone"],"msg":"Value error, That doesn't look like a phone number."}]}"""
        assertEquals("That doesn't look like a phone number.", SyndicateRepository.serverMessage(error(422, body)))
    }

    @Test
    fun ignoresBodiesItDoesNotUnderstand() {
        assertNull(SyndicateRepository.serverMessage(error(500, "Internal Server Error")))
    }

    @Test
    fun readsScreensInTheServersFormat() {
        // A trimmed copy of GET /screens/syndicates/s-office/members; unknown fields are ignored.
        val body = """{"syndicate":{"id":"s-office","name":"Office Syndicate","weekly_cost_cents":500,"draw_days":["WED","SAT"]},
            "week_start":"2026-10-19","summary":{"title":"Week of 19 Oct","lines":["2 of 4 members paid this week"]},
            "members":[{"id":"m2","name":"Ciarán","phone":null,"whatsapp_number":null,"paid_this_week":false,
            "weeks_owed":1,"amount_owed_cents":500,"status":"Owes €5.00 (1 week)","message":"Hi","new_field":1}],
            "empty_text":null}"""
        val screen = SyndicateRepository.json.decodeFromString<MembersScreen>(body)
        assertEquals("Owes €5.00 (1 week)", screen.members.single().status)
        assertEquals(500, screen.syndicate.weeklyCostCents)
        assertNull(screen.members.single().phone)
    }
}
