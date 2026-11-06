package com.aura.aura_ui.remote

/**
 * Roxxy fork: the upstream remote device blocklist (Firestore) was removed. Only the data type
 * remains so [evaluateGate] and its tests keep working. Nothing here talks to a network.
 */
object Blocklist {
    const val DEFAULT_MESSAGE = "This app is unavailable."

    data class Verdict(val blocked: Boolean, val message: String?)
}
