"""Live event callback support shared by the agent and tools."""

event_callback = None

def set_event_callback(callback):
    """Set a callback that receives live agent/tool events."""
    global event_callback
    event_callback = callback

def emit_event(event):
    """Send an event to the active UI, if one is connected."""
    if event_callback is not None:
        try:
            event_callback(event)
        except Exception:
            # UI streaming must never break the agent itself.
            pass
