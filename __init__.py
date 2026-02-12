bl_info = {
    "name": "Tool Preview",
    "author": "Léo Vigin",
    "version": (2, 9, 0),
    "blender": (4, 2, 0),
    "location": "Ctrl + Shift + P",
    "description": "Live MP4 preview window with subtitles",
    "category": "Interface",
}

import bpy
import os
from PySide6 import QtWidgets, QtCore
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QFont


tool_preview_window = None
tool_preview_running = False
addon_keymaps = []

# ----------------------------------------------------------
# Qt preview window
# ----------------------------------------------------------

class ToolPreviewWindow(QtWidgets.QWidget):
    def __init__(self, addon_path):
        super().__init__()

        self.setWindowTitle("Tool Video Preview")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(480, 320)

        self.video_folder = os.path.join(addon_path, "video")
        self.subtitle_folder = os.path.join(addon_path, "subtitles")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Frame container for stacking video + subtitles
        self.container = QtWidgets.QFrame()
        self.container.setStyleSheet("background-color: black;")
        container_layout = QtWidgets.QVBoxLayout(self.container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(0)

        # Video widget
        self.video_widget = QVideoWidget()
        container_layout.addWidget(self.video_widget, stretch=1)

        # Subtitle label (spacing and font fixed)
        self.subtitle_label = QtWidgets.QLabel("", self.container)
        self.subtitle_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        self.subtitle_label.setMargin(2)
        self.subtitle_label.setStyleSheet(
            "color: white; background-color: rgba(0,0,0,180); padding: 4px; height: "
        )
        # Set bigger, bold font
        font = QFont()
        font.setPointSize(20) 
        font.setBold(True)
        self.subtitle_label.setFont(font)

        container_layout.addWidget(self.subtitle_label, stretch=0)
        self.subtitle_label.raise_()

        layout.addWidget(self.container)

        # Media player
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self.loop_video)

        # Subtitles
        self.subtitles_enabled = True
        self.subtitles = {}
        self.current_tool_id = ""

        # Timer to update subtitles reliably
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(lambda: self.update_subtitle(self.player.position()))
        self.timer.start(50)  # every 50ms


    def loop_video(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def check_active_tool(self, context):
        if not context.workspace:
            return
        tool = context.workspace.tools.from_space_view3d_mode(context.mode)
        if not tool:
            return
        if tool.idname != self.current_tool_id:
            self.current_tool_id = tool.idname
            self.load_video(tool.idname)


    def load_video(self, tool_id):
        video_path = os.path.join(self.video_folder, f"{tool_id}.mp4")
        subtitle_path = os.path.join(self.subtitle_folder, f"{tool_id}.srt")

        print("Tool ID:", tool_id)
        print("Video path:", video_path)
        print("Subtitle path:", subtitle_path)

        # Load subtitles
        if os.path.exists(subtitle_path):
            self.subtitles = self.parse_srt(subtitle_path)
            print("Loaded subtitles:")
            for (start, end), text in self.subtitles.items():
                print(f"{start}ms → {end}ms: {text}")
        else:
            self.subtitles = {}
            print("No subtitles found!")

        # Load video
        if os.path.exists(video_path):
            self.player.stop()
            self.player.setSource(QtCore.QUrl.fromLocalFile(video_path))
            self.player.play()
            print("Playing video:", video_path)
        else:
            self.player.stop()
            print("Video not found!")


    def parse_srt(self, filepath):
        subs = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
        except Exception as e:
            print("Error reading SRT:", e)
            return subs

        i = 0
        while i < len(lines):
            if lines[i].isdigit():
                i += 1
                if i >= len(lines): break
                time_line = lines[i]
                if ' --> ' not in time_line:
                    i += 1
                    continue
                start_str, _, end_str = time_line.partition(' --> ')
                try:
                    start_ms = self.srt_time_to_ms(start_str.strip())
                    end_ms = self.srt_time_to_ms(end_str.strip())
                except Exception as e:
                    i += 1
                    continue
                i += 1
                text_lines = []
                while i < len(lines) and lines[i]:
                    text_lines.append(lines[i])
                    i += 1
                subs[(start_ms, end_ms)] = "\n".join(text_lines)
            else:
                i += 1
        return subs

    @staticmethod
    def srt_time_to_ms(time_str):
        h,m,s_ms = time_str.split(":")
        s,ms = s_ms.split(",")
        return (int(h)*3600 + int(m)*60 + int(s))*1000 + int(ms)


    def update_subtitle(self, position):
        if not self.subtitles_enabled or not self.subtitles:
            self.subtitle_label.setText("")
            return
        for (start,end), text in self.subtitles.items():
            if start <= position <= end:
                self.subtitle_label.setText(text)
                return
        self.subtitle_label.setText("")


    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_S and event.modifiers() & QtCore.Qt.ControlModifier:
            self.subtitles_enabled = not self.subtitles_enabled
            print("Subtitles", "ON" if self.subtitles_enabled else "OFF")
            return
        if key == QtCore.Qt.Key_Space:
            if self.player.playbackState() == QMediaPlayer.PlayingState:
                self.player.pause()
            else:
                self.player.play()
            return
        super().keyPressEvent(event)


    def closeEvent(self, event):
        global tool_preview_window, tool_preview_running
        if self.player:
            self.player.stop()
            self.player.deleteLater()
        tool_preview_window = None
        tool_preview_running = False
        event.accept()


# ----------------------------------------------------------
# operator
# ----------------------------------------------------------

class WM_OT_tool_preview_modal(bpy.types.Operator):
    bl_idname = "wm.tool_preview_modal"
    bl_label = "Tool Preview Modal"

    _timer = None

    def execute(self, context):
        global tool_preview_window, tool_preview_running

        if tool_preview_running:
            return {'CANCELLED'}

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

    def modal(self, context, event):
        global tool_preview_window

        if not tool_preview_window or not tool_preview_window.isVisible():
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            tool_preview_window.check_active_tool(context)

        QtWidgets.QApplication.processEvents()
        return {'PASS_THROUGH'}

    def cancel(self, context):
        global tool_preview_running, tool_preview_window
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        tool_preview_running = False
        tool_preview_window = None


# ----------------------------------------------------------
# registration + hotkey
# ----------------------------------------------------------

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
    global tool_preview_window, tool_preview_running
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