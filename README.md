# Roxxy

Roxxy is an Android assistant that can read your screen and tap, type and scroll in other apps when you ask it to. It is a **modified fork of [AURA](https://github.com/Dinesh210805/aura-android-use) by Dinesh Kumar C**, licensed under the **GNU AGPL v3** with the additional permission in `LICENSE-EXCEPTION.md`. It is not made or endorsed by the original author. The original README is kept as `UPSTREAM_README.md`.

## What was changed from upstream

- Renamed to Roxxy (app name, package `com.roxxy.aura`, visible strings).
- Removed the upstream Firebase backend: Google sign-in, Analytics, Crashlytics, device registry, remote kill switch and blocklist. Roxxy has no accounts and sends no usage data to anyone. Nothing can remotely switch it off.
- Replaced the in-app privacy and terms text with a fork-specific version.
- Onboarding no longer requires a Google account.
- Everything else (accessibility-based phone control, on-device agent, MCP server, models) is upstream code, unmodified.

## Things to know

- Install is a sideloaded APK. Android will show a Play Protect prompt for apps from outside the Play Store.
- It needs the Accessibility permission, which lets it see and operate other apps. Only grant it if you accept that.
- You supply your own AI provider key in the app. Provider usage costs are charged by the provider to you.
- This fork was built and checked by CI (compile and unit tests). It has not been verified on a real phone by the person who made the changes. Treat it as a test build.

## Build

Android Studio or `cd aura-android && ./gradlew assembleRelease` (JDK 17). The workflow in `.github/workflows/build.yml` builds the release APK and attaches it to a GitHub release.

## License

AGPL-3.0-or-later plus the Google-libraries exception, see `LICENSE` and `LICENSE-EXCEPTION.md`. The complete source for the shipped APK is this repository.
