import threading
import time
import math
import numpy as np
from audio import buffer
from librosa import yin


def _note_to_freq(note: int) -> float:
    """Convert standard tuning notes on guitar to their frequency in Hz."""
    note_frequencies = {
        6: 82.41,
        5: 110.00,
        4: 146.83,
        3: 196.00,
        2: 246.94,
        1: 329.63
    }
    return note_frequencies.get(note, 0.0)


def _calculate_offset(frequency: float, target_frequency: float) -> int:
    """Calculate the offset from range: -3 to +3, where 0 is in tune."""
    temp = frequency - target_frequency
    if -1 < temp < 1:
        return 0
    elif -5 < temp <= -1:
        return -1
    elif -10 < temp <= -5:
        return -2
    elif temp <= -10:
        return -3
    elif 1 <= temp < 5:
        return 1
    elif 5 <= temp < 10:
        return 2
    elif temp >= 10:
        return 3
    else:
        return 5


class Processor:
    def __init__(self, rolling_buffer: buffer.RollingBuffer, fs, window_length):
        self._rolling_buffer = rolling_buffer
        self._fs = fs
        self._window_length = window_length
        self._enable = False
        self._thread = None

    def _process_loop(self):
        while self._enable:
            data = self._rolling_buffer.read()
            if data is not None:
                rms = np.sqrt(np.mean(data ** 2))
                threshold = 0.0075
                if rms < threshold:
                    time.sleep(0.01)
                    continue

                frame = data.flatten()
                f0 = yin(frame, fmin=50, fmax=500, sr=self._fs, frame_length=len(frame))
                fundamental = np.median(f0)
                print (f"Detected fundamental frequency: {fundamental:.2f} Hz")
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
