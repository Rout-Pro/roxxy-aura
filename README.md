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
- Gemini has a free tier with limits. Google's pricing page says that on the free tier your content may be used to improve its products (checked November 2026; terms can change). Roxxy sends screenshots and on-screen text to your provider, so decide before you use a free key.
- This fork was built and checked by CI (compile and unit tests). It has not been verified on a real phone by the person who made the changes. Treat it as a test build. Network use: your AI provider, web search/fetch, optional Hugging Face voice models; see in-app Privacy.

## Network limits in this fork

- Plain http is allowed only to loopback (`localhost`, `127.0.0.1`, `::1`): the on-device MCP server and a model server running on the same phone. Everything else must be https. The app rejects http endpoints with a message saying so.
- Local-model servers on another machine over plain http (for example Ollama at `192.168.x.x`) are NOT supported. Upstream allowed cleartext globally; this fork does not. Serving such an endpoint over https works. A scoped per-endpoint allowance for a user-approved LAN host could be added later.

## Build

Android Studio or `cd aura-android && ./gradlew assembleRelease` (JDK 17). The workflow in `.github/workflows/build.yml` builds the release APK and attaches it to a GitHub release.

## License

AGPL-3.0-or-later plus the Google-libraries exception, see `LICENSE` and `LICENSE-EXCEPTION.md`. The complete source for the shipped APK is this repository.


## Permissions at setup

- **Required:** Accessibility (Roxxy cannot act on your phone without it) and your own Gemini API key (setup will not finish without a verified key).
- **Optional, can be skipped at setup:** microphone and display-over-apps (voice and the floating overlay), the Roxxy keyboard (typing into apps that expose no editable field), and notifications / notification access (alert pill and quick replies). Skipping grants nothing. Roxxy does not prompt for them at every launch. The home screen shows a banner when Accessibility, overlay or microphone is missing, with a one-tap fix. A feature that needs a missing permission may do nothing until you enable it. The microphone check in the live voice path is covered; other feature paths were checked by reading the code, not by running them on a device.
