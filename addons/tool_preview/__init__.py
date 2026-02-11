from . import dependencies
dependencies.preload_modules()
import bpy
import sys
import os

from PySide6 import QtWidgets, QtGui, QtCore, QtMultimedia, QtMultimediaWidgets

bl_info = {
    "name": "Tool Video Preview Window",
    "author": "Your Name",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "Ctrl + Shift + T",
    "description": "Shows PySide6 window with video previews for active built-in tools",
    "category": "Interface",
}

# Keep track of window and shortcut
tool_preview_window = None
addon_keymaps = []


# ---------------------------
# Video Viewer Widget
# ---------------------------
class VideoViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool Video Preview")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400, 300)

        # Video player
        self.player = QtMultimedia.QMediaPlayer(self)
        self.video_widget = QtMultimediaWidgets.QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.video_widget)

        # State
        self.current_tool = ""
        self.current_video_path = ""

    def play_video(self, video_path: str):
        if not os.path.exists(video_path):
            print(f"Video not found: {video_path}")
            return False

        if self.current_video_path == video_path:
            return True  # already playing

        self.player.stop()
        self.player.setSource(QtCore.QUrl.fromLocalFile(video_path))
        self.player.play()
        self.current_video_path = video_path
        return True

    def stop_video(self):
        self.player.stop()
        self.current_video_path = ""


# ---------------------------
# PySide6 Tool Preview Window
# ---------------------------
class ToolPreviewWindow(VideoViewer):
    def __init__(self, addon_path):
        super().__init__()
        self.video_folder = os.path.join(addon_path, "video")

        # Timer to update active tool
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_tool_video)
        self.timer.start(200)  # every 200ms

    def update_tool_video(self):
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode)
        if not tool:
            self.stop_video()
            self.current_tool = ""
            return

        tool_id = tool.idname
        if tool_id == self.current_tool:
            return

        self.current_tool = tool_id
        video_path = os.path.join(self.video_folder, f"{tool_id}.gif")
        print("Active tool:", tool_id)
        print("Video path:", video_path)

        if os.path.exists(video_path):
            if not self.play_video(video_path):
                print("Failed to play video:", video_path)
        else:
            self.stop_video()
            print("Video not found for tool:", tool_id)


# ---------------------------
# Blender Operator
# ---------------------------
class WM_OT_show_tool_preview(bpy.types.Operator):
    bl_idname = "wm.show_tool_preview"
    bl_label = "Show Tool Video Preview Window"

    def execute(self, context):
        global tool_preview_window

        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication([])

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


# ---------------------------
# Register Classes
# ---------------------------
classes = (WM_OT_show_tool_preview, ToolPreviewWindow)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymap()


def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
