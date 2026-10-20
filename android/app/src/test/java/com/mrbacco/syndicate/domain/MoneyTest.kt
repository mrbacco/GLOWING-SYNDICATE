/*
 * File:     android/app/src/test/java/com/mrbacco/syndicate/domain/MoneyTest.kt
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

class MoneyTest {

    @Test
    fun parsesEuroAmounts() {
        assertEquals(500, Money.parseEuro("5"))
        assertEquals(550, Money.parseEuro("5.5"))
        assertEquals(250, Money.parseEuro("2,50"))
        assertEquals(300, Money.parseEuro("€3.00"))
    }

    @Test
    fun rejectsBadAmounts() {
        assertNull(Money.parseEuro(""))
        assertNull(Money.parseEuro("abc"))
        assertNull(Money.parseEuro("0"))
        assertNull(Money.parseEuro("-2"))
        assertNull(Money.parseEuro("1.234"))
    }
}
