import sys
import time
import os

import pydub.utils
from pylab import *
from pydub import AudioSegment
from pydub import *
import numpy as np

ffmpeg_path = os.path.join("C:", "Network-ext", "LightCommander", "ffmpeg.exe")  # replace with your actual path
ffmpeg_play = os.path.join("C:", "Network-ext", "LightCommander", "ffplay.exe")  # replace with your actual path
ffmpeg_probe = os.path.join("C:", "Network-ext", "LightCommander", "ffprobe.exe")  # replace with your actual path
print(ffmpeg_path)
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffmpeg_probe


def show_wave_n_spec_mp3(speech_file):
    """
    Reads an MP3 file, displays its waveform and spectrogram.
    """
    try:
        sound = AudioSegment.from_mp3(speech_file)
    except Exception as e:
        print(f"Error loading MP3 file: {e}")
        return

    # Convert to mono (if it's stereo) for simplicity in plotting
    sound = sound.set_channels(1)
    raw_audio_data = np.array(sound.get_array_of_samples())
    frame_rate = sound.frame_rate

    subplot(211)
    plot(raw_audio_data)
    title(f'Waveform and spectrogram of {sys.argv[1]}')
    xlabel('Time (samples)')
    ylabel('Amplitude')

    subplot(212)
    spectrogram = specgram(raw_audio_data, Fs=frame_rate, scale_by_freq=True, sides='default')
    xlabel('Time (s)')
    ylabel('Frequency (Hz)')

    show()

if len(sys.argv) < 2:
    print("Usage: python your_script_name.py <audio_file.mp3>")
    sys.exit(1)

fil = sys.argv[1]

show_wave_n_spec_mp3(fil)
