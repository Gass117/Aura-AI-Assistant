import time
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32ui
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

dwmapi = ctypes.windll.dwmapi

def get_active_windows():
    """
    Restituisce una lista di dizionari contenenti titolo e handle (HWND)
    delle finestre visibili, filtrando le app in background di Windows.
    """
    windows = []
    
    def enum_windows_callback(hwnd, lParam):
        if not win32gui.IsWindowVisible(hwnd):
            return True
            
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
            
        ignore_exact = [
            "Program Manager", 
            "Settings", 
            "Microsoft Text Input Application", 
            "Monitor stato P3000 PCL"
        ]
        if title in ignore_exact:
            return True
            
        # Filtra Aura AI Assistant, ma mantieni le finestre di Esplora Risorse (CabinetWClass)
        cls_name = win32gui.GetClassName(hwnd)
        if "Aura AI Assistant" in title and cls_name != "CabinetWClass":
            return True
            
        # Controlla se la finestra è "cloaked" (nascosta da Windows 10/11)
        DWMWA_CLOAKED = 14
        cloaked = wintypes.DWORD()
        try:
            res = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
            if res == 0 and cloaked.value != 0:
                return True
        except:
            pass

        # Escludi le Tool Window
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return True

        windows.append({"title": title, "hwnd": hwnd})
        return True
    
    win32gui.EnumWindows(enum_windows_callback, None)
    unique_windows = {w['hwnd']: w for w in windows}.values()
    return sorted(unique_windows, key=lambda x: x['title'])


class WindowCaptureThread(QThread):
    # Emette un dizionario: {hwnd: PIL.Image}
    frames_captured = pyqtSignal(dict)
    
    def __init__(self, hwnds=None, interval=2.0):
        super().__init__()
        self.hwnds = hwnds if hwnds else []
        self.interval = interval
        self._is_running = True
        
    def set_windows(self, hwnds):
        self.hwnds = hwnds

    def set_interval(self, interval):
        self.interval = interval
        
    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()

    def capture_window(self, hwnd):
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
                
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # PW_RENDERFULLCONTENT = 2. Serve per catturare in background in Win 10/11
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            
            img = None
            if result == 1:
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
            
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return img
        except Exception as e:
            # Errore silenzioso per evitare spam se la finestra viene chiusa in quel momento
            pass
        return None

    def run(self):
        while self._is_running:
            if self.hwnds:
                results = {}
                for hwnd in self.hwnds:
                    if hwnd:
                        img = self.capture_window(hwnd)
                        if img:
                            results[hwnd] = img
                if results:
                    self.frames_captured.emit(results)
            time.sleep(self.interval)
