from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox)
from db_utils import get_db
from user_manager import verify_user
from config import UserType
from parent_player_window import ParentPlayerWindow
from child_player_window import ChildPlayerWindow


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音乐播放系统 - 登录")
        self.setFixedSize(400, 300)
        self.db = next(get_db())  # 获取数据库会话
        self.init_ui()

    def init_ui(self):
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("音乐播放系统")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名：")
        username_label.setStyleSheet("font-size: 16px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setFixedSize(250, 35)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密  码：")
        password_label.setStyleSheet("font-size: 16px;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setFixedSize(250, 35)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # 登录按钮
        login_btn = QPushButton("登录")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def handle_login(self):
        """处理登录逻辑"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "警告", "用户名和密码不能为空！")
            return

        # 验证用户
        user, msg = verify_user(self.db, username, password)
        if not user:
            QMessageBox.critical(self, "错误", msg)
            return

        # 根据用户类型打开对应窗口
        QMessageBox.information(self, "成功", msg)
        self.close()  # 关闭登录窗口

        if user.user_type == UserType.PARENT:
            self.parent_window = ParentPlayerWindow(user.id, self.db)
            self.parent_window.show()
        else:
            # 孩子用户：确保parent_id存在
            if not user.parent_id:
                QMessageBox.critical(self, "错误", "该孩子用户未关联家长，无法登录！")
                return
            self.child_window = ChildPlayerWindow(child_id=user.id, db=self.db, parent_id=user.parent_id)
            self.child_window.show()


# 测试登录窗口
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())