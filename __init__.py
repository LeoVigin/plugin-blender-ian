bl_info = {
    "name": "Tool Preview Window",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "Ctrl + Shift + T",
    "description": "Shows PySide2 window with previews for active built-in tools",
    "category": "Interface",
}

import bpy
from .main import WM_OT_show_tool_preview
from .main import register_keymap, unregister_keymap

classes = (
    WM_OT_show_tool_preview,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymap()

def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
