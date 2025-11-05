from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, \
    QFileDialog, QScrollBar, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QPointF, pyqtSignal
import sys
import numpy as np
import librosa
import pyaudio
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *


class AudioHistogramWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // 60)

    def initializeGL(self):
        glClearColor(0.1, 0.2, 0.3, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        if len(self.audio_data) > 0:
            bar_width = 2.0 / len(self.audio_data)
            glColor3f(0.5, 0.8, 0.6)
            glBegin(GL_QUADS)
            for i, height in enumerate(self.audio_data):
                x_pos = -1.0 + i * bar_width
                glVertex2f(x_pos, -1.0)
                glVertex2f(x_pos + bar_width, -1.0)
                glVertex2f(x_pos + bar_width, -1.0 + height)
                glVertex2f(x_pos, -1.0 + height)
            glEnd()

    def load_audio_and_process(self, filename):
        if isinstance(filename, list):
            filename = filename[0]
        try:
            y, sr = librosa.load(filename, sr=None)
            D = np.abs(librosa.stft(y))
            magnitude_spectrum = np.mean(D, axis=1)
            max_mag = np.max(magnitude_spectrum)
            if max_mag > 0:
                self.audio_data = (magnitude_spectrum / max_mag) * 2.0
            else:
                self.audio_data = []
            self.update()
        except Exception as e:
            print(f"Error loading or processing audio file: {e}")


class WaveformTimelineWidget(QOpenGLWidget):
    x_offset_changed = pyqtSignal(float)
    x_scale_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = np.array([])
        self.sr = 0
        self.playhead_position_s = 0.0
        self.x_offset_s = 0.0
        self.x_scale_px_per_s = 50.0
        self.y_scale_factor = 1.0
        self.last_mouse_pos = QPointF()
        self.panning = False
        self._pending_fit_to_screen = False

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
        if self.audio_data.size == 0 or self.sr == 0:
            return

        glColor3f(0.6, 0.8, 0.9)
        glBegin(GL_LINE_STRIP)

        num_samples = self.audio_data.size
        audio_duration = num_samples / self.sr

        visible_width_s = self.width() / self.x_scale_px_per_s
        start_time_s = self.x_offset_s
        end_time_s = self.x_offset_s + visible_width_s

        start_sample = max(0, int(start_time_s * self.sr))
        end_sample = min(num_samples, int(end_time_s * self.sr))

        pixels = self.width()
        if end_sample - start_sample > pixels * 2:
            step = max(1, (end_sample - start_sample) // pixels)
            for i in range(start_sample, end_sample, step):
                time_s = i / self.sr
                amplitude = self.audio_data[i]
                glVertex2f(time_s, amplitude)
        else:
            for i in range(start_sample, end_sample):
                time_s = i / self.sr
                amplitude = self.audio_data[i]
                glVertex2f(time_s, amplitude)

        glEnd()

        if 0 <= self.playhead_position_s <= audio_duration:
            glColor3f(1.0, 0.0, 0.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glVertex2f(self.playhead_position_s, -1.0 * self.y_scale_factor)
            glVertex2f(self.playhead_position_s, 1.0 * self.y_scale_factor)
            glEnd()
            glLineWidth(1.0)

    def load_audio_and_process(self, filename):
        if isinstance(filename, list):
            filename = filename[0]
        try:
            self.audio_data, self.sr = librosa.load(filename, sr=None)
            if np.max(np.abs(self.audio_data)) > 0:
                self.audio_data = self.audio_data / np.max(np.abs(self.audio_data))

            self.reset_view()
            self._pending_fit_to_screen = True

        except Exception as e:
            print(f"Error loading or processing audio file: {e}")

    def reset_view(self):
        self.playhead_position_s = 0.0
        self.x_offset_s = 0.0
        self.update()

    def fit_to_screen(self):
        audio_duration = self.audio_data.size / self.sr if self.sr > 0 else 0
        if audio_duration > 0 and self.width() > 0:
            self.x_scale_px_per_s = self.width() / audio_duration
        else:
            self.x_scale_px_per_s = 50.0
        self.set_x_offset(0.0)
        self.update_projection(self.width(), self.height())

    def set_x_offset(self, offset_s):
        audio_duration = self.audio_data.size / self.sr if self.sr > 0 else 0
        visible_width_s = self.width() / self.x_scale_px_per_s
        max_offset_s = max(0.0, audio_duration - visible_width_s)
        self.x_offset_s = max(0.0, min(offset_s, max_offset_s))
        self.update_projection(self.width(), self.height())

    def set_playhead_position(self, position_s):
        self.playhead_position_s = position_s

        # Auto-scroll to keep the playhead in view
        visible_width_s = self.width() / self.x_scale_px_per_s
        if self.playhead_position_s < self.x_offset_s or self.playhead_position_s > self.x_offset_s + visible_width_s:
            # Center the playhead
            new_offset = self.playhead_position_s - visible_width_s / 2
            self.set_x_offset(new_offset)

        self.update()

    def wheelEvent(self, event):
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1

        widget_width_s = self.width() / 1
        time_at_mouse_s = self.x_offset_s + (event.x() / self.width()) * widget_width_s

        self.x_scale_px_per_s = 1

        audio_duration = self.audio_data.size / self.sr if self.sr > 0 else 0
        min_scale = self.width() / (audio_duration + 1e-6) if audio_duration > 0 else 5.0
        #self.x_scale_px_per_s = max(min_scale, min(self.x_scale_px_per_s, 5000.0))

        new_widget_width_s = self.width() / self.x_scale_px_per_s
        new_x_offset_s = time_at_mouse_s - (event.x() / self.width()) * new_widget_width_s

        self.set_x_offset(new_x_offset_s)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            self.panning = True
            widget_width_s = self.width() / self.x_scale_px_per_s
            time_at_mouse_s = self.x_offset_s + (event.x() / self.width()) * widget_width_s
            audio_duration = self.audio_data.size / self.sr if self.sr > 0 else 0
            self.playhead_position_s = max(0.0, min(time_at_mouse_s, audio_duration))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.panning = False

    def mouseMoveEvent(self, event):
        if self.panning:
            delta_x_pixels = event.x() - self.last_mouse_pos.x()
            delta_time_s = delta_x_pixels / self.x_scale_px_per_s
            self.set_x_offset(self.x_offset_s - delta_time_s)
            self.last_mouse_pos = event.pos()
            self.x_offset_changed.emit(self.x_offset_s)


class AudioVisualizerUI(QMainWindow):
    volume_level_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Waveform Visualizer")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.file_label = QLabel("No Audio File Loaded", self)
        main_layout.addWidget(self.file_label, alignment=Qt.AlignHCenter)

        browse_button = QPushButton("Browse Audio File", self)
        browse_button.clicked.connect(self.load_audio_file)
        main_layout.addWidget(browse_button, alignment=Qt.AlignHCenter)

        self.histogram_widget = AudioHistogramWidget(self)
        self.histogram_widget.setMaximumHeight(150)
        main_layout.addWidget(self.histogram_widget)

        self.timeline_widget = WaveformTimelineWidget(self)
        self.timeline_widget.setMinimumHeight(200)
        main_layout.addWidget(self.timeline_widget)

        self.waveform_scrollbar = QScrollBar(Qt.Horizontal)
        self.waveform_scrollbar.setMinimum(0)
        self.waveform_scrollbar.setMaximum(0)
        self.waveform_scrollbar.valueChanged.connect(self.update_timeline_from_scrollbar)
        main_layout.addWidget(self.waveform_scrollbar)

        self.timeline_widget.x_offset_changed.connect(self.update_scrollbar_from_timeline)
        self.timeline_widget.x_scale_changed.connect(self.update_scrollbar_range)

        self.playback_monitor = QProgressBar(self)
        self.playback_monitor.setFormat("Time: %v/%m")
        self.playback_monitor.setTextVisible(True)
        main_layout.addWidget(self.playback_monitor)

        playback_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_audio)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_audio)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_audio)

        self.volume_label = QLabel("Volume", self)
        self.volume_label.setAlignment(Qt.AlignCenter)
        self.volume_monitor = QProgressBar(self)
        self.volume_monitor.setOrientation(Qt.Vertical)
        self.volume_monitor.setRange(0, 100)
        self.volume_monitor.setTextVisible(False)
        self.volume_level_signal.connect(self.update_volume_monitor)

        volume_layout = QVBoxLayout()
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_monitor)

        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.pause_button)
        playback_layout.addWidget(self.stop_button)
        playback_layout.addLayout(volume_layout)
        main_layout.addLayout(playback_layout)

        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None
        self.audio_data_buffer = np.array([])
        self.playback_position_samples = 0
        self.is_playing = False
        self.audio_duration = 0.0
        self.scrollbar_scale = 1000

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.update_playhead)
        self.playback_timer.start(30)

    def update_volume_monitor(self, level):
        self.volume_monitor.setValue(level)

    def load_audio_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.wav *.mp3)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.file_label.setText(f"Loaded: {selected_file}")

            self.stop_audio()

            self.histogram_widget.load_audio_and_process(selected_file)
            self.timeline_widget.load_audio_and_process(selected_file)
            self.audio_data_buffer = self.timeline_widget.audio_data
            self.playback_position_samples = 0

            self.audio_duration = self.audio_data_buffer.size / self.timeline_widget.sr if self.timeline_widget.sr > 0 else 0

            self.waveform_scrollbar.setMaximum(0)
            self.waveform_scrollbar.setValue(0)

            self.playback_monitor.setRange(0, int(self.audio_duration * self.scrollbar_scale))
            self.playback_monitor.setValue(0)

            # Timer to guarantee a correct fit-to-screen after the widget has rendered
            QTimer.singleShot(100, self.timeline_widget.fit_to_screen)

    def update_timeline_from_scrollbar(self, value):
        if self.waveform_scrollbar.maximum() > 0:
            offset_s = value / self.scrollbar_scale
            self.timeline_widget.set_x_offset(offset_s)

    def update_scrollbar_from_timeline(self, offset_s):
        self.waveform_scrollbar.blockSignals(True)
        self.waveform_scrollbar.setValue(int(offset_s * self.scrollbar_scale))
        self.waveform_scrollbar.blockSignals(False)

    def update_scrollbar_range(self, x_scale_px_per_s):
        if self.timeline_widget.audio_data.size == 0 or self.timeline_widget.sr == 0:
            self.waveform_scrollbar.setMaximum(0)
            return

        audio_duration = self.timeline_widget.audio_data.size / self.timeline_widget.sr
        visible_width_s = self.timeline_widget.width() / x_scale_px_per_s

        if audio_duration > visible_width_s:
            max_offset_s = audio_duration - visible_width_s
            self.waveform_scrollbar.setMaximum(int(max_offset_s * self.scrollbar_scale))
        else:
            self.waveform_scrollbar.setMaximum(0)

    def play_audio(self):
        if not self.is_playing and self.audio_data_buffer.size > 0:
            if self.stream is None:
                self.stream = self.pyaudio_instance.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.timeline_widget.sr,
                    output=True,
                    stream_callback=self._audio_callback
                )

            self.is_playing = True
            self.playback_position_samples = int(self.timeline_widget.playhead_position_s * self.timeline_widget.sr)
            self.stream.start_stream()

    def pause_audio(self):
        if self.is_playing:
            self.is_playing = False
            self.stream.stop_stream()

    def stop_audio(self):
        if self.stream:
            self.is_playing = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self.timeline_widget.set_playhead_position(0.0)
        self.playback_position_samples = 0
        self.playback_monitor.setValue(0)
        self.volume_monitor.setValue(0)

    def _audio_callback(self, in_data, frame_count, time_info, status):
        end_index = self.playback_position_samples + frame_count
        chunk = self.audio_data_buffer[self.playback_position_samples:end_index]

        if chunk.size > 0:
            rms = np.sqrt(np.mean(np.square(chunk)))
            volume_level = min(int(rms * 200), 100)
            self.volume_level_signal.emit(volume_level)
        else:
            self.volume_level_signal.emit(0)

        self.playback_position_samples = end_index

        if len(chunk) < frame_count:
            padding = np.zeros(frame_count - len(chunk), dtype=np.float32)
            chunk = np.concatenate((chunk, padding))
            self.is_playing = False
            return (chunk.tobytes(), pyaudio.paComplete)

        return (chunk.tobytes(), pyaudio.paContinue)

    def update_playhead(self):
        if self.is_playing:
            position_s = self.playback_position_samples / self.timeline_widget.sr
            self.timeline_widget.set_playhead_position(position_s)

            current_scaled_value = int(position_s * self.scrollbar_scale)

            self.playback_monitor.setValue(current_scaled_value)

    def closeEvent(self, event):
        self.stop_audio()
        self.pyaudio_instance.terminate()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioVisualizerUI()
    window.show()
    sys.exit(app.exec_())