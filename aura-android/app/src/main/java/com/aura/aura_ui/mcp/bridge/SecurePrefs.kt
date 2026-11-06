package com.aura.aura_ui.mcp.bridge

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Fail-closed access to the encrypted `aura_secure_keys` preferences (API keys, tokens).
 *
 * There is deliberately NO plaintext fallback. If the Android Keystore or the encrypted file cannot
 * be opened, reads return nothing, writes are refused (the editor reports `commit() == false`), and
 * [FailClosedPrefs.isAvailable] is false so the UI can say so. Opening is retried on every access,
 * so a transient Keystore failure recovers without deleting or overwriting stored data.
 */
object SecurePrefs {
    const val KEYS_FILE = "aura_secure_keys"
    private const val TAG = "SecurePrefs"

    internal fun openEncrypted(context: Context, name: String): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        return EncryptedSharedPreferences.create(
            context,
            name,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    /** Test seam only: unit tests replace it because Robolectric has no real Keystore. */
    @Volatile
    internal var opener: (Context, String) -> SharedPreferences = ::openEncrypted

    internal fun log(t: Throwable) {
        Log.w(TAG, "secure storage unavailable (${t.javaClass.simpleName}); refusing plaintext fallback")
    }
}

class FailClosedPrefs(context: Context, private val name: String) : SharedPreferences {
    private val appContext = context.applicationContext ?: context

    @Volatile
    private var delegate: SharedPreferences? = null

    private fun d(): SharedPreferences? {
        delegate?.let { return it }
        synchronized(this) {
            delegate?.let { return it }
            val opened = runCatching { SecurePrefs.opener(appContext, name) }
                .onFailure { SecurePrefs.log(it) }
                .getOrNull()
            delegate = opened
            return opened
        }
    }

    /** True when the encrypted store is open. False means nothing is read or written. */
    val isAvailable: Boolean get() = d() != null

    override fun getAll(): MutableMap<String, *> = d()?.all ?: mutableMapOf<String, Any>()
    override fun getString(key: String?, defValue: String?): String? = d()?.getString(key, defValue) ?: defValue
    override fun getStringSet(key: String?, defValues: MutableSet<String>?): MutableSet<String>? =
        d()?.getStringSet(key, defValues) ?: defValues
    override fun getInt(key: String?, defValue: Int): Int = d()?.getInt(key, defValue) ?: defValue
    override fun getLong(key: String?, defValue: Long): Long = d()?.getLong(key, defValue) ?: defValue
    override fun getFloat(key: String?, defValue: Float): Float = d()?.getFloat(key, defValue) ?: defValue
    override fun getBoolean(key: String?, defValue: Boolean): Boolean = d()?.getBoolean(key, defValue) ?: defValue
    override fun contains(key: String?): Boolean = d()?.contains(key) ?: false
    override fun edit(): SharedPreferences.Editor = d()?.edit() ?: RefusingEditor
    override fun registerOnSharedPreferenceChangeListener(l: SharedPreferences.OnSharedPreferenceChangeListener?) {
        d()?.registerOnSharedPreferenceChangeListener(l)
    }
    override fun unregisterOnSharedPreferenceChangeListener(l: SharedPreferences.OnSharedPreferenceChangeListener?) {
        d()?.unregisterOnSharedPreferenceChangeListener(l)
    }

    private object RefusingEditor : SharedPreferences.Editor {
        override fun putString(key: String?, value: String?) = this
        override fun putStringSet(key: String?, values: MutableSet<String>?) = this
        override fun putInt(key: String?, value: Int) = this
        override fun putLong(key: String?, value: Long) = this
        override fun putFloat(key: String?, value: Float) = this
        override fun putBoolean(key: String?, value: Boolean) = this
        override fun remove(key: String?) = this
        override fun clear() = this
        override fun commit(): Boolean = false
        override fun apply() {}
    }
}
