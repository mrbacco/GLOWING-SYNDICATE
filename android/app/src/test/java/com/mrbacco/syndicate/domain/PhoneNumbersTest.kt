/*
 * File:     android/app/src/test/java/com/mrbacco/syndicate/domain/PhoneNumbersTest.kt
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

class PhoneNumbersTest {

    @Test
    fun irishLocalNumberGetsCountryCode() {
        assertEquals("353871234567", PhoneNumbers.international("087 123 4567"))
    }

    @Test
    fun internationalFormatsAreKept() {
        assertEquals("353871234567", PhoneNumbers.international("+353 87 123 4567"))
        assertEquals("447700900123", PhoneNumbers.international("0044 7700 900123"))
        assertEquals("447700900123", PhoneNumbers.international("+44 (7700) 900-123"))
    }

    @Test
    fun rejectsThingsThatAreNotPhoneNumbers() {
        assertNull(PhoneNumbers.international(""))
        assertNull(PhoneNumbers.international("12345"))
        assertNull(PhoneNumbers.international("call me"))
    }
}
