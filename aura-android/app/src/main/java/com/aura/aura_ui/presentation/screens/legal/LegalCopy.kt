package com.aura.aura_ui.presentation.screens.legal

/**
 * In-app privacy policy, terms and open-source licence list. DRAFT text, pending legal review.
 * - Change together: the website copy at `aura-android-use-website/privacy.html` is generated from this
 *   file. Run `node scripts/gen_legal_page.mjs` after any edit and commit both.
 */

object LegalCopy {


    val PRIVACY = """
Roxxy - Privacy
Roxxy is a modified fork of AURA (https://github.com/Dinesh210805/aura-android-use) by
Dinesh Kumar C, licensed under the GNU AGPL v3. It is not made or endorsed by the
original author.

What this fork changed
The upstream Firebase backend was removed: no Google sign-in, no analytics, no crash
reporting, no device registry, and no remote kill switch or blocklist. Roxxy does not
send usage data to its developers. This text replaces the upstream privacy policy,
which described that backend.

What Roxxy does on your phone
Roxxy can read what is on your screen and tap, type and scroll in other apps through
Android's Accessibility service, when you ask it to. Banking, payment and authenticator
apps known to the app are blocked by its own rules. That list cannot cover every app.

Permissions
Roxxy's manifest declares more permissions than it uses at any moment. Some need your
approval (Android asks you, or you switch them on in system Settings, and you can
revoke them). Others are "normal" permissions that Android grants automatically at
install, with no prompt.
- Needs your explicit setup: Accessibility service (required for Roxxy to work),
  microphone, notifications, display over other apps, battery optimisation exemption.
- Asks you only when a task uses it: contacts, camera, photos/video/audio files,
  location, Bluetooth, alarms, system settings and Do Not Disturb.
- Granted at install with no prompt: internet, network and Wi-Fi state, vibrate, wake
  lock, start on boot, foreground services, and seeing which apps are installed (used
  to open apps by name; you cannot turn this one off separately).
Roxxy cannot use contacts, camera, location or files you have not allowed.

Network traffic
Roxxy has no developer-run backend of its own, but it does use the network:
- Your AI provider: what a task needs (your request, on-screen text, screenshots,
  voice in live mode) is sent from your phone to the provider you configure with your
  own key. Their terms and prices apply. Free tiers can have limits, and some providers
  may use what you send on a free tier to improve their products. Google's Gemini API
  pricing page said so for its free tier when we checked (November 2026); terms can
  change, so read your provider's current terms.
- Web search and page fetch for tasks that need it: DuckDuckGo/Bing pages, or Tavily
  if you add a Tavily key.
- Voice model downloads from Hugging Face, if you choose the on-device voice.
- Your phone's own speech recognizer, which may send audio to its maker.
- If you connect a computer over MCP, the connection is intended to stay on your
  local network.
Your API keys are stored on the phone in encrypted storage only. If this device cannot
provide it, Roxxy refuses to save a key instead of storing it unencrypted. Android
backup is turned off for Roxxy, so keys and settings are not backed up or moved to a
new phone. You can remove them in Settings. Anything not
listed here is upstream behavior that has not been fully audited in this fork.
""".trim()

    val TERMS = """
Roxxy - Terms
Roxxy is a modified fork of AURA by Dinesh Kumar C, under the GNU AGPL v3. The full
license and the additional permission for Google libraries are in the source
repository you got this APK from, which also holds the complete corresponding source.

Use
Use Roxxy only on your own device and accounts, and only for lawful purposes. Do not
use it to bypass security controls or reach accounts that are not yours.

Your AI provider and costs
Roxxy needs your own API key for a third-party AI provider. That provider's terms
apply, and any usage costs are charged by them to you. Roxxy does not control them.

AI makes mistakes
Roxxy is powered by AI and can misread instructions or act wrongly, including tapping
the wrong thing in another app. Review important or irreversible actions. Give the
Accessibility permission only if you accept this.

No warranty
Roxxy is provided "AS IS", without warranty of any kind, as the AGPL says. You use it
at your own risk.
""".trim()

    /** library name -> license. Seeded with the app's key dependencies. */
    val LICENSES: List<Pair<String, String>> = listOf(
        "Jetpack Compose" to "Apache License 2.0",
        "AndroidX Navigation Compose" to "Apache License 2.0",
        "Material Components (Material 3)" to "Apache License 2.0",
        "Kotlin & Coroutines" to "Apache License 2.0",
        "MCP Kotlin SDK" to "MIT License",
        "Ktor" to "Apache License 2.0",
        "kotlinx.serialization" to "Apache License 2.0",
        "ONNX Runtime (Android)" to "MIT License",
        "AndroidX Lifecycle" to "Apache License 2.0",
    )
}
