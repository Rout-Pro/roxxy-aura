package com.aura.aura_ui.presentation.screens.legal

/**
 * In-app privacy policy, terms and open-source licence list. DRAFT text, pending legal review.
 * - Change together: the website copy at `aura-android-use-website/privacy.html` is generated from this
 *   file. Run `node scripts/gen_legal_page.mjs` after any edit and commit both.
 */

object LegalCopy {

    const val CONTACT_EMAIL = "the Roxxy repository issue tracker on GitHub"
    const val PRIVACY_URL = "https://github.com/Rout-Pro/roxxy-aura"
    const val TERMS_URL = "https://github.com/Rout-Pro/roxxy-aura"

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
Android's Accessibility service, when you ask it to. It may use the microphone,
camera-free screenshots, notifications and contacts only if you grant those
permissions. Known banking, payment and authenticator apps are blocked by the app's
own rules. That list cannot cover every app.

Where your data goes
Roxxy has no server of its own. Text, screen content and audio needed for a task are
sent from your phone directly to the AI provider you choose and configure with your own
API key (for example Google Gemini), and to your phone's own speech services. That
provider's terms and prices apply. Voice input may be handled by your phone's speech
recognizer, which can send audio to its maker. If you connect a computer over MCP, the
connection is local-network only, as designed upstream.

Your key stays on your phone. You can remove it in Settings.
""".trim()

    val TERMS = """
Roxxy - Terms
Roxxy is a modified fork of AURA by Dinesh Kumar C, under the GNU AGPL v3. The full
license and the additional permission for Google libraries are in the source
repository. Complete corresponding source: $PRIVACY_URL

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

Contact
$CONTACT_EMAIL.
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
