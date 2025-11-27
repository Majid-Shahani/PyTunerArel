import threading
import time
import queue

import numpy as np
from librosa import yin
from audio import buffer


class Processor:
    def __init__(self, input_buffer: buffer.RollingBuffer, output_buffer: queue.Queue, fs, window_length):
        self._rolling_buffer = input_buffer
        self._output = output_buffer
        self._fs = fs
        self._window_length = window_length
        self._enable = False
        self._thread = None

    def _process_loop(self):
        while self._enable: # Main processing loop
            data = self._rolling_buffer.read() # Read audio data from the rolling buffer
            if data is not None: # If data is available
                rms = np.sqrt(np.mean(data ** 2)) # Calculate RMS to check signal strength
                threshold = 0.0075 # Threshold to ignore low-amplitude signals
                if rms < threshold:# If signal is too weak, skip processing
                    time.sleep(0.01) # Sleep briefly to avoid busy-waiting
                    continue # Continue to the next iteration

                frame = data.flatten() # Flatten the audio data
                f0 = yin(frame, fmin=50, fmax=500, sr=self._fs, frame_length=len(frame)) # Apply YIN algorithm to estimate fundamental frequency
                fundamental = np.median(f0) # Take the median of the estimated frequencies
                try:
                    self._output.put_nowait(fundamental) # Output the estimated frequency to the output queue
                except queue.Full: # If the output queue is full, skip this value
                    pass
            else:
                time.sleep(0.01) # Sleep briefly if no data is available

    def start_processing(self):
        if not self._enable:
            self._enable = True
            self._thread = threading.Thread(target=self._process_loop, daemon=True)
            self._thread.start()

    def stop_processing(self):
        self._enable = False
        if self._thread is not None:
            self._thread.join()
