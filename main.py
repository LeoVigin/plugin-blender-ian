import bpy
import sys
import os
from PySide2 import QtWidgets, QtGui, QtCore

# Keep track of window and shortcut
tool_preview_window = None
addon_keymaps = []


# ---------------------------
# PySide2 Window
# ---------------------------
class ToolPreviewWindow(QtWidgets.QWidget):

    def __init__(self, addon_path):
        super().__init__()
        self.setWindowTitle("Tool Preview")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(300, 300)

        self.label = QtWidgets.QLabel("No Tool", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)

        # Folder inside addon
        self.video_folder = os.path.join(addon_path, "video")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_tool_image)
        self.timer.start(200)

        self.current_tool = ""

    def update_tool_image(self):
        # Get active tool in 3D view
        tool = bpy.context.workspace.tools.from_space_view3d_mode(
            bpy.context.mode
        )

        if not tool:
            self.label.setText("No Tool Active")
            return

        tool_id = tool.idname

        if tool_id == self.current_tool:
            return

        self.current_tool = tool_id

        # Debug: print active tool and image path
        print("Active tool:", tool_id)
        image_path = os.path.join(self.video_folder, f"{tool_id}.png")
        print("Looking for image:", image_path)
        print("Exists:", os.path.exists(image_path))

        if os.path.exists(image_path):
            pixmap = QtGui.QPixmap(image_path)
            if pixmap.isNull():
                print("Failed to load image:", image_path)
                self.label.setText(tool_id)
            else:
                self.label.setPixmap(
                    pixmap.scaled(
                        250, 250,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation
                    )
                )
        else:
            self.label.setText(tool_id)
            print("Image not found!")

# ---------------------------
# Blender Operator
# ---------------------------
class WM_OT_show_tool_preview(bpy.types.Operator):
    bl_idname = "wm.show_tool_preview"
    bl_label = "Show Tool Preview Window"

    def execute(self, context):
        global tool_preview_window

        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)

        # Get addon path dynamically
        addon_path = os.path.dirname(__file__)

        if tool_preview_window is None:
            tool_preview_window = ToolPreviewWindow(addon_path)

        tool_preview_window.show()
        tool_preview_window.raise_()
        tool_preview_window.activateWindow()

        return {'FINISHED'}

# ---------------------------
# Keymap for shortcut
# ---------------------------
def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Window", space_type='EMPTY')
        kmi = km.keymap_items.new(
            WM_OT_show_tool_preview.bl_idname,
            type='T',
            value='PRESS',
            ctrl=True,
            shift=True
        )
        addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
