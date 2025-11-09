import queue
from collections import deque
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
import pyqtgraph as pg
import numpy as np


class PlotsWindow(QMainWindow):
    def __init__(self, input_buffer: object, output_queue: queue.Queue, fs: int, window_length: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Signal Plots")
        self._input_buffer = input_buffer
        self._output_buffer = output_queue
        self._fs = fs
        self._window_length = window_length

        self.setWindowIcon(QIcon(r"Resources\bar.png"))

        # Create three stacked pyqtgraph plots
        self.plot_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_fft = pg.PlotWidget(title="FFT (magnitude)")
        self.plot_yin = pg.PlotWidget(title="YIN (f0 over time)")

        self.plot_raw.setLabel('left', 'Amplitude')
        self.plot_fft.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_fft.setLabel('left', 'Magnitude')
        self.plot_yin.setLabel('left', 'Frequency', units='Hz')

        central = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        layout.addWidget(self.plot_raw)
        layout.addWidget(self.plot_fft)
        layout.addWidget(self.plot_yin)
        central.setLayout(layout)
        self.setCentralWidget(central)

        # Plot handles
        self.raw_curve = self.plot_raw.plot(pen='y')
        self.fft_curve = self.plot_fft.plot(pen='c')
        self.yin_curve = self.plot_yin.plot(pen='m')

        # YIN history
        history_len = max(1, int(self._fs / 10))
        self.yin_history = deque(maxlen=history_len)

        # Timer to refresh plots (~30 Hz)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._update_plots)
        self._timer.start()

    def _update_plots(self):
        # Read latest audio frame
        try:
            data = self._input_buffer.read()
        except Exception:
            data = None

        if data is not None:
            frame = np.asarray(data).flatten()
            if frame.size > 0:
                # Raw
                self.raw_curve.setData(frame)

                # FFT
                win = np.hanning(len(frame))
                spectrum = np.fft.rfft(frame * win)
                mags = np.abs(spectrum)
                freqs = np.fft.rfftfreq(len(frame), d=1.0 / self._fs)
                self.fft_curve.setData(freqs, mags)

        # Drain YIN output queue non-blocking
        try:
            while True:
                f0 = self._output_buffer.get_nowait()
                if f0 is None or not np.isfinite(f0):
                    continue
                self.yin_history.append(float(f0))
        except queue.Empty:
            pass

        # Plot YIN history as time series
        if len(self.yin_history) > 0:
            y = np.array(self.yin_history)
            x = np.linspace(-len(y) / float(max(1, len(y))), 0.0, num=len(y))
            self.yin_curve.setData(x, y)
        else:
            self.yin_curve.clear()