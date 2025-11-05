import librosa
import numpy as np

def loadWav(file, sr=None):
    # Load audio file,  setting sr=None to keep original sampling rate
    audio_data, srt = librosa.load(file, sr=sr)
    return audio_data, srt

def loadMp3(file):
    pass