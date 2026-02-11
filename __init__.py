bl_info = {
    "name": "Tool Preview",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (5, 0, 1),
    "location": "3D View > Sidebar > Tool Preview",
    "description": "Shows a small preview image of the active tool",
    "category": "Interface",
}

import bpy
from . import main

classes = (
    main.WM_OT_show_tool_preview,
    main.VIEW3D_PT_tool_preview,
)

def register():
    # Safe unregister old classes first
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register timer once
    if not hasattr(bpy.app.timers, "_tool_preview_timer_registered"):
        bpy.app.timers.register(main.refresh_panel)
        bpy.app.timers._tool_preview_timer_registered = True

    print("Tool Preview Addon Registered")

def unregister():
    # Unregister timer safely
    try:
        bpy.app.timers.unregister(main.refresh_panel)
        del bpy.app.timers._tool_preview_timer_registered
    except Exception:
        pass

    # Unregister classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    print("Tool Preview Addon Unregistered")
