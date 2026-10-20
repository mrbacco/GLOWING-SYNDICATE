/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/theme/Theme.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// The whole UI uses three colours: green (brand, matched numbers), gold (bonus ball,
// things that need attention) and neutral grey (backgrounds, text). Every scheme slot is
// set so Material does not fill the gaps with its default purple and red.
// Keep surfaceContainerHighest (card background) different from surfaceVariant: if they are
// equal, Material gives cards the faded onSurfaceVariant text colour instead of onSurface.
private val Green = Color(0xFF0B6E4F)
private val GreenLight = Color(0xFF6FD3A8)
private val GreenTint = Color(0xFFD3EFE3)
private val GreenDeep = Color(0xFF00382A)
private val GreenDark = Color(0xFF0E4D39)

private val Gold = Color(0xFFFFD54F)
private val GoldDeep = Color(0xFF7A5F00)
private val GoldInk = Color(0xFF261A00)
private val GoldDark = Color(0xFF5C4A00)

private val LightColors = lightColorScheme(
    primary = Green,
    onPrimary = Color.White,
    primaryContainer = GreenTint,
    onPrimaryContainer = GreenDeep,
    inversePrimary = GreenLight,
    secondary = GoldDeep,
    onSecondary = Color.White,
    secondaryContainer = Gold,
    onSecondaryContainer = GoldInk,
    tertiary = GoldDeep,
    onTertiary = Color.White,
    tertiaryContainer = Gold,
    onTertiaryContainer = GoldInk,
    error = GoldDeep,
    onError = Color.White,
    errorContainer = Gold,
    onErrorContainer = GoldInk,
    background = Color(0xFFFAFAFA),
    onBackground = Color(0xFF1B1B1B),
    surface = Color(0xFFFAFAFA),
    onSurface = Color(0xFF1B1B1B),
    surfaceVariant = Color(0xFFE6E6E6),
    onSurfaceVariant = Color(0xFF5C5C5C),
    surfaceTint = Color(0xFF8A8A8A),
    inverseSurface = Color(0xFF303030),
    inverseOnSurface = Color(0xFFF2F2F2),
    outline = Color(0xFF8A8A8A),
    outlineVariant = Color(0xFFD0D0D0),
    surfaceBright = Color(0xFFFAFAFA),
    surfaceDim = Color(0xFFDADADA),
    surfaceContainerLowest = Color.White,
    surfaceContainerLow = Color(0xFFF4F4F4),
    surfaceContainer = Color(0xFFEEEEEE),
    surfaceContainerHigh = Color(0xFFE9E9E9),
    surfaceContainerHighest = Color(0xFFE4E4E4),
)

private val DarkColors = darkColorScheme(
    primary = GreenLight,
    onPrimary = GreenDeep,
    primaryContainer = GreenDark,
    onPrimaryContainer = GreenTint,
    inversePrimary = Green,
    secondary = Gold,
    onSecondary = GoldInk,
    secondaryContainer = GoldDark,
    onSecondaryContainer = Gold,
    tertiary = Gold,
    onTertiary = GoldInk,
    tertiaryContainer = GoldDark,
    onTertiaryContainer = Gold,
    error = Gold,
    onError = GoldInk,
    errorContainer = GoldDark,
    onErrorContainer = Gold,
    background = Color(0xFF121212),
    onBackground = Color(0xFFE6E6E6),
    surface = Color(0xFF121212),
    onSurface = Color(0xFFE6E6E6),
    surfaceVariant = Color(0xFF2C2C2C),
    onSurfaceVariant = Color(0xFFB8B8B8),
    surfaceTint = Color(0xFF8A8A8A),
    inverseSurface = Color(0xFFE6E6E6),
    inverseOnSurface = Color(0xFF303030),
    outline = Color(0xFF8A8A8A),
    outlineVariant = Color(0xFF444444),
    surfaceBright = Color(0xFF383838),
    surfaceDim = Color(0xFF121212),
    surfaceContainerLowest = Color(0xFF0D0D0D),
    surfaceContainerLow = Color(0xFF1A1A1A),
    surfaceContainer = Color(0xFF1E1E1E),
    surfaceContainerHigh = Color(0xFF262626),
    surfaceContainerHighest = Color(0xFF2E2E2E),
)

@Composable
fun SyndicateTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}
