package com.aura.aura_ui.agent.mcpbridge.client

import android.content.Context
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment

@RunWith(RobolectricTestRunner::class)
class McpServerStoreTest {
    @org.junit.Before fun plainSecurePrefsForRobolectric() {
        // Robolectric has no Android Keystore; back the fail-closed store with plain prefs in tests only.
        com.aura.aura_ui.mcp.bridge.SecurePrefs.opener = { c, n -> c.getSharedPreferences(n, android.content.Context.MODE_PRIVATE) }
    }

    private val ctx: Context = RuntimeEnvironment.getApplication()

    @Test fun `upsert then list round-trips config`() {
        val store = McpServerStore(ctx)
        store.upsert(McpServerConfig(id = "gh", displayName = "GitHub", url = "https://mcp.github.com"))
        val out = store.list().single()
        assertEquals("gh", out.id)
        assertEquals(McpTransportType.STREAMABLE_HTTP, out.transport)
    }

    @Test fun `setEnabled toggles persisted flag`() {
        val store = McpServerStore(ctx)
        store.upsert(McpServerConfig(id = "gh", displayName = "GitHub", url = "https://mcp.github.com"))
        store.setEnabled("gh", false)
        assertEquals(false, store.list().single().enabled)
    }

    @Test fun `delete removes config and its token`() {
        val store = McpServerStore(ctx)
        val secrets = McpSecretStore(ctx)
        store.upsert(McpServerConfig(id = "gh", displayName = "GitHub", url = "https://mcp.github.com"))
        secrets.setToken("gh", "tok-123")
        store.delete("gh")
        secrets.clearToken("gh")
        assertTrue(store.list().isEmpty())
        assertNull(secrets.getToken("gh"))
    }
}
