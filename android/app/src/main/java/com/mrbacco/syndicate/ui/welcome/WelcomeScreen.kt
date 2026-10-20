/*
 * File:     android/app/src/main/java/com/mrbacco/syndicate/ui/welcome/WelcomeScreen.kt
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

package com.mrbacco.syndicate.ui.welcome

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.mrbacco.syndicate.R

// The launcher icon's background, so the logo looks the same here as on the home screen.
private val LogoBackground = Color.White

private data class Feature(val icon: ImageVector, val title: String, val text: String)

private val features = listOf(
    Feature(Icons.Filled.CheckCircle, "Know who's paid", "Tick off each week's payments and send a reminder by SMS or WhatsApp in one tap."),
    Feature(Icons.Filled.DateRange, "Every draw checked for you", "Results come in after each Monday, Wednesday and Saturday draw, with any prize tier."),
    Feature(Icons.Filled.Share, "Members see their own page", "Each member gets a private link to their payments and the results. Nothing to install."),
)

/** The landing page, shown each time the app opens; "Get started" leads to My syndicates. */
@Composable
fun WelcomeScreen(onGetStarted: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    Column(
        Modifier
            .fillMaxSize()
            .background(colors.background)
            .verticalScroll(rememberScrollState()),
    ) {
        // Banner, drawn behind the status bar.
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(colors.primaryContainer)
                .windowInsetsPadding(WindowInsets.statusBars)
                .padding(horizontal = 24.dp, vertical = 40.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Box(Modifier.size(112.dp).background(LogoBackground, CircleShape), contentAlignment = Alignment.Center) {
                Image(
                    painter = painterResource(R.mipmap.ic_launcher_foreground),
                    contentDescription = null,
                    // The icon art keeps a margin for launcher masks; enlarge it so the logo fills the circle.
                    modifier = Modifier.size(112.dp).graphicsLayer(scaleX = 1.45f, scaleY = 1.45f),
                )
            }
            Spacer(Modifier.height(20.dp))
            Text(
                "Syndicate",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = colors.onPrimaryContainer,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Run your lotto syndicate without the spreadsheet.",
                style = MaterialTheme.typography.titleMedium,
                textAlign = TextAlign.Center,
                color = colors.onPrimaryContainer,
            )
        }

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            features.forEach { FeatureCard(it) }
        }

        Spacer(Modifier.height(12.dp))
        Column(
            modifier = Modifier
                .padding(horizontal = 16.dp)
                .padding(bottom = 16.dp)
                .navigationBarsPadding(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Button(onClick = onGetStarted, modifier = Modifier.fillMaxWidth().height(52.dp)) {
                Text("Get started", style = MaterialTheme.typography.titleMedium)
            }
            Text(
                "Syndicate only keeps a record. It never takes payments or buys tickets.",
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                color = colors.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun FeatureCard(feature: Feature) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Icon(feature.icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(28.dp))
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(feature.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(feature.text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}
