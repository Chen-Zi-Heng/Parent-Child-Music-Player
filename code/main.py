"""音乐播放系统主程序"""
import sys
from PySide6.QtWidgets import QApplication  # 正确导入 QApplication
from PySide6 import QtCore  # 正确导入 QtCore 模块（整个模块导入）
from PySide6 import QtGui
from db_utils import init_db, get_db
from login_window import LoginWindow

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

def main():
    # 初始化数据库（首次运行自动创建表）
    init_db()

    # 启动应用
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('logo.ico'))
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()