import threading
import time
import multiprocessing as mp
import queue

import numpy as np
from librosa import yin
from audio import buffer


class Processor:
    def __init__(self, input_buffer: buffer.RollingBuffer, output_buffer: mp.Queue, fs, window_length):
        self._rolling_buffer = input_buffer
        self._output = output_buffer
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
                try:
                    self._output.put_nowait(fundamental)
                except queue.Full:
                    pass
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
