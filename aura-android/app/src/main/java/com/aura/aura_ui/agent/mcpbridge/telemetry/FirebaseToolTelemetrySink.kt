package com.aura.aura_ui.agent.mcpbridge.telemetry

/**
 * Roxxy fork: tool-call telemetry was removed. Kept under its upstream name so call sites are
 * unchanged. It records and sends nothing.
 */
class FirebaseToolTelemetrySink : ToolTelemetrySink {

    override fun reportToolCall(toolName: String, durationMs: Long, success: Boolean) = Unit

    companion object {
        val shared: FirebaseToolTelemetrySink by lazy { FirebaseToolTelemetrySink() }
    }
}
