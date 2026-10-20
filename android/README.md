<!--
File:     android/README.md
Author:   mrbacco04@gmail.com
GitHub:   https://github.com/mrbacco
Created:  2026-10-20
Updated:  2026-10-20
Project:  SYNDICATE
License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
-->
# SYNDICATE Android app

Kotlin + Jetpack Compose app for the syndicate organiser.
Package name: `com.mrbacco.syndicate`

The app is a thin client: all data and every rule (who owes what, the Lotto rules, line checking,
the wording on screen) live in the Python backend (`../backend`). Each screen asks the backend for
exactly what it shows and displays it. The app itself only does what needs the phone: the contact
picker, saving contacts, and opening SMS or WhatsApp.

## Open and run

1. Start the backend on the PC (see `../backend/README.md`):
   `.venv\Scripts\python -m uvicorn app.main:app --reload` from the `backend` folder.
2. Android Studio → **File → Open** → select this `android` folder, and wait for **Gradle sync**.
3. Connect a phone (USB or wireless debugging) or start an emulator, then let it reach the PC:
   `adb reverse tcp:8000 tcp:8000`. Run this again whenever the phone reconnects.
4. Press **Run ▶**. If the server is not reachable, the app says so and offers Retry.

Debug builds talk to `http://127.0.0.1:8000/` (set in `app/build.gradle.kts`); plain HTTP is
allowed only in debug builds and only to the PC (`src/debug/res/xml/network_security_config.xml`).

Unit tests: right-click `app/src/test` → **Run 'Tests in ...'**, or run
`gradlew test` from a terminal in this folder.

## Code layout

```
app/src/main/java/com/mrbacco/syndicate/
├── MainActivity.kt              app entry point
├── data/
│   ├── model/Screens.kt         what the backend sends for each screen
│   ├── SyndicateApi.kt          the backend's HTTP endpoints (Retrofit)
│   ├── SyndicateRepository.kt   calls the backend, turns failures into messages
│   ├── AppPrefs.kt              small settings kept on the phone ("don't show this again")
│   └── AppContainer.kt          creates the repository with the backend address
├── domain/
│   ├── LineInput.kt             reads a typed line (limits come from the server)
│   ├── Money.kt                 reads typed euro amounts
│   └── PhoneNumbers.kt          phone numbers for WhatsApp links
└── ui/
    ├── theme/Theme.kt           colours, light and dark
    ├── navigation/SyndicateNavHost.kt  screen navigation
    ├── components/              number balls, input dialog, loading and error states
    ├── welcome/                 landing page, shown each time the app opens (unless turned off)
    ├── list/                    "My syndicates" screen
    └── detail/                  Members / Lines / Results tabs, add member dialog
```

## Versions

Android Gradle Plugin 9.4.1, Gradle 9.6.0, Kotlin 2.2.10, Compose BOM 2024.12.01, Retrofit 3.0.0,
OkHttp 4.12.0, kotlinx.serialization 1.9.0, compileSdk/targetSdk 36, minSdk 26 (Android 8.0).
