import sys
import numpy as np
import librosa
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout,
    QPushButton, QSlider, QLabel, QProgressBar, QScrollBar, QOpenGLWidget
)
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *

class WaveformWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = np.zeros(1, dtype=np.float32)
        self.sample_rate = 44100
        self.position = 0
        self.playing = False
        self.samples_per_pixel = 200
        self.h_offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.volume_meter = None
        self.progress_meter = None

    def load_audio(self, path):
        data, sr = librosa.load(path, sr=None, mono=True)
        self.samples = data.astype(np.float32)
        self.sample_rate = sr
        self.position = 0
        self.h_offset = 0
        self.update()

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.2, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.update_projection(w, h)

        if self._pending_fit_to_screen:
            self.fit_to_screen()
            self._pending_fit_to_screen = False

    def update_projection(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        visible_width_s = w / self.x_scale_px_per_s
        left_s = self.x_offset_s
        right_s = self.x_offset_s + visible_width_s
        bottom_amplitude = -1.0 * self.y_scale_factor
        top_amplitude = 1.0 * self.y_scale_factor
        glOrtho(left_s, right_s, bottom_amplitude, top_amplitude, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.update()
        self.x_scale_changed.emit(self.x_scale_px_per_s)
        self.x_offset_changed.emit(self.x_offset_s)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        if len(self.samples) < 2:
            return

        w, h = self.width(), self.height()

        # ---- Timeline height ----
        timeline_height = 20
        waveform_bottom = -1 + (timeline_height / h) * 2  # GL coords
        half_wave_height = 1 - (timeline_height / h) * 2

        start = int(self.h_offset)
        end = min(start + int(w * self.samples_per_pixel), len(self.samples))
        segment = self.samples[start:end]

        step = max(1, int(len(segment) / w))
        peaks_min = []
        peaks_max = []
        for i in range(0, len(segment), step):
            slice_ = segment[i:i + step]
            if len(slice_) > 0:
                peaks_min.append(slice_.min())
                peaks_max.append(slice_.max())

        # ---- Waveform fill ----
        glColor4f(0.5, 0.8, 1.0, 1.0)  # light blue fill
        glBegin(GL_QUADS)
        for x, (mn, mx) in enumerate(zip(peaks_min, peaks_max)):
            xpos = x
            glVertex2f(xpos, mn * half_wave_height)
            glVertex2f(xpos, mx * half_wave_height)
            glVertex2f(xpos + 1, mx * half_wave_height)
            glVertex2f(xpos + 1, mn * half_wave_height)
        glEnd()

        # ---- Playhead ----
        ph_x = (self.position - self.h_offset) / self.samples_per_pixel
        if 0 <= ph_x < w:
            glColor4f(1, 0, 0, 1)
            glBegin(GL_QUADS)
            glVertex2f(ph_x, -1)
            glVertex2f(ph_x + 1, -1)
            glVertex2f(ph_x + 1, 1)
            glVertex2f(ph_x, 1)
            glEnd()

        # ---- Timeline ----
        glColor4f(1, 1, 1, 1)
        seconds_per_pixel = self.samples_per_pixel / self.sample_rate
        start_time = start / self.sample_rate
        tick_spacing = self._choose_tick_spacing(seconds_per_pixel * w)

        for tick_time in np.arange(
                math.floor(start_time / tick_spacing) * tick_spacing,
                start_time + seconds_per_pixel * w,
                tick_spacing
        ):
            tick_x = (tick_time * self.sample_rate - start) / self.samples_per_pixel
            if 0 <= tick_x < w:
                glBegin(GL_LINES)
                glVertex2f(tick_x, 1)
                glVertex2f(tick_x, waveform_bottom)
                glEnd()
                # Draw label
                self.renderText(tick_x + 2, h - 5, f"{tick_time:.1f}s")

    def _choose_tick_spacing(self, visible_seconds):
        """Pick a nice tick spacing given visible time range."""
        for spacing in [0.1, 0.25, 0.5, 1, 2, 5, 10]:
            if visible_seconds / (self.width() / 100) < spacing:
                return spacing
        return 10

    def _tick(self):
        if self.playing:
            self.position += int(self.sample_rate / 60)
            if self.position >= len(self.samples):
                self.playing = False
                self.position = len(self.samples)
            # Update volume meter
            if self.volume_meter is not None:
                window = self.samples[self.position:self.position + 1024]
                if len(window) > 0:
                    rms = np.sqrt(np.mean(window ** 2))
                    self.volume_meter.setValue(int(rms * 100))
            # Update progress bar
            if self.progress_meter is not None:
                self.progress_meter.setValue(int(self.position / len(self.samples) * 100))
        self.update()

    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.timer.start(16)
        else:
            self.timer.stop()

    def zoom(self, factor):
        self.samples_per_pixel = max(10, min(2000, self.samples_per_pixel * factor))
        self.update()

    def scroll_horizontal(self, value):
        self.h_offset = int(value * len(self.samples) / 100)
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Waveform Timeline (PyQt5 + OpenGL + Librosa)")

        self.waveform = WaveformWidget()
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout(self.centralWidget())

        # Controls
        controls = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        play_btn = QPushButton("Play/Pause")
        play_btn.clicked.connect(self.waveform.toggle_play)

        zoom_in = QPushButton("Zoom In")
        zoom_in.clicked.connect(lambda: self.waveform.zoom(0.8))
        zoom_out = QPushButton("Zoom Out")
        zoom_out.clicked.connect(lambda: self.waveform.zoom(1.25))

        h_scroll = QScrollBar(Qt.Horizontal)
        h_scroll.valueChanged.connect(self.waveform.scroll_horizontal)

        self.volume_meter = QProgressBar()
        self.volume_meter.setOrientation(Qt.Vertical)
        self.volume_meter.setRange(0, 100)
        self.waveform.volume_meter = self.volume_meter

        self.progress_meter = QProgressBar()
        self.progress_meter.setOrientation(Qt.Horizontal)
        self.progress_meter.setRange(0, 100)
        self.waveform.progress_meter = self.progress_meter

        controls.addWidget(open_btn)
        controls.addWidget(play_btn)
        controls.addWidget(zoom_in)
        controls.addWidget(zoom_out)
        controls.addWidget(self.volume_meter)
        layout.addLayout(controls)
        layout.addWidget(self.waveform)
        layout.addWidget(h_scroll)
        layout.addWidget(QLabel("Progress"))
        layout.addWidget(self.progress_meter)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Audio", "",
                                              "Audio Files (*.wav *.mp3 *.flac *.ogg)")
        if path:
            self.waveform.load_audio(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1000, 500)
    w.show()
    sys.exit(app.exec_())
