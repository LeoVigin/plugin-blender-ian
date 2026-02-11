import bpy
import os

def get_active_tool_id():
    try:
        tools = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
        if tools:
            return tools[0].idname
        return None
    except:
        return None

class WM_OT_show_tool_preview(bpy.types.Operator):
    bl_idname = "wm.show_tool_preview"
    bl_label = "Show Tool Preview"

    def execute(self, context):
        tool_id = get_active_tool_id()
        self.report({'INFO'}, f"Active Tool: {tool_id}" if tool_id else "No active tool")
        return {'FINISHED'}

class VIEW3D_PT_tool_preview(bpy.types.Panel):
    bl_label = "Tool Preview"
    bl_idname = "VIEW3D_PT_tool_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool Preview"

    _last_tool_id = None

    def draw(self, context):
        layout = self.layout
        tool_id = get_active_tool_id()
        addon_dir = os.path.dirname(__file__)
        if tool_id != self._last_tool_id:
            self._last_tool_id = tool_id

        image_path = os.path.join(addon_dir, "video", f"{tool_id}.png")
        print("Tool ID:", tool_id)
        print("Looking for image:", image_path, "Exists?", os.path.exists(image_path))

        if tool_id and os.path.exists(image_path):
            # Force reload image to avoid cache issues
            img = bpy.data.images.get(tool_id)
            if img:
                bpy.data.images.remove(img)
            try:
                img = bpy.data.images.load(image_path)
                img.name = tool_id
            except Exception as e:
                layout.label(text=f"Failed to load image: {e}")
                return
            layout.template_preview(img, show_buttons=False)
        else:
            layout.label(text=f"MISSING IMAGE: {tool_id}.png" if tool_id else "No active tool")

def refresh_panel():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    return 1.0  # repeat every second
