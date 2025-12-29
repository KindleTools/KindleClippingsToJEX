import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """
    Main entry point for the GUI application.
    Initializes the QApplication and the main window.
    """
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
