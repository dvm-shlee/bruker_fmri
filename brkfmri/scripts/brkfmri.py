from PySide2 import QtWidgets
from ..gui.main_win import MainWindow
import sys

def main():
    app = QtWidgets.QApplication(sys.argv)
    exe = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()