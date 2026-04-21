import sys
import keyboard
import markdown
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QSlider, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QCheckBox, QFrame, QDialog, QTreeWidget, QTreeWidgetItem, QSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QImage, QPixmap, QIcon, QFont, QColor

from modules.cattura import WindowCaptureThread, get_active_windows
from modules.api_manager import ApiManager
from modules.settings_manager import load_settings, save_settings
from modules.history_manager import load_history, add_to_history

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ApiWorker(QThread):
    result_ready = pyqtSignal(str)
    
    def __init__(self, api_manager, window_titles, user_prompt, images, model_name):
        super().__init__()
        self.api_manager = api_manager
        self.window_titles = window_titles
        self.user_prompt = user_prompt
        self.images = images
        self.model_name = model_name
        
    def run(self):
        res = self.api_manager.send_message(self.window_titles, self.user_prompt, self.images, self.model_name)
        self.result_ready.emit(res)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni Aura")
        self.setFixedSize(320, 300)
        self.settings = load_settings()
        
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: white; }
            QLabel { color: white; font-weight: bold; }
            QComboBox, QSpinBox { background-color: #2D2D30; color: white; border: 1px solid #555; padding: 5px; border-radius: 4px; }
            QComboBox QAbstractItemView { background-color: #2D2D30; color: white; }
            QPushButton { background-color: #0E639C; color: white; padding: 10px; border-radius: 4px; font-weight: bold; min-width: 100px; }
            QPushButton:hover { background-color: #1177BB; }
        """)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Segoe UI", "Roboto", "Nunito", "Verdana", "Tahoma"])
        self.font_combo.setCurrentText(self.settings.get("font_family", "Segoe UI"))
        layout.addWidget(self.font_combo)
        
        layout.addWidget(QLabel("Dimensione Font:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 24)
        self.size_spin.setValue(self.settings.get("font_size", 13))
        layout.addWidget(self.size_spin)
        
        layout.addWidget(QLabel("Colore Testo:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["#FFFFFF", "#DDDDDD", "#000000", "#333333"])
        self.color_combo.setCurrentText(self.settings.get("text_color", "#FFFFFF"))
        layout.addWidget(self.color_combo)
        
        layout.addWidget(QLabel("Tema Sfondo:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Green"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Dark"))
        layout.addWidget(self.theme_combo)
        
        layout.addSpacing(10)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)

    def save_and_close(self):
        self.settings["font_family"] = self.font_combo.currentText()
        self.settings["font_size"] = self.size_spin.value()
        self.settings["text_color"] = self.color_combo.currentText()
        self.settings["theme"] = self.theme_combo.currentText()
        save_settings(self.settings)
        self.accept()


class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(35)
        self.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.icon_label = QLabel()
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.icon_label.setPixmap(QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_label)
        
        self.title_label = QLabel("Aura AI Assistant")
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("titleBtn")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.clicked.connect(self.main_window.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("X")
        self.close_btn.setObjectName("titleBtnClose")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.main_window.close)
        layout.addWidget(self.close_btn)
        
        self.startPos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint() - self.main_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.startPos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.main_window.move(event.globalPosition().toPoint() - self.startPos)


class AuraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_manager = ApiManager()
        self.last_images = {1: None, 2: None}
        self.current_hwnd_1 = None
        self.current_hwnd_2 = None
        self.is_dual_mode = False
        
        self.init_ui()
        self.apply_settings()
        self.init_threads()
        self.setup_hotkey()
        self.load_history_on_startup()
        
        # Inizializza variabili per il ridimensionamento
        self.resizing_edge = None
        self.start_geometry = None
        self.start_pos = None
        self.setMouseTracking(True)
        
    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        screen = self.screen().availableGeometry()
        width, height = 550, 750
        self.setGeometry(screen.width() - width - 20, 20, width, height)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10) # Margins per Resize
        main_layout.setSpacing(0)
        
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        
        self.frame_layout = QVBoxLayout(self.main_frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 10)
        
        self.title_bar = CustomTitleBar(self)
        self.frame_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 0, 15, 0)
        
        # AI Engine & Dual Mode
        top_controls_layout = QHBoxLayout()
        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            "Gemini 3 Flash Preview",
            "Gemini 2.5 Flash", 
            "Gemini 2.5 Pro", 
            "Gemini 1.5 Pro"
        ])
        top_controls_layout.addWidget(QLabel("Motore:"))
        top_controls_layout.addWidget(self.engine_combo)
        top_controls_layout.addStretch()
        
        self.dual_mode_switch = QCheckBox("Modalità Doppia Finestra")
        self.dual_mode_switch.stateChanged.connect(self.toggle_dual_mode)
        top_controls_layout.addWidget(self.dual_mode_switch)
        content_layout.addLayout(top_controls_layout)
        
        # Action Buttons Layout (Horizontal center)
        action_layout = QHBoxLayout()
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.setSpacing(15)
        
        self.settings_btn = QPushButton("⚙ Impostazioni")
        self.settings_btn.setObjectName("actionBtn")
        self.settings_btn.clicked.connect(self.open_settings)
        
        refresh_btn = QPushButton("🔃 Aggiorna finestre")
        refresh_btn.setFixedWidth(180)
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self.refresh_windows_list)
        
        self.history_btn = QPushButton("💬 Cronologia")
        self.history_btn.setObjectName("actionBtn")
        self.history_btn.clicked.connect(self.toggle_history)
        
        action_layout.addWidget(self.settings_btn)
        action_layout.addWidget(refresh_btn)
        action_layout.addWidget(self.history_btn)
        
        content_layout.addSpacing(10)
        content_layout.addLayout(action_layout)
        content_layout.addSpacing(10)
        
        self.windows_layout = QHBoxLayout()
        
        col1 = QVBoxLayout()
        self.window_selector_1 = QComboBox()
        self.window_selector_1.currentIndexChanged.connect(lambda idx: self.on_window_selected(idx, 1))
        self.thumbnail_1 = QLabel("Nessuna cattura")
        self.thumbnail_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_1.setMinimumHeight(100)
        self.thumbnail_1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.thumbnail_1.setStyleSheet("background-color: #000000; border-radius: 5px;")
        col1.addWidget(QLabel("Finestra 1:"))
        col1.addWidget(self.window_selector_1)
        col1.addWidget(self.thumbnail_1)
        self.windows_layout.addLayout(col1)
        
        self.col2_widget = QWidget()
        col2 = QVBoxLayout(self.col2_widget)
        col2.setContentsMargins(0,0,0,0)
        self.window_selector_2 = QComboBox()
        self.window_selector_2.currentIndexChanged.connect(lambda idx: self.on_window_selected(idx, 2))
        self.thumbnail_2 = QLabel("Nessuna cattura")
        self.thumbnail_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_2.setMinimumHeight(100)
        self.thumbnail_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.thumbnail_2.setStyleSheet("background-color: #000000; border-radius: 5px;")
        col2.addWidget(QLabel("Finestra 2:"))
        col2.addWidget(self.window_selector_2)
        col2.addWidget(self.thumbnail_2)
        self.windows_layout.addWidget(self.col2_widget)
        self.col2_widget.hide()
        
        content_layout.addLayout(self.windows_layout)
        
        # Opacity
        opacity_controls = QVBoxLayout()
        preset_layout = QHBoxLayout()
        for val in [25, 50, 75, 100]:
            btn = QPushButton(f"{val}%")
            btn.clicked.connect(lambda checked, v=val: self.opacity_slider.setValue(v))
            preset_layout.addWidget(btn)
            
        opacity_controls.addLayout(preset_layout)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Opacità:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(90)
        self.setWindowOpacity(0.9)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v / 100.0))
        slider_layout.addWidget(self.opacity_slider)
        opacity_controls.addLayout(slider_layout)
        content_layout.addLayout(opacity_controls)
        
        # Chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        content_layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Chiedi qualcosa sul contesto visivo...")
        self.chat_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Invia")
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        content_layout.addLayout(input_layout)
        
        self.frame_layout.addLayout(content_layout)
        
        # History Sidebar
        self.history_sidebar = QFrame()
        self.history_sidebar.setObjectName("historySidebar")
        self.history_sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.history_sidebar)
        sidebar_layout.addWidget(QLabel("<b>Cronologia</b>"))
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderHidden(True)
        self.history_tree.itemClicked.connect(self.on_history_item_clicked)
        sidebar_layout.addWidget(self.history_tree)
        self.history_sidebar.hide()
        
        main_layout.addWidget(self.main_frame)
        main_layout.addWidget(self.history_sidebar)

        self.refresh_windows_list()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            margin = 10
            w, h = self.width(), self.height()
            
            edge = ""
            if pos.y() < margin: edge += "top"
            elif pos.y() > h - margin: edge += "bottom"
            
            if pos.x() < margin: edge += "left"
            elif pos.x() > w - margin: edge += "right"
            
            if edge:
                self.resizing_edge = edge
                self.start_pos = event.globalPosition().toPoint()
                self.start_geometry = self.geometry()
            else:
                self.resizing_edge = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing_edge = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        margin = 10
        w, h = self.width(), self.height()
        
        # Change cursor on hover
        edge = ""
        if pos.y() < margin: edge += "top"
        elif pos.y() > h - margin: edge += "bottom"
        
        if pos.x() < margin: edge += "left"
        elif pos.x() > w - margin: edge += "right"
        
        if edge in ["topleft", "bottomright"]:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ["topright", "bottomleft"]:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge in ["left", "right"]:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in ["top", "bottom"]:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        # Perform resizing
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'resizing_edge') and self.resizing_edge:
            delta = event.globalPosition().toPoint() - self.start_pos
            rect = self.start_geometry
            
            new_x, new_y, new_w, new_h = rect.x(), rect.y(), rect.width(), rect.height()
            min_w, min_h = 400, 500 # Minimum size
            
            if "left" in self.resizing_edge:
                new_w = max(min_w, rect.width() - delta.x())
                if new_w > min_w: new_x = rect.x() + delta.x()
            elif "right" in self.resizing_edge:
                new_w = max(min_w, rect.width() + delta.x())
                
            if "top" in self.resizing_edge:
                new_h = max(min_h, rect.height() - delta.y())
                if new_h > min_h: new_y = rect.y() + delta.y()
            elif "bottom" in self.resizing_edge:
                new_h = max(min_h, rect.height() + delta.y())
                
            self.setGeometry(new_x, new_y, new_w, new_h)
            
        super().mouseMoveEvent(event)

    def apply_settings(self):
        settings = load_settings()
        font_family = settings.get("font_family", "Segoe UI")
        font_size = settings.get("font_size", 13)
        text_color = settings.get("text_color", "#FFFFFF")
        theme = settings.get("theme", "Dark")
        
        bg_color = "#1E1E1E"
        second_bg = "#2D2D30"
        btn_bg = "#0E639C"
        btn_hover = "#1177BB"
        
        if theme == "Light":
            bg_color = "#F0F0F0"
            second_bg = "#FFFFFF"
            btn_bg = "#0078D7"
            btn_hover = "#005A9E"
            text_color = "#000000" if settings.get("text_color") == "#FFFFFF" else text_color
        elif theme == "Green":
            bg_color = "#1A2E1A"
            second_bg = "#264026"
            btn_bg = "#2E8B57"
            btn_hover = "#3CB371"
            
        css = f"""
            #mainFrame, #historySidebar {{
                background-color: {bg_color};
                border-radius: 15px;
                border: 1px solid {second_bg};
            }}
            QWidget {{ 
                color: {text_color}; 
                font-family: '{font_family}'; 
                font-size: {font_size}px;
            }}
            QComboBox, QLineEdit, QTreeWidget {{
                background-color: {second_bg};
                color: {text_color};
                border: 1px solid #3E3E42;
                border-radius: 5px;
                padding: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {second_bg};
                color: {text_color};
                selection-background-color: {btn_bg};
            }}
            QTextEdit {{
                background-color: {second_bg};
                color: {text_color};
                border: 1px solid #3E3E42;
                border-radius: 5px;
                padding: 10px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
            #actionBtn {{
                background-color: {second_bg};
                color: {text_color};
                border: 1px solid {btn_bg};
                padding: 8px;
                font-size: 13px;
            }}
            #actionBtn:hover {{ background-color: {btn_bg}; color: white; }}
            #titleBtn, #titleBtnClose {{
                background-color: transparent;
                color: {text_color};
                padding: 0px;
                font-size: 14px;
                border-radius: 15px;
            }}
            #titleBtn:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
            #titleBtnClose:hover {{ background-color: #FF5252; color: white; }}
        """
        self.setStyleSheet(css)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.apply_settings()

    def toggle_history(self):
        if self.history_sidebar.isHidden():
            self.history_sidebar.show()
            self.setFixedSize(self.width() + 250, self.height())
        else:
            self.history_sidebar.hide()
            self.setFixedSize(self.width() - 250, self.height())

    def toggle_dual_mode(self, state):
        self.is_dual_mode = (state == 2)
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

    def append_chat_html(self, html_content):
        self.chat_display.append(f"<div style='margin-bottom: 10px;'>{html_content}</div>")
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def send_message(self):
        prompt = self.chat_input.text().strip()
        if not prompt:
            return
            
        self.chat_input.clear()
        self.append_chat_html(f"<b>Tu:</b> {prompt}")
        
        titles = []
        images = []
        
        if self.current_hwnd_1 and self.last_images[1]:
            titles.append(self.window_selector_1.currentText())
            images.append(self.last_images[1])
            
        if self.is_dual_mode and self.current_hwnd_2 and self.last_images[2]:
            titles.append(self.window_selector_2.currentText())
            images.append(self.last_images[2])
            
        if not titles:
            self.append_chat_html("<b style='color: #FF5252;'>Aura:</b> Seleziona almeno una finestra attiva prima di inviare un messaggio!")
            return
            
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        self.append_chat_html("<i id='loader' style='color: #888;'>Aura sta pensando...</i>")
        
        self.current_prompt = prompt
        
        model_map = {
            "Gemini 3 Flash Preview": "gemini-3-flash-preview",
            "Gemini 2.5 Flash": "gemini-2.5-flash",
            "Gemini 2.5 Pro": "gemini-2.5-pro",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        selected_model = model_map.get(self.engine_combo.currentText(), "gemini-2.5-flash")
        
        self.api_worker = ApiWorker(self.api_manager, titles, prompt, images, selected_model)
        self.api_worker.result_ready.connect(self.on_api_response)
        self.api_worker.start()
        
    def on_api_response(self, response):
        current_html = self.chat_display.toHtml()
        if "Aura sta pensando..." in current_html:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()
            
        html_response = markdown.markdown(response)
        self.append_chat_html(f"<b style='color: #4CAF50;'>Aura:</b><br>{html_response}")
        
        win_title = self.window_selector_1.currentText()
        if self.is_dual_mode:
            win_title += f" & {self.window_selector_2.currentText()}"
            
        add_to_history(win_title, self.current_prompt, html_response)
        self.reload_history_tree()
        
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.chat_input.setFocus()

    def reload_history_tree(self):
        self.history_tree.clear()
        data = load_history()
        
        dates = data.get("Dates", {})
        # Sort dates (assuming DD/MM/YYYY)
        for date_str, windows in dates.items():
            date_item = QTreeWidgetItem(self.history_tree, [date_str])
            date_item.setExpanded(True)
            for win_title, conversations in windows.items():
                win_item = QTreeWidgetItem(date_item, [win_title[:30] + "..."])
                win_item.setExpanded(True)
                for conv in conversations:
                    prompt_preview = conv.get("time", "") + " - " + conv["prompt"][:25] + "..."
                    child_item = QTreeWidgetItem(win_item, [prompt_preview])
                    child_item.setData(0, Qt.ItemDataRole.UserRole, conv)

    def load_history_on_startup(self):
        self.reload_history_tree()
        data = load_history()
        last = data.get("LastSession", {})
        if last.get("chat_html"):
            self.chat_display.clear()
            self.append_chat_html(last["chat_html"])
        else:
            self.append_chat_html("<b>Aura:</b> Ciao! Seleziona una finestra e fammi una domanda.")

    def on_history_item_clicked(self, item, column):
        conv = item.data(0, Qt.ItemDataRole.UserRole)
        if conv:
            self.chat_display.clear()
            self.append_chat_html(f"<b>Tu:</b> {conv['prompt']}")
            self.append_chat_html(f"<b style='color: #4CAF50;'>Aura:</b><br>{conv['response']}")

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
