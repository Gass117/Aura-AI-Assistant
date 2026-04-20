import keyboard
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QSlider, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QSizePolicy, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QRect
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QPalette

from modules.cattura import WindowCaptureThread, get_active_windows
from modules.api_manager import ApiManager


class ApiWorker(QThread):
    result_ready = pyqtSignal(str)
    
    def __init__(self, api_manager, window_titles, user_prompt, images):
        super().__init__()
        self.api_manager = api_manager
        self.window_titles = window_titles
        self.user_prompt = user_prompt
        self.images = images
        
    def run(self):
        res = self.api_manager.send_message(self.window_titles, self.user_prompt, self.images)
        self.result_ready.emit(res)


class AuraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_manager = ApiManager()
        self.last_images = {1: None, 2: None}
        self.current_hwnd_1 = None
        self.current_hwnd_2 = None
        self.is_dual_mode = False
        
        self.init_ui()
        self.init_threads()
        self.setup_hotkey()
        
    def init_ui(self):
        self.setWindowTitle("Aura AI Assistant")
        # Posiziona in alto a destra
        screen = self.screen().availableGeometry()
        width, height = 450, 700
        self.setGeometry(screen.width() - width - 20, 20, width, height)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QWidget { color: #FFFFFF; font-family: 'Segoe UI', Inter, sans-serif; }
            QComboBox, QLineEdit {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #007ACC;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D30;
                color: #FFFFFF;
                selection-background-color: #007ACC;
            }
            QTextEdit {
                background-color: #252526;
                border: 1px solid #3E3E42;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0E639C;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177BB; }
            QPushButton:pressed { background-color: #094771; }
            QSlider::groove:horizontal { border: 1px solid #bbb; background: white; height: 10px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #0E639C; border: 1px solid #777; height: 10px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #eee; border: 1px solid #777; width: 13px; margin-top: -2px; margin-bottom: -2px; border-radius: 4px; }
            QCheckBox { spacing: 8px; font-weight: bold; }
            QCheckBox::indicator { width: 15px; height: 15px; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Dual mode switch
        top_layout = QHBoxLayout()
        self.dual_mode_switch = QCheckBox("Modalità Doppia Finestra")
        self.dual_mode_switch.stateChanged.connect(self.toggle_dual_mode)
        top_layout.addWidget(self.dual_mode_switch)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Aggiorna Liste")
        refresh_btn.setFixedWidth(130)
        refresh_btn.clicked.connect(self.refresh_windows_list)
        top_layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(top_layout)
        
        # Selectors & Thumbnails Layout
        self.windows_layout = QHBoxLayout()
        
        # -- Colonna 1 --
        col1 = QVBoxLayout()
        self.window_selector_1 = QComboBox()
        self.window_selector_1.currentIndexChanged.connect(lambda idx: self.on_window_selected(idx, 1))
        self.thumbnail_1 = QLabel("Nessuna cattura")
        self.thumbnail_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_1.setFixedHeight(120)
        self.thumbnail_1.setStyleSheet("background-color: #000000; border-radius: 5px;")
        col1.addWidget(QLabel("Finestra 1:"))
        col1.addWidget(self.window_selector_1)
        col1.addWidget(self.thumbnail_1)
        self.windows_layout.addLayout(col1)
        
        # -- Colonna 2 --
        self.col2_widget = QWidget()
        col2 = QVBoxLayout(self.col2_widget)
        col2.setContentsMargins(0,0,0,0)
        self.window_selector_2 = QComboBox()
        self.window_selector_2.currentIndexChanged.connect(lambda idx: self.on_window_selected(idx, 2))
        self.thumbnail_2 = QLabel("Nessuna cattura")
        self.thumbnail_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_2.setFixedHeight(120)
        self.thumbnail_2.setStyleSheet("background-color: #000000; border-radius: 5px;")
        col2.addWidget(QLabel("Finestra 2:"))
        col2.addWidget(self.window_selector_2)
        col2.addWidget(self.thumbnail_2)
        self.windows_layout.addWidget(self.col2_widget)
        
        self.col2_widget.hide() # Nascondi all'inizio
        
        layout.addLayout(self.windows_layout)
        
        # Opacity Slider
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("Opacità:")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(90)
        self.setWindowOpacity(0.9)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v / 100.0))
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        layout.addLayout(opacity_layout)
        
        # Chat History
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("<b>Aura:</b> Ciao! Seleziona una finestra (o due) e fammi una domanda.")
        layout.addWidget(self.chat_display)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Chiedi qualcosa sul contesto visivo...")
        self.chat_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Invia")
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        self.refresh_windows_list()

    def toggle_dual_mode(self, state):
        self.is_dual_mode = (state == 2) # Qt.CheckState.Checked is 2
        if self.is_dual_mode:
            self.col2_widget.show()
        else:
            self.col2_widget.hide()
            self.current_hwnd_2 = None
            self.last_images[2] = None
            self.thumbnail_2.setPixmap(QPixmap())
            self.thumbnail_2.setText("Nessuna cattura")
            
        self.update_capture_hwnds()

    def init_threads(self):
        self.capture_thread = WindowCaptureThread()
        self.capture_thread.frames_captured.connect(self.on_frames_captured)
        self.capture_thread.start()
        
    def refresh_windows_list(self):
        self.window_selector_1.blockSignals(True)
        self.window_selector_2.blockSignals(True)
        
        self.window_selector_1.clear()
        self.window_selector_2.clear()
        
        self.window_selector_1.addItem("-- Seleziona Finestra 1 --", None)
        self.window_selector_2.addItem("-- Seleziona Finestra 2 --", None)
        
        windows = get_active_windows()
        for w in windows:
            self.window_selector_1.addItem(w['title'], w['hwnd'])
            self.window_selector_2.addItem(w['title'], w['hwnd'])
            
        self.window_selector_1.blockSignals(False)
        self.window_selector_2.blockSignals(False)
            
    def on_window_selected(self, index, selector_num):
        if index > 0:
            if selector_num == 1:
                self.current_hwnd_1 = self.window_selector_1.itemData(index)
            elif selector_num == 2:
                self.current_hwnd_2 = self.window_selector_2.itemData(index)
        else:
            if selector_num == 1: self.current_hwnd_1 = None
            if selector_num == 2: self.current_hwnd_2 = None
            
        self.update_capture_hwnds()
        
    def update_capture_hwnds(self):
        hwnds = []
        if self.current_hwnd_1: hwnds.append(self.current_hwnd_1)
        if self.is_dual_mode and self.current_hwnd_2: hwnds.append(self.current_hwnd_2)
        self.capture_thread.set_windows(hwnds)

    def on_frames_captured(self, frames_dict):
        # frames_dict contains {hwnd: PIL.Image}
        if self.current_hwnd_1 in frames_dict:
            img1 = frames_dict[self.current_hwnd_1]
            self.last_images[1] = img1
            self.display_image(img1, self.thumbnail_1)
            
        if self.is_dual_mode and self.current_hwnd_2 in frames_dict:
            img2 = frames_dict[self.current_hwnd_2]
            self.last_images[2] = img2
            self.display_image(img2, self.thumbnail_2)

    def display_image(self, pil_image, label):
        data = pil_image.tobytes("raw", "RGB")
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qim)
        pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)

    def send_message(self):
        prompt = self.chat_input.text().strip()
        if not prompt:
            return
            
        self.chat_input.clear()
        self.chat_display.append(f"<br><b>Tu:</b> {prompt}")
        
        titles = []
        images = []
        
        if self.current_hwnd_1 and self.last_images[1]:
            titles.append(self.window_selector_1.currentText())
            images.append(self.last_images[1])
            
        if self.is_dual_mode and self.current_hwnd_2 and self.last_images[2]:
            titles.append(self.window_selector_2.currentText())
            images.append(self.last_images[2])
            
        if not titles:
            self.chat_display.append("<br><b style='color: #FF5252;'>Aura:</b> Seleziona almeno una finestra attiva prima di inviare un messaggio!")
            return
            
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        self.api_worker = ApiWorker(self.api_manager, titles, prompt, images)
        self.api_worker.result_ready.connect(self.on_api_response)
        self.api_worker.start()
        
    def on_api_response(self, response):
        self.chat_display.append(f"<br><b style='color: #4CAF50;'>Aura:</b> {response}")
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.chat_input.setFocus()

    def setup_hotkey(self):
        try:
            keyboard.add_hotkey('ctrl+shift+a', self.toggle_visibility)
        except Exception as e:
            print(f"Impossibile registrare l'hotkey: {e}")

    def toggle_visibility(self):
        if self.isHidden():
            self.show()
            self.activateWindow()
        else:
            self.hide()

    def closeEvent(self, event):
        self.capture_thread.stop()
        super().closeEvent(event)
