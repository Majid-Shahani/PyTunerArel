import sys
import time
import multiprocessing as mp

import numpy as np
import sounddevice

from PyQt6.QtWidgets import QApplication
from GUI.main_window import MainWindow

from audio import buffer, capture, process

AUDIO_CHANNELS = 1  # Mono channel
SAMPLERATE = 44100  # 441.k Hz
WINDOW_LENGTH = 8192  # Window length by Sample Count


def gui_process(output_buffer):
    app = QApplication(sys.argv)
    window = MainWindow(output_buffer)
    window.show()
    sys.exit(app.exec())


def main():
    sounddevice.default.channels = AUDIO_CHANNELS
    sounddevice.default.samplerate = SAMPLERATE
    sounddevice.default.blocksize = WINDOW_LENGTH

    circular_buffer = buffer.RollingBuffer(5, chunk_size=AUDIO_CHANNELS * WINDOW_LENGTH)
    recorder = capture.AudioCapture(circular_buffer, SAMPLERATE, WINDOW_LENGTH, AUDIO_CHANNELS)
    recorder.start_recording()

    output_buffer = mp.Queue(maxsize=5)
    processor = process.Processor(circular_buffer, output_buffer, SAMPLERATE, WINDOW_LENGTH)
    processor.start_processing()

    gui = mp.Process(target=gui_process, args=(output_buffer,), daemon=True)
    gui.start()

    try:
        while gui.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        processor.stop_processing()
        recorder.stop_recording()
        gui.terminate()


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
