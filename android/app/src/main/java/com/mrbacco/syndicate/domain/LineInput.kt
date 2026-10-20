/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/domain/LineInput.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.domain

/**
 * Reads a line typed by the user, for a quick error message before anything is sent.
 * The limits come from the server's game rules, and the server checks the line again.
 */
object LineInput {

    /** Parses "3 12 24 27 38 41" (spaces, commas or semicolons). Null if it is not [count] different numbers from 1 to [max]. */
    fun parse(text: String, count: Int, max: Int): List<Int>? {
        val numbers = text.split(' ', ',', ';')
            .filter { it.isNotBlank() }
            .map { it.trim().toIntOrNull() ?: return null }
        val valid = numbers.size == count &&
            numbers.toSet().size == count &&
            numbers.all { it in 1..max }
        return if (valid) numbers.sorted() else null
    }
}
