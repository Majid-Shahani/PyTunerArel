import sounddevice as sd
import numpy as np
from audio.buffer import RollingBuffer


class AudioCapture:
    def __init__(self, buffer: RollingBuffer, fs, recording_time, channels):
        self._buffer = buffer
        self._sample_rate = fs
        self._window_time = recording_time
        self._channels = channels
        self._enable = False
        self._stream = None

    @property
    def enable(self):
        return self._enable


    def audio_callback(self, indata : np.ndarray, frames: int, time, status) -> None :
        if status:
           print(status)
        self._buffer.write(indata.squeeze())

    def start_recording(self):
        if not self._enable:
            self._enable = True
            self._stream = sd.InputStream(
                samplerate= self._sample_rate,
                channels= self._channels,
                blocksize= self._window_time,
                callback= self.audio_callback,
            )
            self._stream.start()

    def stop_recording(self):
        self._enable = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
