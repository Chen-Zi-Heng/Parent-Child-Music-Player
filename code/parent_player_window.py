from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QSlider,
    QLineEdit,
    QMenu,
    QGridLayout,
    QComboBox,
    QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont
import matplotlib

# 设置matplotlib使用Qt后端
from log_manager import get_child_daily_stats

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

from music_manager import (
    add_music,
    get_parent_musics,
    update_music,
    delete_music,
    get_music_by_id,
)
from play_history_manager import add_parent_recent_play, get_parent_recent_plays
from favorite_manager import (
    add_parent_favorite,
    remove_parent_favorite,
    get_parent_favorites,
)
from user_manager import create_user  # 新增导入
from config import UserType  # 新增导入
import os
import pygame
import random

# 音频格式支持列表（可扩展）
SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".ape", ".wma")


# 播放模式枚举
class PlayMode:
    ORDER = 0  # 顺序播放
    SINGLE_LOOP = 1  # 单曲循环
    RANDOM = 2  # 随机播放


# 新增：折线图组件类
class PlayDurationChart(FigureCanvas):
    """孩子播放时长统计折线图"""

    def __init__(self, parent=None, width=10, height=6, dpi=100):
        # 创建图形和坐标轴
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)

        # 初始化样式
        self.fig.patch.set_facecolor('white')  # 设置背景色为白色（匹配Qt界面）
        self.ax.set_facecolor('#f8f9fa')  # 坐标轴背景色

        # 设置字体（解决中文显示问题）
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    def update_chart(self, data, child_name):
        """更新折线图数据
        data格式：[{date: 日期对象, total_duration: 时长（秒）}, ...]
        """
        # 清空图表
        self.ax.clear()

        if not data:
            # 无数据时显示提示
            self.ax.text(0.5, 0.5, '暂无播放数据', ha='center', va='center',
                         transform=self.ax.transAxes, fontsize=14)
            self.ax.set_xlabel('日期', fontsize=12)
            self.ax.set_ylabel('播放时长（分钟）', fontsize=12)
            self.ax.set_title(f'{child_name} 听歌时长统计', fontsize=14, fontweight='bold')
            self.draw()
            return

        # 处理数据
        dates = [item['date'] for item in data]
        durations_sec = [item['total_duration'] for item in data]
        durations_min = [d / 60 for d in durations_sec]  # 转换为分钟

        # 绘制折线图
        line = self.ax.plot(dates, durations_min,
                            marker='o', linewidth=2.5, markersize=6,
                            color='#2E86AB', markerfacecolor='#A23B72',
                            markeredgecolor='white', markeredgewidth=1.5)

        # 填充折线下方区域（增加视觉效果）
        self.ax.fill_between(dates, durations_min, alpha=0.3, color='#2E86AB')

        # 设置X轴（日期格式）
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # 每天显示一个刻度
        self.fig.autofmt_xdate()  # 旋转日期标签

        # 设置Y轴（确保从0开始）
        self.ax.set_ylim(bottom=0)
        max_duration = max(durations_min) if durations_min else 10
        self.ax.set_ylim(top=max_duration * 1.1 if max_duration > 0 else 10)

        # 添加数值标签（只显示大于0的数值）
        for i, (x, y) in enumerate(zip(dates, durations_min)):
            if y > 0:
                self.ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points",
                                 xytext=(0, 10), ha='center', fontsize=9,
                                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

        # 设置标题和标签
        self.ax.set_xlabel('日期', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('播放时长（分钟）', fontsize=12, fontweight='bold')
        self.ax.set_title(f'{child_name} 听歌时长统计', fontsize=14, fontweight='bold', pad=20)

        # 设置网格
        self.ax.grid(True, alpha=0.3, linestyle='--')

        # 设置边框
        for spine in self.ax.spines.values():
            spine.set_linewidth(1.2)
            spine.set_color('#cccccc')

        # 刷新图表
        self.draw()


# 新增：统计标签页组件
class ChildStatsWidget(QWidget):
    """孩子播放统计标签页"""

    def __init__(self, parent_id, db, parent=None):
        super().__init__(parent)
        self.parent_id = parent_id
        self.db = db

        # 获取所有孩子
        self.children = self._get_children()

        self.init_ui()
        self.load_stats_data()

    def _get_children(self):
        """获取家长的所有孩子 - 修正：使用大写 CHILD"""
        from models import User
        return self.db.query(User).filter(
            User.parent_id == self.parent_id,
            User.user_type == "CHILD"  # 关键修正：枚举值为大写
        ).all()

    def init_ui(self):
        """初始化统计页面布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("孩子听歌时长统计")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 筛选条件区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(20)

        # 孩子选择下拉框
        child_label = QLabel("选择孩子：")
        child_label.setFont(QFont("Arial", 11))
        filter_layout.addWidget(child_label)

        self.child_combo = QComboBox()
        self.child_combo.setFont(QFont("Arial", 11))
        self.child_combo.addItem("所有孩子", None)
        for child in self.children:
            self.child_combo.addItem(child.username, child.id)
        filter_layout.addWidget(self.child_combo)

        # 时间范围选择
        days_label = QLabel("时间范围：")
        days_label.setFont(QFont("Arial", 11))
        filter_layout.addWidget(days_label)

        self.days_spin = QSpinBox()
        self.days_spin.setFont(QFont("Arial", 11))
        self.days_spin.setRange(7, 90)  # 支持7-90天
        self.days_spin.setValue(30)
        self.days_spin.setSuffix(" 天")
        filter_layout.addWidget(self.days_spin)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新数据")
        self.refresh_btn.setFont(QFont("Arial", 11))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_stats_data)
        filter_layout.addWidget(self.refresh_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # 统计信息卡片区域
        stats_card_layout = QHBoxLayout()
        stats_card_layout.setSpacing(15)

        # 总播放时长卡片
        self.total_duration_card = self._create_stats_card("总播放时长", "0 分钟")
        stats_card_layout.addWidget(self.total_duration_card)

        # 平均每日时长卡片
        self.avg_duration_card = self._create_stats_card("平均每日时长", "0 分钟")
        stats_card_layout.addWidget(self.avg_duration_card)

        # 总播放次数卡片
        self.total_plays_card = self._create_stats_card("总播放次数", "0 次")
        stats_card_layout.addWidget(self.total_plays_card)

        # 播放歌曲数卡片
        self.total_songs_card = self._create_stats_card("播放歌曲数", "0 首")
        stats_card_layout.addWidget(self.total_songs_card)

        main_layout.addLayout(stats_card_layout)

        # 折线图区域
        self.chart = PlayDurationChart(self)
        main_layout.addWidget(self.chart, stretch=1)

    def _create_stats_card(self, title, value):
        """创建统计信息卡片"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 15px;
            }
        """)
        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet("color: #666666;")
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet("color: #2E86AB;")
        card_layout.addWidget(value_label)

        card_layout.addStretch()
        return card

    def _update_stats_cards(self, total_duration_sec, days, total_plays, total_songs):
        """更新统计卡片数据"""
        total_duration_min = total_duration_sec / 60
        avg_duration_min = total_duration_min / days if days > 0 else 0

        # 更新卡片内容
        self.total_duration_card.findChildren(QLabel)[1].setText(f"{total_duration_min:.1f} 分钟")
        self.avg_duration_card.findChildren(QLabel)[1].setText(f"{avg_duration_min:.1f} 分钟")
        self.total_plays_card.findChildren(QLabel)[1].setText(f"{total_plays} 次")
        self.total_songs_card.findChildren(QLabel)[1].setText(f"{total_songs} 首")

    def load_stats_data(self):
        """加载统计数据并更新图表"""
        selected_child_id = self.child_combo.currentData()
        days = self.days_spin.value()

        # 获取统计数据
        all_stats = get_child_daily_stats(self.db, self.parent_id, days)

        # 筛选选中的孩子数据
        if selected_child_id:
            child_stats = [stat for stat in all_stats if stat['child_id'] == selected_child_id]
            child_name = self.child_combo.currentText()
        else:
            # 所有孩子：按日期合并数据
            child_stats = self._merge_all_children_stats(all_stats)
            child_name = "所有孩子"

        # 计算汇总统计
        total_duration_sec = sum(stat['total_duration'] for stat in child_stats)
        total_plays = sum(stat['play_count'] for stat in child_stats)
        total_songs = len(set(stat['songs_count'] for stat in child_stats))  # 去重统计

        # 更新统计卡片
        self._update_stats_cards(total_duration_sec, days, total_plays, total_songs)

        # 准备图表数据（按日期排序）
        chart_data = sorted(child_stats, key=lambda x: x['date'])

        # 更新折线图
        self.chart.update_chart(chart_data, child_name)

    def _merge_all_children_stats(self, all_stats):
        """合并所有孩子的统计数据（按日期汇总）"""
        date_stats = {}

        for stat in all_stats:
            date_str = stat['date'].isoformat()

            if date_str not in date_stats:
                date_stats[date_str] = {
                    'date': stat['date'],
                    'total_duration': 0,
                    'play_count': 0,
                    'songs_count': 0
                }

            # 汇总数据
            date_stats[date_str]['total_duration'] += stat['total_duration']
            date_stats[date_str]['play_count'] += stat['play_count']
            date_stats[date_str]['songs_count'] += stat['songs_count']

        return list(date_stats.values())


class ChildRegisterDialog(QDialog):
    """孩子注册对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册孩子账户")
        self.setFixedSize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # 表单布局
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(10)

        # 用户名
        username_label = QLabel("用户名：")
        username_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(
            username_label, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入孩子用户名")
        self.username_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                min-height: 35px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        form_layout.addWidget(self.username_input, 0, 1)

        # 密码
        password_label = QLabel("密码：")
        password_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(
            password_label, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                min-height: 35px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        form_layout.addWidget(self.password_input, 1, 1)

        # 确认密码
        confirm_label = QLabel("确认密码：")
        confirm_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(
            confirm_label, 2, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                min-height: 35px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        form_layout.addWidget(self.confirm_input, 2, 1)

        layout.addLayout(form_layout)
        layout.addStretch()

        # 按钮区域
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(
            """
            QDialogButtonBox QPushButton {
                font-size: 14px;
                min-width: 85px;
                min-height: 35px;
            }
        """
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def validate_and_accept(self):
        """验证输入并接受对话框"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_input.text()

        if not username:
            QMessageBox.warning(self, "输入错误", "用户名不能为空！")
            return

        if not password:
            QMessageBox.warning(self, "输入错误", "密码不能为空！")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "输入错误", "两次输入的密码不一致！")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "输入错误", "密码长度至少为6位！")
            return

        self.accept()

    def get_data(self):
        """获取输入的数据"""
        return {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
        }


class MusicInfoDialog(QDialog):
    """音乐信息编辑对话框（添加/编辑音乐时使用）"""

    def __init__(self, parent=None, music=None):
        super().__init__(parent)
        self.setWindowTitle("编辑音乐信息" if music else "添加音乐信息")
        self.setFixedSize(400, 300)  # 增加高度以提供更多空间
        self.music = music  # 编辑时传入音乐对象，添加时为None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)  # 统一边距
        layout.setSpacing(20)  # 增加整体间距

        # 表单布局 - 使用网格布局来更好地控制标签和输入框的对齐
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)  # 增加垂直间距
        form_layout.setHorizontalSpacing(10)  # 水平间距

        # 歌曲标题
        title_label = QLabel("歌曲标题：")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(
            title_label, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入歌曲标题")
        self.title_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                min-height: 35px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        if self.music:
            self.title_input.setText(self.music.title)
        form_layout.addWidget(self.title_input, 0, 1)

        # 情绪类型
        emotion_label = QLabel("情绪类型：")
        emotion_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(
            emotion_label, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.emotion_input = QLineEdit()
        self.emotion_input.setPlaceholderText("请输入情绪类型")
        self.emotion_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                min-height: 35px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        if self.music:
            self.emotion_input.setText(self.music.emotion)
        else:
            self.emotion_input.setText("未知情绪类型")
        form_layout.addWidget(self.emotion_input, 1, 1)

        # 将表单布局添加到主布局
        layout.addLayout(form_layout)

        # 共享选项（仅编辑时显示）
        if self.music:
            # 在共享选项前添加一些间距
            layout.addSpacing(10)
            self.share_checkbox = QCheckBox("共享给孩子")
            self.share_checkbox.setStyleSheet(
                """
                QCheckBox {
                    font-size: 14px;
                    font-weight: bold;
                    spacing: 8px;
                }
            """
            )
            self.share_checkbox.setChecked(self.music.is_shared)
            layout.addWidget(self.share_checkbox)

        # 弹性空间，让按钮贴底
        layout.addStretch()

        # 按钮区域
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(
            """
            QDialogButtonBox QPushButton {
                font-size: 14px;
                min-width: 85px;
                min-height: 35px;
            }
        """
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        """获取输入的音乐信息"""
        data = {
            "title": self.title_input.text().strip(),
            "emotion": self.emotion_input.text().strip() or "未知情绪类型",
        }
        if self.music:
            data["is_shared"] = self.share_checkbox.isChecked()
        return data


class ParentPlayerWindow(QMainWindow):
    def __init__(self, parent_id: int, db):
        super().__init__()
        self.parent_id = parent_id
        self.db = db
        self.current_music = None
        self.current_music_index = -1
        self.play_start_time = None
        self.pause_position = 0
        self.is_playing = False
        self.play_mode = PlayMode.ORDER
        self.original_playlist = []
        self.shuffled_indices = []

        # 拖动进度条相关
        self.is_dragging_progress = False
        self.was_playing_before_drag = False

        pygame.mixer.init(frequency=44100, channels=2, buffer=1024)
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

        self.setWindowTitle("家长音乐播放器")
        self.setFixedSize(900, 750)  # 增加窗口高度以适应统计页面
        self.init_ui()
        self.load_musics()
        self.load_recent_plays()
        self.load_favorites()

        # 定时器：用于更新进度条
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(200)

    def init_ui(self):
        """初始化界面布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 上半部分：左侧控制区 + 右侧列表区
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        # 左侧：功能按钮区
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 添加注册孩子按钮
        self.register_child_btn = QPushButton("👶 注册孩子")
        self.register_child_btn.setFixedSize(120, 40)
        self.register_child_btn.setStyleSheet("font-size: 14px;")
        self.register_child_btn.clicked.connect(self.register_child)
        left_layout.addWidget(self.register_child_btn)

        # 所有左侧按钮...
        self.add_music_btn = QPushButton("📁 添加音乐")
        self.add_music_btn.setFixedSize(120, 40)
        self.add_music_btn.setStyleSheet("font-size: 14px;")
        self.add_music_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.add_music_btn.customContextMenuRequested.connect(self.show_add_music_menu)
        self.add_music_btn.clicked.connect(self.show_add_music_menu_direct)
        left_layout.addWidget(self.add_music_btn)

        self.edit_btn = QPushButton("✏️ 编辑信息")
        self.edit_btn.setFixedSize(120, 40)
        self.edit_btn.setStyleSheet("font-size: 14px;")
        self.edit_btn.clicked.connect(self.edit_music)
        self.edit_btn.setEnabled(False)
        left_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ 删除音乐")
        self.delete_btn.setFixedSize(120, 40)
        self.delete_btn.setStyleSheet("font-size: 14px;")
        self.delete_btn.clicked.connect(self.delete_selected_music)
        self.delete_btn.setEnabled(False)
        left_layout.addWidget(self.delete_btn)

        self.favorite_btn = QPushButton("❤️ 添加到喜欢")
        self.favorite_btn.setFixedSize(120, 40)
        self.favorite_btn.setStyleSheet("font-size: 14px;")
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.favorite_btn.setEnabled(False)
        left_layout.addWidget(self.favorite_btn)

        volume_label = QLabel("音量：")
        volume_label.setStyleSheet("font-size: 14px;")
        left_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedSize(120, 20)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(60)
        self.volume_slider.valueChanged.connect(self.set_volume)
        left_layout.addWidget(self.volume_slider)

        search_label = QLabel("搜索：")
        search_label.setStyleSheet("font-size: 14px;")
        left_layout.addWidget(search_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入歌曲标题或情绪类型")
        self.search_input.textChanged.connect(self.search_music)
        search_layout.addWidget(self.search_input)

        self.clear_search_btn = QPushButton("清除")
        self.clear_search_btn.setFixedSize(50, 25)
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_search_btn)

        left_layout.addLayout(search_layout)

        # 退出登录按钮
        self.logout_btn = QPushButton("🚪 退出登录")
        self.logout_btn.setFixedSize(120, 40)
        self.logout_btn.setStyleSheet("font-size: 14px;")
        self.logout_btn.clicked.connect(self.handle_logout)
        left_layout.addWidget(self.logout_btn)

        left_layout.addStretch()

        # 右侧：音乐列表区 + 统计标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("font-size: 14px;")

        self.music_list_widget = QListWidget()
        self.music_list_widget.itemClicked.connect(self.on_music_selected)
        self.music_list_widget.itemDoubleClicked.connect(self.play_music)
        self.music_list_widget.setStyleSheet(
            """
            QListWidget { font-size: 13px; }
            QListWidget::item:selected { background-color: #4CAF50; color: white; }
        """
        )
        tab_widget.addTab(self.music_list_widget, "全部音乐")

        self.recent_play_widget = QListWidget()
        self.recent_play_widget.itemDoubleClicked.connect(self.play_recent_music)
        self.recent_play_widget.setStyleSheet("QListWidget { font-size: 13px; }")
        tab_widget.addTab(self.recent_play_widget, "最近播放")

        self.favorite_widget = QListWidget()
        self.favorite_widget.itemDoubleClicked.connect(self.play_favorite_music)
        self.favorite_widget.setStyleSheet("QListWidget { font-size: 13px; }")
        tab_widget.addTab(self.favorite_widget, "喜欢的歌曲")

        # 新增：统计标签页
        self.stats_widget = ChildStatsWidget(self.parent_id, self.db)
        tab_widget.addTab(self.stats_widget, "孩子听歌统计")

        top_layout.addLayout(left_layout)
        top_layout.addWidget(tab_widget, stretch=1)
        main_layout.addLayout(top_layout)

        # 下半部分：播放控制区
        control_layout = QVBoxLayout()
        control_layout.setSpacing(10)

        # 播放信息标签 + 进度条
        progress_layout = QVBoxLayout()

        self.current_play_label = QLabel("未播放音乐")
        self.current_play_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.current_play_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.current_play_label)

        # 进度条布局（修复重点）
        progress_bar_layout = QHBoxLayout()
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        # 连接拖动信号（修复重点）
        self.progress_bar.sliderPressed.connect(self.on_progress_drag_start)
        self.progress_bar.sliderReleased.connect(self.on_progress_drag_end)
        progress_bar_layout.addWidget(self.progress_bar)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 13px;")
        self.time_label.setFixedWidth(90)
        progress_bar_layout.addWidget(self.time_label)

        progress_layout.addLayout(progress_bar_layout)
        control_layout.addLayout(progress_layout)

        # 控制按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(20, 10, 20, 10)

        self.prev_btn = QPushButton("⏮️ 上一首")
        self.prev_btn.setFixedSize(90, 40)
        self.prev_btn.setStyleSheet("font-size: 14px;")
        self.prev_btn.clicked.connect(self.play_previous)
        button_layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.setFixedSize(80, 40)
        self.play_btn.setStyleSheet("font-size: 14px;")
        self.play_btn.clicked.connect(self.toggle_play)
        button_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setFixedSize(80, 40)
        self.pause_btn.setStyleSheet("font-size: 14px;")
        self.pause_btn.clicked.connect(self.pause_play)
        button_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setFixedSize(80, 40)
        self.stop_btn.setStyleSheet("font-size: 14px;")
        self.stop_btn.clicked.connect(self.stop_play)
        button_layout.addWidget(self.stop_btn)

        self.next_btn = QPushButton("⏭️ 下一首")
        self.next_btn.setFixedSize(90, 40)
        self.next_btn.setStyleSheet("font-size: 14px;")
        self.next_btn.clicked.connect(self.play_next)
        button_layout.addWidget(self.next_btn)

        self.mode_btn = QPushButton("🔁 顺序播放")
        self.mode_btn.setFixedSize(120, 40)
        self.mode_btn.setStyleSheet("font-size: 14px;")
        self.mode_btn.clicked.connect(self.switch_play_mode)
        button_layout.addWidget(self.mode_btn)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)
        main_layout.addLayout(control_layout)

    def register_child(self):
        """注册孩子账户"""
        dialog = ChildRegisterDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # 调用user_manager创建孩子用户 - 确保使用大写 CHILD
            success, msg = create_user(
                self.db,
                username=data["username"],
                password=data["password"],
                user_type=UserType.CHILD,  # 这里使用枚举，确保是大写
                parent_id=self.parent_id,
            )

            if success:
                QMessageBox.information(self, "注册成功", msg)
                # 刷新统计页面的孩子列表
                self.stats_widget.children = self.stats_widget._get_children()
                self.stats_widget.child_combo.clear()
                self.stats_widget.child_combo.addItem("所有孩子", None)
                for child in self.stats_widget.children:
                    self.stats_widget.child_combo.addItem(child.username, child.id)
            else:
                QMessageBox.warning(self, "注册失败", msg)

    # 其余方法保持不变...
    def show_add_music_menu(self, pos):
        """右键显示添加音乐菜单"""
        menu = QMenu()
        menu.setStyleSheet("font-size: 13px;")
        file_action = menu.addAction("选择音频文件")
        folder_action = menu.addAction("选择音乐文件夹")
        file_action.triggered.connect(self.add_files_music)
        folder_action.triggered.connect(self.add_folder_music)
        menu.exec(self.add_music_btn.mapToGlobal(pos))

    def show_add_music_menu_direct(self):
        """左键点击直接显示菜单"""
        menu = QMenu()
        menu.setStyleSheet("font-size: 13px;")
        file_action = menu.addAction("选择音频文件")
        folder_action = menu.addAction("选择音乐文件夹")
        file_action.triggered.connect(self.add_files_music)
        folder_action.triggered.connect(self.add_folder_music)
        menu.exec(
            self.add_music_btn.mapToGlobal(
                QtCore.QPoint(0, self.add_music_btn.height())
            )
        )

    def add_files_music(self):
        """选择单个/多个音频文件添加"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择音频文件",
            "",
            f"音频文件 ({' '.join([f'*{ext}' for ext in SUPPORTED_AUDIO_FORMATS])})",
        )
        if file_paths:
            self.batch_add_music(file_paths)

    def add_folder_music(self):
        """选择文件夹，遍历所有音频文件添加"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if not folder_path:
            return

        file_paths = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(SUPPORTED_AUDIO_FORMATS):
                    full_path = os.path.abspath(os.path.join(root, file))
                    file_paths.append(full_path)

        if not file_paths:
            QMessageBox.information(
                self, "提示", "该文件夹及子文件夹中未找到支持的音频文件！"
            )
            return

        self.batch_add_music(file_paths)

    def batch_add_music(self, file_paths):
        """批量添加音乐（核心：去重逻辑）"""
        from models import Music

        existing_paths = (
            self.db.query(Music.file_path)
                .filter(Music.parent_id == self.parent_id)
                .all()
        )
        existing_paths = set([path[0] for path in existing_paths])

        new_file_paths = [path for path in file_paths if path not in existing_paths]
        if not new_file_paths:
            QMessageBox.information(
                self, "提示", "所有选中的音乐已存在于库中，无需重复添加！"
            )
            return

        default_emotion, ok = QInputDialog.getText(
            self,
            "批量添加设置",
            "请输入默认情绪类型：",
            QLineEdit.EchoMode.Normal,
            "未知情绪类型",
        )
        if not ok:
            return
        default_emotion = default_emotion.strip() or "未知情绪类型"

        success_count = 0
        fail_count = 0
        fail_files = []

        for file_path in new_file_paths:
            title = os.path.splitext(os.path.basename(file_path))[0]
            success, msg = add_music(
                self.db,
                parent_id=self.parent_id,
                title=title,
                emotion=default_emotion,
                file_path=file_path,
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
                fail_files.append(f"{os.path.basename(file_path)}：{msg}")

        result_msg = f"批量添加完成！\n✅ 成功添加：{success_count}首\n❌ 添加失败：{fail_count}首"
        if fail_files:
            result_msg += "\n\n失败详情（最多显示10条）：\n" + "\n".join(
                fail_files[:10]
            )
        QMessageBox.information(self, "添加结果", result_msg)
        self.load_musics()

    def edit_music(self):
        """编辑选中音乐的信息"""
        selected_item = self.music_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一首音乐！")
            return

        music_id = int(selected_item.data(Qt.ItemDataRole.UserRole))
        music = get_music_by_id(self.db, music_id)
        if not music:
            QMessageBox.warning(self, "警告", "该音乐不存在或已被删除！")
            self.load_musics()
            return

        dialog = MusicInfoDialog(self, music)
        if dialog.exec():
            data = dialog.get_data()
            if not data["title"]:
                QMessageBox.warning(self, "警告", "歌曲标题不能为空！")
                return

            success, msg = update_music(
                self.db, music_id=music_id, parent_id=self.parent_id, **data
            )
            QMessageBox.information(self, "编辑结果", msg)
            self.load_musics()

            if self.current_music and self.current_music.id == music_id:
                self.current_music = get_music_by_id(self.db, music_id)
                self.current_play_label.setText(
                    f"正在播放：【{self.current_music.emotion}】- {self.current_music.title}"
                )

    def delete_selected_music(self):
        """删除选中的音乐"""
        selected_item = self.music_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一首音乐！")
            return

        music_id = int(selected_item.data(Qt.ItemDataRole.UserRole))
        music = get_music_by_id(self.db, music_id)
        if not music:
            QMessageBox.warning(self, "警告", "该音乐不存在或已被删除！")
            self.load_musics()
            return

        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"是否永久删除歌曲《{music.title}》？\n删除后无法恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if self.current_music and self.current_music.id == music_id:
            self.stop_play()

        success, msg = delete_music(self.db, music_id, self.parent_id)
        QMessageBox.information(self, "删除结果", msg)
        self.load_musics()
        self.load_favorites()
        self.load_recent_plays()

        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.favorite_btn.setEnabled(False)

    def toggle_favorite(self):
        """添加/取消喜欢歌曲"""
        selected_item = self.music_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一首音乐！")
            return

        music_id = int(selected_item.data(Qt.ItemDataRole.UserRole))
        music = get_music_by_id(self.db, music_id)
        if not music:
            QMessageBox.warning(self, "警告", "该音乐不存在或已被删除！")
            self.load_musics()
            return

        from models import ParentFavorite

        existing_fav = (
            self.db.query(ParentFavorite)
                .filter(
                ParentFavorite.parent_id == self.parent_id,
                ParentFavorite.music_id == music_id,
            )
                .first()
        )

        if existing_fav:
            success, msg = remove_parent_favorite(self.db, self.parent_id, music_id)
            self.favorite_btn.setText("❤️ 添加到喜欢")
        else:
            success, msg = add_parent_favorite(self.db, self.parent_id, music_id)
            self.favorite_btn.setText("💔 取消喜欢")

        QMessageBox.information(self, "操作结果", msg)
        self.load_favorites()

    def load_musics(self):
        """加载全部音乐到列表，并更新播放列表"""
        self.music_list_widget.clear()
        musics = get_parent_musics(self.db, self.parent_id)
        self.original_playlist = musics  # 保存原始播放列表

        for music in musics:
            share_tag = " [已共享]" if music.is_shared else ""
            item_text = f"【{music.emotion}】- {music.title}{share_tag}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, music.id)
            self.music_list_widget.addItem(item)

    def load_recent_plays(self):
        """加载最近播放的音乐"""
        self.recent_play_widget.clear()
        recent_plays = get_parent_recent_plays(self.db, self.parent_id)
        for play in recent_plays:
            item_text = f"【{play['emotion']}】- {play['title']}（{play['play_time']}）"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, play["music_id"])
            self.recent_play_widget.addItem(item)

    def load_favorites(self):
        """加载喜欢的歌曲"""
        self.favorite_widget.clear()
        favorites = get_parent_favorites(self.db, self.parent_id)
        for fav in favorites:
            item_text = f"【{fav['emotion']}】- {fav['title']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, fav["music_id"])
            self.favorite_widget.addItem(item)

    def on_music_selected(self, item):
        """选中音乐时，更新按钮状态"""
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.favorite_btn.setEnabled(True)

        music_id = int(item.data(Qt.ItemDataRole.UserRole))
        from models import ParentFavorite

        is_favorite = (
            self.db.query(ParentFavorite)
                .filter(
                ParentFavorite.parent_id == self.parent_id,
                ParentFavorite.music_id == music_id,
            )
                .first()
        )
        self.favorite_btn.setText("💔 取消喜欢" if is_favorite else "❤️ 添加到喜欢")

    def play_music(self, item=None, music_id=None):
        """播放选中的音乐"""
        # 优先使用 music_id（上一首/下一首调用）
        if music_id is not None:
            music = get_music_by_id(self.db, music_id)
            if not music:
                return False
        else:
            # 从列表项播放
            if not item:
                item = self.music_list_widget.currentItem()
                if not item:
                    QMessageBox.warning(self, "警告", "请先选择一首音乐！")
                    return False

            music_id = int(item.data(Qt.ItemDataRole.UserRole))
            music = get_music_by_id(self.db, music_id)
            if not music:
                QMessageBox.warning(self, "警告", "该音乐不存在或已被删除！")
                self.load_musics()
                return False

        # 停止当前播放
        if self.is_playing:
            self.stop_play()

        # 加载并播放音乐
        try:
            pygame.mixer.music.load(music.file_path)
            pygame.mixer.music.play(start=self.pause_position / 1000)

            # 清除拖动相关标记
            if hasattr(self, "drag_start_time"):
                delattr(self, "drag_start_time")

            # 更新当前音乐状态
            self.current_music = music
            self.is_playing = True
            self.current_play_label.setText(
                f"正在播放：【{music.emotion}】- {music.title}"
            )

            # 更新当前索引
            for i, m in enumerate(self.original_playlist):
                if m.id == music.id:
                    self.current_music_index = i
                    break

            # 记录最近播放
            add_parent_recent_play(self.db, self.parent_id, music.id)
            self.load_recent_plays()

            # 重置进度
            self.play_start_time = QDateTime.currentMSecsSinceEpoch()
            self.pause_position = 0
            self.progress_bar.setValue(0)

            # 获取音乐总时长（秒）
            music_length = pygame.mixer.Sound(music.file_path).get_length()
            self.total_duration = music_length * 1000  # 转换为毫秒

            return True
        except Exception as e:
            QMessageBox.critical(self, "播放失败", f"无法播放该音乐：\n{str(e)}")
            return False

    def play_recent_music(self, item):
        """播放最近播放的音乐"""
        self.play_music(item)

    def play_favorite_music(self, item):
        """播放喜欢的歌曲"""
        self.play_music(item)

    def toggle_play(self):
        """播放/继续播放"""
        if not self.current_music:
            self.play_music()
            return

        if not self.is_playing:
            if self.pause_position > 0:
                # 如果有暂停位置，使用pause/unpause机制
                pygame.mixer.music.unpause()
            else:
                # 否则从开始或指定位置播放
                pygame.mixer.music.play(start=self.pause_position / 1000)
            self.is_playing = True
            self.current_play_label.setText(
                f"正在播放：【{self.current_music.emotion}】- {self.current_music.title}"
            )
            self.play_start_time = (
                    QDateTime.currentMSecsSinceEpoch() - self.pause_position
            )
            # 注意：不要重置pause_position，因为我们可能需要在暂停后再次使用它

    def pause_play(self):
        """暂停播放"""
        if self.is_playing and pygame.mixer.music.get_busy():
            self.pause_position = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()  # 使用pause而不是stop
            self.is_playing = False
            self.current_play_label.setText(
                f"已暂停：【{self.current_music.emotion}】- {self.current_music.title}"
            )

    def stop_play(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.pause_position = 0

        if self.play_start_time and self.current_music:
            play_duration = int(
                (QDateTime.currentMSecsSinceEpoch() - self.play_start_time) / 1000
            )
            if play_duration > 0:
                print(f"播放完成：{self.current_music.title}，时长：{play_duration}秒")
            self.play_start_time = None

        self.current_play_label.setText("未播放音乐")
        self.progress_bar.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def set_volume(self, value):
        """调节音量"""
        pygame.mixer.music.set_volume(value / 100)

    def switch_play_mode(self):
        """切换播放模式（顺序 → 单曲循环 → 随机）"""
        if self.play_mode == PlayMode.ORDER:
            self.play_mode = PlayMode.SINGLE_LOOP
            self.mode_btn.setText("🔂 单曲循环")
        elif self.play_mode == PlayMode.SINGLE_LOOP:
            self.play_mode = PlayMode.RANDOM
            self.mode_btn.setText("🔀 随机播放")
        else:
            self.play_mode = PlayMode.ORDER
            self.mode_btn.setText("🔁 顺序播放")

    def play_previous(self):
        """播放上一首"""
        if not self.original_playlist:
            return

        if self.play_mode == PlayMode.RANDOM:
            # 随机模式：重新随机选择一首
            if not self.shuffled_indices:
                self.shuffled_indices = list(range(len(self.original_playlist)))
                random.shuffle(self.shuffled_indices)
            # 找到当前索引在随机列表中的位置
            try:
                current_pos = self.shuffled_indices.index(self.current_music_index)
                prev_pos = (current_pos - 1) % len(self.shuffled_indices)
                prev_index = self.shuffled_indices[prev_pos]
            except (ValueError, AttributeError):
                prev_index = random.randint(0, len(self.original_playlist) - 1)
        else:
            # 顺序/单曲循环模式：直接找上一首
            prev_index = (self.current_music_index - 1) % len(self.original_playlist)

        prev_music = self.original_playlist[prev_index]
        self.play_music(music_id=prev_music.id)

    def play_next(self):
        """播放下一首"""
        if not self.original_playlist:
            return

        if self.play_mode == PlayMode.SINGLE_LOOP:
            # 单曲循环：重新播放当前音乐
            self.pause_position = 0
            self.play_music(music_id=self.current_music.id)
        elif self.play_mode == PlayMode.RANDOM:
            # 随机模式：随机选择（或直接找下一首）
            self.shuffled_indices = list(range(len(self.original_playlist)))
            random.shuffle(self.shuffled_indices)
            try:
                current_pos = self.shuffled_indices.index(self.current_music_index)
                next_pos = (current_pos + 1) % len(self.shuffled_indices)
                next_index = self.shuffled_indices[next_pos]
            except (ValueError, AttributeError):
                next_index = random.randint(0, len(self.original_playlist) - 1)

            next_music = self.original_playlist[next_index]
            self.play_music(music_id=next_music.id)
        else:
            # 顺序模式：播放下一首
            next_index = (self.current_music_index + 1) % len(self.original_playlist)
            next_music = self.original_playlist[next_index]
            self.play_music(music_id=next_music.id)

    def search_music(self, text):
        """搜索音乐（实时过滤）"""
        search_text = text.strip().lower()

        if not search_text:
            self.load_musics()
            return

        self.music_list_widget.clear()
        musics = get_parent_musics(self.db, self.parent_id)

        for music in musics:
            title_match = search_text in music.title.lower()
            emotion_match = search_text in music.emotion.lower()

            if title_match or emotion_match:
                share_tag = " [已共享]" if music.is_shared else ""
                item_text = f"【{music.emotion}】- {music.title}{share_tag}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, music.id)
                self.music_list_widget.addItem(item)

    def clear_search(self):
        """清除搜索并显示所有音乐"""
        self.search_input.clear()
        self.load_musics()

    def update_progress(self):
        """更新进度条和时间显示（修复版本）"""
        # 如果正在拖动，完全跳过更新
        if self.is_dragging_progress:
            return

        if self.is_playing and self.current_music and hasattr(self, "total_duration"):
            # 如果是拖动后重新播放，使用新的计算方法
            if hasattr(self, "drag_start_time") and self.drag_start_time:
                current_pos = QDateTime.currentMSecsSinceEpoch() - self.drag_start_time
            else:
                # 正常播放时使用pygame的位置
                current_pos = pygame.mixer.music.get_pos()

                if current_pos == -1:  # 音乐自然结束
                    self.on_music_finished()
                    return

            # 确保不超过总时长
            current_pos = min(current_pos, self.total_duration)

            # 计算进度比例（0-1000）
            progress_value = int((current_pos / self.total_duration) * 1000)
            self.progress_bar.setValue(progress_value)

            # 更新时间标签
            current_sec = current_pos / 1000
            total_sec = self.total_duration / 1000
            self.time_label.setText(
                f"{self.format_time(current_sec)} / {self.format_time(total_sec)}"
            )

    def on_music_finished(self):
        """音乐播放完成时的处理"""
        if self.play_mode == PlayMode.SINGLE_LOOP:
            # 单曲循环：重新播放当前音乐
            self.pause_position = 0
            self.play_music(music_id=self.current_music.id)
        else:
            # 其他模式：播放下一首
            self.play_next()

    def on_progress_drag_start(self):
        """开始拖拽进度条"""
        self.is_dragging_progress = True
        # 记录拖动前的播放状态
        self.was_playing_before_drag = self.is_playing
        # 记录拖动前的播放位置
        self.before_drag_position = pygame.mixer.music.get_pos()

    def on_progress_drag_end(self):
        """结束拖拽进度条，跳转到指定位置"""
        self.is_dragging_progress = False

        # 只有在有音乐且有时长信息时才处理
        if (
                self.current_music
                and hasattr(self, "total_duration")
                and self.total_duration > 0
        ):
            # 计算目标播放位置（毫秒）
            progress_value = self.progress_bar.value()
            target_ms = int((progress_value / 1000) * self.total_duration)

            # 更新内部状态
            self.pause_position = target_ms

            # 如果在播放，重新播放以跳转到新位置
            if self.was_playing_before_drag:
                pygame.mixer.music.stop()
                pygame.mixer.music.play(start=target_ms / 1000)
                self.is_playing = True

                # 记录拖动后的开始时间，用于进度计算
                self.drag_start_time = QDateTime.currentMSecsSinceEpoch() - target_ms

                # 清除之前的拖动开始时间
                if hasattr(self, "drag_start_time"):
                    self.drag_start_time = (
                            QDateTime.currentMSecsSinceEpoch() - target_ms
                    )
                else:
                    self.drag_start_time = (
                            QDateTime.currentMSecsSinceEpoch() - target_ms
                    )
            else:
                # 如果之前是暂停状态，只更新位置但不播放
                self.pause_position = target_ms
                # 清除拖动开始时间标记
                if hasattr(self, "drag_start_time"):
                    delattr(self, "drag_start_time")

    def handle_logout(self):
        """处理退出登录"""
        from login_window import LoginWindow

        # 停止播放并释放资源
        self.progress_timer.stop()
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        # 关闭当前窗口
        self.close()

        # 重新打开登录窗口（保存引用避免被垃圾回收）
        self.login_window = LoginWindow()
        self.login_window.show()

    def format_time(self, seconds):
        """格式化时间显示（mm:ss）"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def closeEvent(self, event):
        """窗口关闭时，释放pygame资源"""
        self.progress_timer.stop()
        # 检查mixer是否已经初始化，避免重复释放资源
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        event.accept()


# 测试代码
if __name__ == "__main__":
    import sys
    from db_utils import get_db, init_db

    init_db()
    db = next(get_db())
    app = QApplication(sys.argv)
    window = ParentPlayerWindow(parent_id=1, db=db)
    window.show()
    sys.exit(app.exec())
