<!--
File:     README.md
Author:   mrbacco04@gmail.com
GitHub:   https://github.com/mrbacco
Created:  2026-10-20
Updated:  2026-10-20
Project:  SYNDICATE
License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
-->
# SYNDICATE

An app that runs a lotto syndicate for the organiser: it tracks who's in,
who's paid, which numbers are played, and checks every draw automatically.

The product plan is kept privately and is not part of this repository.

## Project layout

```
SYNDICATE/
├── README.md                    this file
├── LICENSE-APACHE               Apache 2.0 license text
├── LICENSE-AGPL                 AGPL v3 license text
├── COMMERCIAL-LICENSE.md        commercial license terms
├── backend/                     Python API, database, scraper, results checking
│   ├── app/                     application code
│   └── tests/                   automated tests
└── android/                     Kotlin + Jetpack Compose app (organiser);
                                 open THIS folder in Android Studio
```

## Build steps

1. Project skeleton ✔
2. Android app with sample data: syndicates, members, payments, lines, results ✔
3. Python backend: data model, database, API ✔
4. Results checking, with a results scraper for lottery.ie ✔
5. Member web page (served by the backend) ✔
6. Connect the Android app to the backend ✔

## File headers

Every source file starts with a header like this:

```
File:     <path inside the project>
Author:   mrbacco04@gmail.com
GitHub:   https://github.com/mrbacco
Created:  <date the file was created>
Updated:  <date of the last change>
Project:  SYNDICATE
License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
```

Exceptions: JSON files (JSON has no comments) and the license texts, which
are kept verbatim.

## License

Licensed under one of: Apache-2.0, AGPL-3.0-or-later, or a commercial
license. See `LICENSE-APACHE`, `LICENSE-AGPL` and `COMMERCIAL-LICENSE.md`.
