import sys
import queue
import sounddevice

from PyQt6.QtWidgets import QApplication
from GUI.main_window import MainWindow

from audio import buffer, capture, process

AUDIO_CHANNELS = 1  # Mono channel
SAMPLERATE = 44100  # 441.k Hz
WINDOW_LENGTH = 8192  # Window length by Sample Count


def main():
    sounddevice.default.channels = AUDIO_CHANNELS
    sounddevice.default.samplerate = SAMPLERATE
    sounddevice.default.blocksize = WINDOW_LENGTH

    circular_buffer = buffer.RollingBuffer(5, chunk_size=AUDIO_CHANNELS * WINDOW_LENGTH)
    recorder = capture.AudioCapture(circular_buffer, SAMPLERATE, WINDOW_LENGTH, AUDIO_CHANNELS)
    recorder.start_recording()

    output_buffer = queue.Queue(maxsize=5)
    processor = process.Processor(circular_buffer, output_buffer, SAMPLERATE, WINDOW_LENGTH)
    processor.start_processing()

    app = QApplication(sys.argv)
    window = MainWindow(output_buffer)
    window.show()
    code = app.exec()

    processor.stop_processing()
    recorder.stop_recording()
    sys.exit(code)


if __name__ == "__main__":
    main()
