import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSizeGrip
from PyQt6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 400)
        
        self.grip_tl = QSizeGrip(self)
        self.grip_tr = QSizeGrip(self)
        self.grip_bl = QSizeGrip(self)
        self.grip_br = QSizeGrip(self)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grip_tl.move(0, 0)
        self.grip_tr.move(self.width() - 15, 0)
        self.grip_bl.move(0, self.height() - 15)
        self.grip_br.move(self.width() - 15, self.height() - 15)

app = QApplication(sys.argv)
win = TestWindow()
win.show()
app.exec()
