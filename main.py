import sys
import os
from PyQt6.QtWidgets import QApplication
from modules.interfaccia import AuraMainWindow

def main():
    try:
        import ctypes
        myappid = 'aura.ai.assistant.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    app = QApplication(sys.argv)
    
    if not os.path.exists(".env") and not os.getenv("GEMINI_API_KEY"):
        with open(".env", "w") as f:
            f.write("GEMINI_API_KEY=\n")
    
    window = AuraMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
