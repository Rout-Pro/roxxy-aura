package com.aura.aura_ui.mcp.bridge

import android.content.Context
import android.content.SharedPreferences
import com.aura.aura_ui.agent.mcpbridge.client.McpSecretStore
import com.aura.aura_ui.agent.llm.LlmEndpointCatalog
import java.io.File
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment

/** Key storage is fail-closed: no plaintext fallback, no plaintext file, and no backup of key files. */
@RunWith(RobolectricTestRunner::class)
class SecureKeyStorageTest {
    private val ctx: Context = RuntimeEnvironment.getApplication()
    private val original = SecurePrefs.opener

    @After fun restore() { SecurePrefs.opener = original }

    private fun breakKeystore() { SecurePrefs.opener = { _, _ -> throw java.security.GeneralSecurityException("keystore broken") } }

    private fun plainFile() = File(ctx.applicationInfo.dataDir, "shared_prefs/${SecurePrefs.KEYS_FILE}.xml")

    @Test fun `broken keystore refuses to save a provider key and writes no file`() {
        plainFile().delete()
        breakKeystore()
        val store = ProviderKeyStore(ctx)
        assertFalse(store.isEncrypted)
        assertFalse(store.setKey(LlmEndpointCatalog.GEMINI_ID, "AIza-secret-value"))
        assertNull(store.getKey(LlmEndpointCatalog.GEMINI_ID))
        assertFalse("no plaintext prefs file may be created", plainFile().exists())
    }

    @Test fun `broken keystore refuses tavily and mcp tokens`() {
        plainFile().delete()
        breakKeystore()
        assertFalse(TavilyKeyStore(ctx).setApiKey("tvly-secret"))
        assertNull(TavilyKeyStore(ctx).getApiKey())
        val mcp = McpSecretStore(ctx)
        assertFalse(mcp.setToken("srv", "tok-secret"))
        assertNull(mcp.getToken("srv"))
        assertFalse(plainFile().exists())
    }

    @Test fun `a pre-existing plaintext file is never read when the keystore is broken`() {
        // Simulates a plaintext file left by an older fallback: it must not be exposed as a key.
        ctx.getSharedPreferences(SecurePrefs.KEYS_FILE, Context.MODE_PRIVATE).edit()
            .putString("provider_key_gemini", "legacy-plain").commit()
        breakKeystore()
        assertNull(ProviderKeyStore(ctx).getKey(LlmEndpointCatalog.GEMINI_ID))
    }

    @Test fun `recovers on later access without losing stored data`() {
        val backing: SharedPreferences = ctx.getSharedPreferences("test_backing_recover", Context.MODE_PRIVATE)
        breakKeystore()
        val store = ProviderKeyStore(ctx)
        assertFalse(store.setKey(LlmEndpointCatalog.GEMINI_ID, "k1"))
        SecurePrefs.opener = { _, _ -> backing }
        assertTrue(store.isEncrypted)
        assertTrue(store.setKey(LlmEndpointCatalog.GEMINI_ID, "k1"))
        assertEquals("k1", store.getKey(LlmEndpointCatalog.GEMINI_ID))
    }

    private fun readRes(name: String) = File("src/main/res/xml/$name").readText()

    @Test fun `backup and extraction rules exclude key material`() {
        for (f in listOf("backup_rules.xml", "data_extraction_rules.xml")) {
            val x = readRes(f)
            assertTrue("$f must exclude aura_secure_keys", x.contains("aura_secure_keys.xml"))
            assertTrue("$f must exclude pairing trust", x.contains("aura_mcp_trust.xml"))
        }
        val de = readRes("data_extraction_rules.xml")
        assertTrue(de.substringAfter("<cloud-backup>").substringBefore("</cloud-backup>").contains("aura_secure_keys.xml"))
        assertTrue(de.substringAfter("<device-transfer>").substringBefore("</device-transfer>").contains("aura_secure_keys.xml"))
    }

    @Test fun `manifest disables backup`() {
        assertTrue(File("src/main/AndroidManifest.xml").readText().contains("android:allowBackup=\"false\""))
    }

    @Test fun `source has no plaintext fallback in key stores`() {
        for (f in listOf("mcp/bridge/ProviderKeyStore.kt", "mcp/bridge/TavilyKeyStore.kt", "agent/mcpbridge/client/McpSecretStore.kt")) {
            val src = File("src/main/java/com/aura/aura_ui/$f").readText()
            assertFalse("$f must not open plain prefs", src.contains("getSharedPreferences("))
        }
    }

    @Test fun `privacy text states permissions are declared not granted and keys are encrypted only`() {
        val p = com.aura.aura_ui.presentation.screens.legal.LegalCopy.PRIVACY
        assertTrue(p.contains("Declaring one"))
        assertTrue(p.contains("does not mean it is granted"))
        assertTrue(p.contains("encrypted storage only"))
        assertFalse(p.contains("stored on the phone. You can"))
    }

    @Test fun `manifest no longer declares unused privileged permissions`() {
        val m = File("src/main/AndroidManifest.xml").readText()
        assertFalse(m.contains("WRITE_SECURE_SETTINGS"))
        assertFalse(m.contains("CHANGE_NETWORK_STATE"))
    }
}
