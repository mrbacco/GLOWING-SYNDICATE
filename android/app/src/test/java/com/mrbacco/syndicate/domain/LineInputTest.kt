/*
 * File:     android/app/src/test/java/com/mrbacco/syndicate/domain/LineInputTest.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class LineInputTest {

    private fun parse(text: String) = LineInput.parse(text, count = 6, max = 45)

    @Test
    fun parsesValidLines() {
        assertEquals(listOf(3, 12, 24, 27, 38, 41), parse("41 3 12, 24 27 38"))
        assertEquals(listOf(1, 2, 3, 4, 5, 6), parse("1;2;3;4;5;6"))
    }

    @Test
    fun rejectsInvalidLines() {
        assertNull(parse("1 2 3 4 5"))        // too few
        assertNull(parse("1 2 3 4 5 5"))      // duplicate
        assertNull(parse("1 2 3 4 5 46"))     // out of range for a 45-ball game
        assertNull(parse("1 2 3 4 5 x"))      // not a number
    }

    @Test
    fun usesTheLimitsItIsGiven() {
        assertEquals(listOf(1, 2, 3, 4, 5, 47), LineInput.parse("1 2 3 4 5 47", count = 6, max = 47))
    }
}
