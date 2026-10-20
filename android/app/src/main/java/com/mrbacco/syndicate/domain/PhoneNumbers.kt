/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/domain/PhoneNumbers.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.domain

object PhoneNumbers {

    /**
     * The number as international digits without "+", as WhatsApp links need it:
     * "087 123 4567" -> "353871234567" (Irish by default), "+44 7700 900123" -> "447700900123".
     * Returns null if it does not look like a phone number.
     */
    fun international(raw: String, defaultCountryCode: String = "353"): String? {
        val trimmed = raw.trim()
        if (trimmed.any { !it.isDigit() && it !in "+ -()." }) return null
        val digits = trimmed.filter { it.isDigit() }
        val result = when {
            trimmed.startsWith("+") -> digits
            digits.startsWith("00") -> digits.drop(2)
            digits.startsWith("0") -> defaultCountryCode + digits.drop(1)
            else -> digits
        }
        return result.takeIf { it.length in 8..15 }
    }
}
