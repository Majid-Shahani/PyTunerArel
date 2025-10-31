from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QPoint
from GUI.tuner_widget import TunerWidget
from PyQt6.QtGui import QIcon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Tuner")

        self.ui = TunerWidget(self)
        self.setCentralWidget(self.ui)
        self.setWindowIcon(QIcon(r"Resources\Pick_Icon.png"))

        # Replace with your selected image file
        self.ui.set_background_image("Resources/Guitar_Head.png")
        self.setFixedSize(620, 800)

        # Adjust these to align with your tuning pegs
        self.ui.set_button_positions({
            "E2": QPoint(105,  205),
            "A": QPoint(105, 295),
            "D": QPoint(105, 385),
            "G": QPoint(460, 205),
            "B": QPoint(460, 295),
            "E4": QPoint(460, 385),
        })


