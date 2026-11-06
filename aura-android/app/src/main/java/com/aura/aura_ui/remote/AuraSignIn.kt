package com.aura.aura_ui.remote

import android.content.Context

/**
 * Roxxy fork: Google sign-in and the upstream Firebase backend were removed. Roxxy has no
 * accounts. This stub keeps the call sites compiling and always reports "not available".
 */
class AuraSignIn(@Suppress("unused") private val context: Context) {
    suspend fun signIn(@Suppress("UNUSED_PARAMETER") activityContext: Context): SignInOutcome =
        SignInOutcome.Misconfigured("Roxxy has no accounts. Nothing to sign in to.")
}

sealed interface SignInOutcome {
    data class Success(val uid: String, val email: String?, val displayName: String?) : SignInOutcome
    data object Cancelled : SignInOutcome
    data object NoGoogleAccount : SignInOutcome
    data class Misconfigured(val message: String) : SignInOutcome
    data class Failed(val message: String) : SignInOutcome
}

/** No account state in Roxxy. */
object AuthState {
    fun isSignedIn(): Boolean = false
    fun email(): String? = null
    fun uid(): String? = null
    fun signOut() = Unit
}
