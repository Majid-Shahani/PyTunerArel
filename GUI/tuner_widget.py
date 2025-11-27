import queue
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
    QButtonGroup,
    QGraphicsOpacityEffect,
)


def _note_to_freq(note) -> float:
    """Convert standard tuning notes on guitar to their frequency in Hz."""
    note_frequencies = {
        "E2": 82.41,
        "A": 110.00,
        "D": 146.83,
        "G": 196.00,
        "B": 246.94,
        "E4": 329.63
    }
    return note_frequencies.get(note, 0.0)


class TunerWidget(QWidget):
    def __init__(self, freq_input_buffer:queue.Queue = None, parent=None):
        super().__init__(parent)

        # Audio Buffer
        self._buffer = freq_input_buffer

        # Rounded container styling
        self.image_label = QLabel(self)
        self.setObjectName("root")
        self.setStyleSheet("""
            QWidget#root {
                background-color: #1a1a1a;
                border-radius: 16px;
            }
        """)
        self.image_label.setScaledContents(False)
        self._orig_pix = None
        QTimer.singleShot(0, self._select_default_note)

        #Frequency tracking
        self.selected_frequency = None
        self.last_frequency = None
        self._last_offset = None

        # Layout: message on top, guitar image container below
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # Invisible message box (shown via helpers)
        self.message_label = QLabel("", self)
        self.message_label.setVisible(False)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("QLabel { color: #ffffff; background: transparent; padding: 6px; }")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.message_label.setFont(font)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(16)
        glow.setColor(QColor(0, 0, 0))
        glow.setOffset(0, 0)
        self.message_label.setGraphicsEffect(glow)

        self._root_layout.addWidget(self.message_label)

        # Image container without layout; we manage child geometry in resizeEvent
        self.image_container = QWidget(self)
        self.image_container.setStyleSheet("background: transparent;")
        self._root_layout.addWidget(self.image_container, 1)

        # Background image
        self.image_label = QLabel(self.image_container)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)

        # Transparent overlay for absolute-positioned circular buttons
        self.overlay = QWidget(self.image_container)
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.overlay.setStyleSheet("background: transparent;")

        # Create string buttons
        self.buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        for name in ["E2", "A", "D", "G", "B", "E4"]:
            btn = QPushButton(name, self.overlay)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(50, 50)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 100);
                    color: rgba(0, 0, 0, 255);
                    border: 2px solid rgba(0, 0, 0, 200);
                    border-radius: 25px;
                    font-weight: 1000;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 200);
                    border: 2px solid rgba(0, 0, 0, 220);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 220);
                    border: 2px solid rgba(0, 0, 0, 240);
                }
                QPushButton:checked {
                    background-color: rgba(255, 255, 255, 230);
                    border: 2px solid #39FF14;  /* neon green ring */
                }
            """)
            self.buttons[name] = btn
            self.button_group.addButton(btn)
        self.button_group.buttonClicked.connect(self._on_note_button)

        # Default placeholder positions
        self.set_button_positions({
            "D": QPoint(105,  205),
            "A": QPoint(105, 295),
            "E2": QPoint(105, 385),
            "G": QPoint(460, 205),
            "B": QPoint(460, 295),
            "E4": QPoint(460, 385),
        })


        # Neon cursive note + frequency labels (bottom-left)
        self._info_left_margin = 18
        self._info_bottom_margin = 60
        self._info_gap = 12

        self.note_label = QLabel("E2", self.overlay)
        self.freq_label = QLabel("freq: ---Hz", self.overlay)

        # Cursive, neon-like styling
        note_font = QFont("Segoe Script", 28)
        note_font.setStyleHint(QFont.StyleHint.Cursive)
        note_font.setItalic(True)
        self.note_label.setFont(note_font)
        self.note_label.setStyleSheet("QLabel { color: #39FF14; background: transparent; }")

        freq_font = QFont("Segoe Script", 16)
        freq_font.setStyleHint(QFont.StyleHint.Cursive)
        freq_font.setItalic(True)
        self.freq_label.setFont(freq_font)
        self.freq_label.setStyleSheet("QLabel { color: #E287FF; background: transparent; }")

        note_glow = QGraphicsDropShadowEffect(self)
        note_glow.setBlurRadius(36)
        note_glow.setColor(QColor(57, 255, 20, 180))  # light neon green
        note_glow.setOffset(0, 0)
        self.note_label.setGraphicsEffect(note_glow)

        freq_glow = QGraphicsDropShadowEffect(self)
        freq_glow.setBlurRadius(28)
        freq_glow.setColor(QColor(226, 135, 255, 180))  # light purple/pinkish
        freq_glow.setOffset(0, 0)
        self.freq_label.setGraphicsEffect(freq_glow)

        self.note_label.setVisible(True)
        self.freq_label.setVisible(True)

        self._status_right_margin = 30  # right padding for status text
        self._status_bottom_margin = 90

        self.status_label = QLabel("", self.overlay)
        status_font = QFont("Segoe Script", 20)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("QLabel { color: #00BFFF; background: transparent; }")  # bright blue

        status_glow = QGraphicsDropShadowEffect(self)
        status_glow.setBlurRadius(32)
        status_glow.setColor(QColor(0, 191, 255, 200))  # neon blue glow
        status_glow.setOffset(0, 0)
        self._status_opacity = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(self._status_opacity)
        self._status_opacity.setOpacity(0.0)
        self.status_label.setVisible(False)

        # opacity effect for fade-out
        self._status_opacity = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(status_glow)  # keep glow
        self.status_label.setGraphicsEffect(self._status_opacity)  # stack opacity (last set wins)
        self._status_opacity.setOpacity(0.0)

        self._status_anim = None  # will hold QPropertyAnimation

        # Default selection
        if "E2" in self.buttons:
            self.buttons["E2"].setChecked(True)
            self._set_selected_note("E2")

        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(66)
        self._frame_timer.timeout.connect(self._on_frame)
        self._frame_timer.start()

    def _read_buffer(self):
        if not self._buffer:
            return
        try:
            while not self._buffer.empty():
                self.last_frequency = self._buffer.get_nowait()
        except Exception:
            # swallow errors from audio buffer so GUI doesn't crash
            self.last_frequency = None

    def _on_frame(self):
        self._read_buffer()
        # run on the GUI thread; keep work light
        self.update_frequency_display()

    def _update_scaled_pixmap(self):
        if not self._orig_pix:
            return
        target = self.image_container.size()
        if target.isEmpty():
            return
        scaled = self._orig_pix.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _layout_info_labels(self):
        # Bottom-left anchoring with gap
        w = self.overlay.width()
        h = self.overlay.height()
        left = self._info_left_margin
        bottom = self._info_bottom_margin

        note_h = self.note_label.sizeHint().height()
        freq_h = self.freq_label.sizeHint().height()

        freq_y = max(0, h - bottom - freq_h)
        note_y = max(0, freq_y - self._info_gap - note_h)

        self.note_label.move(left, note_y)
        self.freq_label.move(left, freq_y)

        # Bottom-right status label aligned with note's top line
        status_sz = self.status_label.sizeHint()
        status_x = max(0, w - self._status_right_margin - status_sz.width())
        status_y = max(0, h - self._status_bottom_margin - status_sz.height())
        self.status_label.move(status_x, status_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # guard early during construction
        if not hasattr(self, "image_container") or self.image_container is None:
            return
        r = QRect(QPoint(0, 0), self.image_container.size())
        self.image_label.setGeometry(r)
        self.overlay.setGeometry(r)
        self.overlay.raise_()
        self._update_scaled_pixmap()
        # correct method name (was __info_labels)
        self._layout_info_labels()

    def set_background_image(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            return
        self._orig_pix = pix
        self._update_scaled_pixmap()

    def set_button_positions(self, positions: dict[str, QPoint | tuple[int, int]]):
        for name, pos in positions.items():
            if name in self.buttons:
                if isinstance(pos, tuple):
                    pos = QPoint(pos[0], pos[1])
                self.buttons[name].move(pos)

    # Public helpers to control text
    def show_status(self, text: str, duration_ms: int = 4000):
        # prepare label
        self.status_label.setText(text)
        self.status_label.adjustSize()
        self._layout_info_labels()
        self.status_label.setVisible(True)

        # reset any running animation
        if self._status_anim is not None:
            self._status_anim.stop()

        # start from full opacity
        self._status_opacity.setOpacity(1.0)

        # animate opacity -> 0 over duration_ms
        self._status_anim = QPropertyAnimation(self._status_opacity, b"opacity", self)
        self._status_anim.setDuration(duration_ms)
        self._status_anim.setStartValue(1.0)
        self._status_anim.setEndValue(0.0)
        self._status_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._status_anim.finished.connect(lambda: self.status_label.setVisible(False))
        self._status_anim.start()

    def set_info_margins(self, left: int = 18, bottom: int = 18, gap: int = 6):
        self._info_left_margin = left
        self._info_bottom_margin = bottom
        self._info_gap = gap
        self._layout_info_labels()

    def update_frequency_display(self):
        if self.last_frequency is None:
            self.freq_label.setText("freq: ---Hz")
        else:
            self.freq_label.setText(f"freq: {self.last_frequency:.2f}Hz")

        self.freq_label.adjustSize()
        self.note_label.adjustSize()
        self._layout_info_labels()

        new_offset = self._calculate_offset()
        if new_offset != getattr(self, "_last_offset", None):
            self._last_offset = new_offset
            self.show_status(new_offset)

    def _apply_selected_glow(self, selected_btn: QPushButton | None):
        # Clear glow from all buttons
        for b in self.buttons.values():
            b.setGraphicsEffect(None)
        if selected_btn is None:
            return
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(36)
        glow.setColor(QColor(57, 255, 20, 200))  # neon green glow
        glow.setOffset(0, 0)
        selected_btn.setGraphicsEffect(glow)

    # Single-selection handling
    def _select_default_note(self):
        btn = self.buttons.get("E2")
        if not btn:
            return
        # Ensure buttons are checkable where you create them: btn.setCheckable(True)
        btn.setChecked(True)
        self._set_selected_note("E2")
        self._apply_selected_glow(btn)

    def _on_note_button(self, btn: QPushButton):
        self._set_selected_note(btn.text())
        self._apply_selected_glow(btn)

    def _set_selected_note(self, note: str):
        self.note_label.setText(note)
        self.selected_frequency = _note_to_freq(note)
        self._layout_info_labels()


    def _show_message(self, text: str):
        self.message_label.setText(text)
        self.message_label.setVisible(True)


    #Note to Frequency and offset calculator

    def _calculate_offset(self) -> str:
        if self.last_frequency is None or self.selected_frequency is None:
            return "No Frequency"
        """Calculate the offset in percentage from the selected frequency."""
        temp = (self.last_frequency - self.selected_frequency)/(self.selected_frequency*0.01)
        if -0.5 < temp < 0.5:
            return "PERFECT!"
        elif -1 < temp < 1:
            return "It's Great"
        elif temp <= -1:
            return "Tune up"
        else:
            return "Tune down"

    # def createPitchOffsetStr(noteName, offset):
    #     """Create a string to indicate whether the pitch is sharp or flat."""
    #     rounded_offset = round(offset * 10)
    #     char_to_use = ">" if rounded_offset < 0 else "<"
    #     num_chars = abs(rounded_offset)
    #     max_chars = 5
    #     if num_chars > max_chars:
    #         num_chars = max_chars
    #     offset_str = char_to_use * num_chars
    #     if rounded_offset < 0:
    #         return f'{offset_str:>{max_chars}}{noteName}{" " * max_chars}'
    #     else:
    #         return f'{" " * max_chars}{noteName}{offset_str:<{max_chars}}'
    #
    # def freqToNote(freqHz: float) -> tuple[str, float]:
    #     """Convert a frequency to a musical note and calculate the offset."""
    #     notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    #     freq_hz_of_a4 = 440
    #     num_semitones = 12
    #     note_num_of_a4 = 49
    #
    #     if freqHz <= 0:
    #         return "INVALID_STR", 0  # Ensure a tuple is returned for invalid frequencies
    #     note_number = num_semitones * math.log2(freqHz / freq_hz_of_a4) + note_num_of_a4
    #     rounded_note_number = round(note_number)
    #     note_name = notes[(rounded_note_number - 1) % len(notes)]
    #     octave = (rounded_note_number + 8) // len(notes)
    #     full_note = f'{note_name}{octave}'
    #     diff = note_number - rounded_note_number
    #     return full_note, diff