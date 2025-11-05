from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt
import sys
import numpy as np
# import wave # Not needed when using Librosa for loading
import librosa  # Import the Librosa library
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import QTimer, QPointF
from OpenGL.GL import *
import pyaudio


class AudioHistogramWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = []  # To store processed histogram data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // 60)  # Update at 60 FPS

    def initializeGL(self):
        glClearColor(0.1, 0.2, 0.3, 1.0)  # Background color
        # Additional OpenGL setup if needed

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)  # Set the viewport

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # Check if the array is empty using .size
        if len(self.audio_data) > 0:  # Check if there are elements in the array
            bar_width = 2.0 / len(self.audio_data)
            for i, height in enumerate(self.audio_data):
                x_pos = -1.0 + i * bar_width
                glColor3f(0.5, 0.8, 0.6)  # Set bar color
                glBegin(GL_QUADS)
                glVertex2f(x_pos, -1.0)
                glVertex2f(x_pos + bar_width, -1.0)
                glVertex2f(x_pos + bar_width, -1.0 + height)
                glVertex2f(x_pos, -1.0 + height)
                glEnd()
        else:
            # Optionally handle the case where the array is empty (e.g., do nothing)
            pass

    def load_audio_and_process(self, filename):
        if isinstance(filename, list):
            filename = filename[0]  # Take the first file if a list is passed

        try:
            # Load the audio file using Librosa
            # librosa.load returns the audio time series (y) and the sampling rate (sr)
            y, sr = librosa.load(filename, sr=None)  # sr=None preserves the original sampling rate

            # Perform FFT
            # Use Short-Time Fourier Transform (STFT) for spectral analysis
            D = np.abs(librosa.stft(y))

            # You might want to average the magnitude spectrum over time for a simple histogram
            magnitude_spectrum = np.mean(D, axis=1)

            # Normalize for OpenGL display
            max_mag = np.max(magnitude_spectrum)
            if max_mag > 0:
                self.audio_data = (magnitude_spectrum / max_mag) * 2.0
            else:
                self.audio_data = []  # Clear if no magnitude to display

            self.update()  # Trigger redraw

        except Exception as e:
            print(f"Error loading or processing audio file: {e}")
            # You might want to display an error message in the UI


class WaveformTimelineWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = np.array([])
        self.sr = 0
        self.playhead_position_s = 0.0
        self.x_offset_s = 0.0
        self.x_scale_px_per_s = 100.0
        self.y_scale_factor = 1.0
        self.last_mouse_pos = QPointF()
        self.panning = False
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.update_playhead)

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.2, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.update_projection(w, h)

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

    def paintGL(self):

        if len(self.audio_data) > 0:
            self.x_scale_px_per_s = ( len(self.audio_data) / self.width() ) / 10

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        if self.audio_data.size == 0:
            return

        # Draw Waveform (simplified per-pixel min/max)
        glColor3f(0.6, 0.8, 0.9)
        visible_width_s = self.width()
        start_time_s = self.x_offset_s
        end_time_s = self.x_offset_s + visible_width_s
        start_sample = max(0, int(start_time_s * self.sr))
        end_sample = min(self.audio_data.size, int(end_time_s * self.sr))
        if end_sample <= start_sample:
            return

        samples_per_pixel = (end_sample - start_sample) / self.width()
        glBegin(GL_TRIANGLE_STRIP)
        current_time_s = start_time_s
        current_pixel_x = 0
        while current_pixel_x < self.width():
            sample_idx_start = start_sample + int(current_pixel_x * samples_per_pixel)
            sample_idx_end = min(start_sample + int((current_pixel_x + 1) * samples_per_pixel), end_sample)
            if sample_idx_end > sample_idx_start:
                window_samples = self.audio_data[sample_idx_start:sample_idx_end]
                if window_samples.size > 0:
                    max_val = np.max(window_samples)
                    min_val = np.min(window_samples)
                    glVertex2f(current_time_s, max_val)
                    glVertex2f(current_time_s, min_val)
            current_time_s += 1.0 / self.x_scale_px_per_s
            current_pixel_x += 1
        glEnd()

        # Draw Playhead
        if 0 <= self.playhead_position_s <= (self.audio_data.size / self.sr):
            glColor3f(1.0, 0.0, 0.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glVertex2f(self.playhead_position_s, -1.0 * self.y_scale_factor)
            glVertex2f(self.playhead_position_s, 1.0 * self.y_scale_factor)
            glEnd()
            glLineWidth(1.0)

    def load_audio_and_process(self, filename):
        if isinstance(filename, list): filename = filename[0]
        try:
            self.audio_data, self.sr = librosa.load(filename, sr=None)
            if np.max(np.abs(self.audio_data)) > 0:
                self.audio_data = self.audio_data / np.max(np.abs(self.audio_data))
            self.playhead_position_s = 0.0
            self.x_offset_s = 0.0
            self.update_projection(self.width(), self.height())
            self.update()
        except Exception as e:
            print(f"Error loading or processing audio file: {e}")

    def update_playhead(self):
        # Placeholder: This would be updated by the audio playback thread
        self.playhead_position_s += 0.01
        audio_duration = self.audio_data.size / self.sr
        if self.playhead_position_s > audio_duration:
            self.playhead_position_s = 0.0

        visible_width_s = self.width() / self.x_scale_px_per_s
        if self.playhead_position_s > self.x_offset_s + visible_width_s * 0.8:
            self.x_offset_s = self.playhead_position_s - visible_width_s * 0.2
            self.update_projection(self.width(), self.height())

        self.update()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            self.panning = True
            widget_width_s = self.width() / self.x_scale_px_per_s
            time_at_mouse_s = self.x_offset_s + (event.x() / self.width()) * widget_width_s
            audio_duration = self.audio_data.size / self.sr
            self.playhead_position_s = max(0.0, min(time_at_mouse_s, audio_duration))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.panning = False

    def mouseMoveEvent(self, event):
        if self.panning:
            delta_x_pixels = event.x() - self.last_mouse_pos.x()
            delta_time_s = delta_x_pixels / self.x_scale_px_per_s
            self.x_offset_s -= delta_time_s
            audio_duration = self.audio_data.size / self.sr
            max_offset_s = audio_duration - (self.width() / self.x_scale_px_per_s)
            if max_offset_s < 0:
                self.x_offset_s = 0.0
            else:
                self.x_offset_s = max(0.0, min(self.x_offset_s, max_offset_s))
            self.last_mouse_pos = event.pos()
            self.update_projection(self.width(), self.height())

def calculateHistogramW(audio_data):
    hist, bin_edges = np.histogram(audio_data, bins=256, range=(-1, 1))
    return hist, bin_edges


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