package com.aura.aura_ui.agent.mcpbridge.client

import android.content.Context
import com.aura.aura_ui.mcp.bridge.FailClosedPrefs
import com.aura.aura_ui.mcp.bridge.SecurePrefs

/** Encrypted per-server token store. Fail-closed (no plaintext fallback); shares aura_secure_keys. */
class McpSecretStore(context: Context) {
    private val prefs = FailClosedPrefs(context, SecurePrefs.KEYS_FILE)

    val isAvailable: Boolean get() = prefs.isAvailable

    fun getToken(serverId: String): String? = prefs.getString(key(serverId), null)?.takeIf { it.isNotBlank() }
    fun setToken(serverId: String, token: String): Boolean = prefs.edit().putString(key(serverId), token.trim()).commit()
    fun clearToken(serverId: String) = prefs.edit().remove(key(serverId)).apply()
    private fun key(id: String) = "mcp_token_$id"
}
