import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

def main():
    """
    Main entry point for the GUI application.
    Initializes the QApplication and the main window.
    """
    # Taskbar Icon Fix for Windows
    import ctypes
    import platform
    if platform.system() == 'Windows':
        myappid = 'personal.kindletools.clippingstojex.1.0' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    
    # Optional: Configure global font settings here
    # font = app.font()
    # font.setPointSize(10)
    # app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
