/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/data/AppPrefs.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.data

import android.content.Context

/** Small settings kept on the phone. Everything else lives on the server. */
class AppPrefs(context: Context) {

    private val prefs = context.applicationContext.getSharedPreferences("syndicate", Context.MODE_PRIVATE)

    /** Whether the welcome page was dismissed with "Get started"; it is only shown until then. */
    var welcomeSeen: Boolean
        get() = prefs.getBoolean(KEY_WELCOME_SEEN, false)
        set(value) = prefs.edit().putBoolean(KEY_WELCOME_SEEN, value).apply()

    private companion object {
        const val KEY_WELCOME_SEEN = "welcome_seen"
    }
}
