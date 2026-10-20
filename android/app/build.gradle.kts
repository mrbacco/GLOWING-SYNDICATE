/*
 * File:     android/app/build.gradle.kts
 * Author:   mrbacco04@gmail.com
 * GitHub:   https://github.com/mrbacco
 * Created:  2026-10-20
 * Updated:  2026-10-20
 * Project:  SYNDICATE
 * License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
 */

import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

// Server address and access key come from local.properties, which git never uploads:
//   syndicate.apiUrl=https://<hosted server>/   (release builds)
//   syndicate.apiKey=<the server's SYNDICATE_API_KEY>
//   syndicate.debugApiUrl=...                    (optional: point debug builds elsewhere)
//   syndicate.debugApiKey=...
val localProps = Properties().apply {
    rootProject.file("local.properties").takeIf { it.exists() }?.inputStream()?.use { load(it) }
}
fun local(name: String, default: String = ""): String = localProps.getProperty(name, default).trim()
fun quoted(value: String): String = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""

android {
    namespace = "com.mrbacco.syndicate"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.mrbacco.syndicate"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        debug {
            // By default the backend on the PC: `adb reverse tcp:8000 tcp:8000` makes the phone's
            // (or the emulator's) 127.0.0.1:8000 reach the PC, over USB or wireless debugging.
            buildConfigField("String", "API_BASE_URL", quoted(local("syndicate.debugApiUrl", "http://127.0.0.1:8000/")))
            buildConfigField("String", "API_KEY", quoted(local("syndicate.debugApiKey")))
        }
        release {
            // The hosted backend (HTTPS only, see network_security_config.xml).
            buildConfigField("String", "API_BASE_URL", quoted(local("syndicate.apiUrl", "https://syndicate.invalid/")))
            buildConfigField("String", "API_KEY", quoted(local("syndicate.apiKey")))
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)

    implementation(libs.kotlinx.serialization.json)
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)
    implementation(libs.okhttp)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.core)
    debugImplementation(libs.androidx.compose.ui.tooling)

    testImplementation(libs.junit)
}
