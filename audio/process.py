import threading
import time

import numpy as np
from audio import buffer
from scipy.signal import stft
from librosa import yin
"""
def find_fundamentals(freqs, mag, max_harmonics= 5, n_fundamentals=3, min_freq = 50, max_freq =1500):
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    mag_masked = mag.copy()
    mag_masked[~mask] = 0

    mag_masked = np.convolve(mag_masked, np.ones(5)/5, mode='same')
    hps = mag_masked.copy()
    for h in range(2, max_harmonics + 1):
        decimated = mag_masked[::h]
        hps[:len(decimated)] *= decimated

    indices = np.argsort(hps)[::-1][:n_fundamentals]
    return indices
"""
class Processor:
    def __init__(self, rolling_buffer: buffer.RollingBuffer , fs, window_length):
        self._rolling_buffer = rolling_buffer
        self._fs = fs
        self._window_length = window_length
        self._enable = False
        self._thread = None

    def _process_loop(self):
        while self._enable:
            data = self._rolling_buffer.read()
            if data is not None:
                rms = np.sqrt(np.mean(data**2))
                threshold = 0.01
                if rms < threshold:
                    time.sleep(0.01)
                    continue

                frame = data.flatten()
                f0 = yin(frame, fmin=50, fmax= 500, sr=self._fs, frame_length=len(frame))
                fundamental = np.median(f0)
                print("Detected pitch: ", fundamental)
                """
                frequencies, times, zxx = stft(data, fs=self._fs, window='hann', nperseg=self._window_length, noverlap= int(self._window_length * 0.5), boundary=None, padded=False)
                #do whatever
                avg_mag = np.mean(np.abs(zxx), axis=1)
                #peaks, _= find_peaks(avg_mag, prominence=np.max(avg_mag) * 0.1, distance=5)
                peaks = find_fundamentals(frequencies, avg_mag)
                if peaks is None or len(peaks) == 0:
                    time.sleep(0.01)
                    continue

                sorted_peaks = np.argsort(avg_mag[peaks])[::-1]
                top_peaks = peaks[sorted_peaks[:3]]
                dominant_freqs = frequencies[top_peaks]
                print("Dominant frequencies (Hz): ", dominant_freqs)
                """
            else:
                time.sleep(0.01)

    def start_processing(self):
        if not self._enable:
            self._enable = True
            self._thread = threading.Thread(target=self._process_loop, daemon=True)
            self._thread.start()

    def stop_processing(self):
        self._enable = False
        if self._thread is not None:
            self._thread.join()
