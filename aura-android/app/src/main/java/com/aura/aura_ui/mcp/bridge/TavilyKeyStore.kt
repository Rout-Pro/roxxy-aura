package com.aura.aura_ui.mcp.bridge

import android.content.Context

/**
 * Encrypted on-device store for the Tavily API key used by the [AppWebSearchBridge].
 *
 * Backed by [EncryptedSharedPreferences] (AES-256 GCM) keyed by an Android-Keystore-
 * backed [MasterKey], so the key never appears in plaintext on disk. The store
 * is fail-closed: if encrypted storage cannot be opened nothing is read or written and no
 * plaintext fallback exists (see [SecurePrefs]).
 */
class TavilyKeyStore(context: Context) {

    private val prefs = FailClosedPrefs(context, SecurePrefs.KEYS_FILE)

    val isAvailable: Boolean get() = prefs.isAvailable

    /** Returns the stored key, or null if the user has not configured one. */
    fun getApiKey(): String? = prefs.getString(KEY_TAVILY, null)?.takeIf { it.isNotBlank() }

    fun setApiKey(value: String): Boolean =
        prefs.edit().putString(KEY_TAVILY, value.trim()).commit()

    fun clear() {
        prefs.edit().remove(KEY_TAVILY).apply()
    }

    fun isConfigured(): Boolean = !getApiKey().isNullOrBlank()

    companion object {
        private const val KEY_TAVILY = "tavily_api_key"
    }
}
