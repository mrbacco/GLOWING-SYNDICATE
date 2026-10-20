/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/data/AppContainer.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.data

import com.mrbacco.syndicate.BuildConfig

/** Holds the app-wide objects. The backend address is set per build type in app/build.gradle.kts. */
object AppContainer {
    val repository: SyndicateRepository by lazy { SyndicateRepository.create(BuildConfig.API_BASE_URL) }
}
