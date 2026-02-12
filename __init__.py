bl_info = {
    "name": "Tool Video Preview Window",
    "author": "Your Name",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "Ctrl + Shift + P",
    "description": "Live MP4 preview window for built-in tools",
    "category": "Interface",
}

import bpy
import os

from PySide6 import QtWidgets, QtCore
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


# ----------------------------------------------------------
# Globals
# ----------------------------------------------------------

tool_preview_window = None
tool_preview_running = False


# ----------------------------------------------------------
# Qt Preview Window
# ----------------------------------------------------------

class ToolPreviewWindow(QtWidgets.QWidget):

    def __init__(self, addon_path):
        super().__init__()

        self.setWindowTitle("Tool Video Preview")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(480, 320)

        self.video_folder = os.path.join(addon_path, "video")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video widget (auto resize)
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        layout.addWidget(self.video_widget)

        # Media player
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_widget)

        # Loop video
        self.player.mediaStatusChanged.connect(self.loop_video)

        self.current_tool_id = ""

    # ------------------------------------------------------

    def loop_video(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    # ------------------------------------------------------

    def check_active_tool(self, context):

        if not context.workspace:
            return

        tool = context.workspace.tools.from_space_view3d_mode(context.mode)

        if not tool:
            return

        if tool.idname != self.current_tool_id:
            self.current_tool_id = tool.idname
            self.load_video(tool.idname)

    # ------------------------------------------------------

    def load_video(self, tool_id):

        video_path = os.path.join(self.video_folder, f"{tool_id}.mp4")

        if os.path.exists(video_path):

            self.player.stop()

            url = QtCore.QUrl.fromLocalFile(video_path)
            self.player.setSource(url)
            self.player.play()

            print("Playing:", tool_id)

        else:
            self.player.stop()
            print("Missing video:", tool_id)

    # ------------------------------------------------------
    # When window closes → allow relaunch
    # ------------------------------------------------------

    def closeEvent(self, event):
        global tool_preview_window
        global tool_preview_running

        if self.player:
            self.player.stop()
            self.player.deleteLater()

        tool_preview_window = None
        tool_preview_running = False

        event.accept()


# ----------------------------------------------------------
# Modal Operator
# ----------------------------------------------------------

class WM_OT_tool_preview_modal(bpy.types.Operator):
    bl_idname = "wm.tool_preview_modal"
    bl_label = "Tool Preview Modal"

    _timer = None

    def execute(self, context):

        global tool_preview_window
        global tool_preview_running

        # Prevent double start
        if tool_preview_running:
            return {'CANCELLED'}

        # Ensure Qt app exists
        app = QtWidgets.QApplication.instance()
        if not app:
            QtWidgets.QApplication([])

        addon_path = os.path.dirname(__file__)
        tool_preview_window = ToolPreviewWindow(addon_path)
        tool_preview_window.show()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)

        tool_preview_running = True

        return {'RUNNING_MODAL'}

    # ------------------------------------------------------

    def modal(self, context, event):

        global tool_preview_window
        global tool_preview_running

        # If window closed → cancel modal cleanly
        if not tool_preview_window or not tool_preview_window.isVisible():
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            tool_preview_window.check_active_tool(context)

        # Keep Qt responsive
        QtWidgets.QApplication.processEvents()

        return {'PASS_THROUGH'}

    # ------------------------------------------------------

    def cancel(self, context):

        global tool_preview_running
        global tool_preview_window

        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        tool_preview_running = False
        tool_preview_window = None


# ----------------------------------------------------------
# Registration + Hotkey
# ----------------------------------------------------------

addon_keymaps = []


def register():
    bpy.utils.register_class(WM_OT_tool_preview_modal)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="Window", space_type='EMPTY')

        kmi = km.keymap_items.new(
            WM_OT_tool_preview_modal.bl_idname,
            'P',
            'PRESS',
            ctrl=True,
            shift=True
        )

        addon_keymaps.append((km, kmi))


def unregister():
    global tool_preview_window
    global tool_preview_running

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()

    bpy.utils.unregister_class(WM_OT_tool_preview_modal)

    if tool_preview_window:
        tool_preview_window.close()

    tool_preview_window = None
    tool_preview_running = False


if __name__ == "__main__":
    register()
