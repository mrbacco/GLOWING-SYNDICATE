/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/navigation/SyndicateNavHost.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.mrbacco.syndicate.data.AppPrefs
import com.mrbacco.syndicate.ui.detail.SyndicateDetailScreen
import com.mrbacco.syndicate.ui.list.SyndicateListScreen
import com.mrbacco.syndicate.ui.welcome.WelcomeScreen

private object Routes {
    const val WELCOME = "welcome"
    const val LIST = "syndicates"
    const val DETAIL = "syndicate/{id}"
    fun detail(id: String) = "syndicate/$id"
}

@Composable
fun SyndicateNavHost() {
    val navController = rememberNavController()
    val prefs = AppPrefs(LocalContext.current)
    // Decided once, so the start screen doesn't change under the user while the app is open.
    val start = remember { if (prefs.welcomeSeen) Routes.LIST else Routes.WELCOME }
    NavHost(navController = navController, startDestination = start) {
        composable(Routes.WELCOME) {
            WelcomeScreen(onGetStarted = {
                prefs.welcomeSeen = true
                // Replace the welcome page, so Back from the list leaves the app.
                navController.navigate(Routes.LIST) { popUpTo(Routes.WELCOME) { inclusive = true } }
            })
        }
        composable(Routes.LIST) {
            SyndicateListScreen(onOpen = { id -> navController.navigate(Routes.detail(id)) })
        }
        composable(Routes.DETAIL) { entry ->
            val id = entry.arguments?.getString("id").orEmpty()
            SyndicateDetailScreen(syndicateId = id, onBack = { navController.popBackStack() })
        }
    }
}
