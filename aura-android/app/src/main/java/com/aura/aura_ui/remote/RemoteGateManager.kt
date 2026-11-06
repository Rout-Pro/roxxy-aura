package com.aura.aura_ui.remote

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Roxxy fork: the upstream remote kill switch, device blocklist and version floor (Firebase
 * Remote Config + Firestore) were removed, so nothing is fetched and no remote party can switch
 * the app off. The gate state machine ([GateState], [GateEnforcer]) stays as local plumbing and
 * is always [GateState.Allowed].
 */
@Singleton
class RemoteGateManager @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    val gateState: StateFlow<GateState> = state

    /** No network. Publishes [GateState.Allowed]. Never throws. */
    @Suppress("RedundantSuspendModifier")
    suspend fun refresh() {
        publish(GateState.Allowed)
    }

    companion object {
        private val _state = MutableStateFlow<GateState>(GateState.Allowed)
        val state: StateFlow<GateState> = _state.asStateFlow()
        val latestState: GateState get() = _state.value
        fun isBlocked(): Boolean = latestState.isBlocking()
        fun blockMessage(): String? = latestState.blockMessageOrNull()
        @Suppress("UNUSED_PARAMETER")
        fun hydrate(context: Context) { publish(GateState.Allowed) }
        private fun publish(newState: GateState) { _state.value = newState }
    }
}
