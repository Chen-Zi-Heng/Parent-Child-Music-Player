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
    QMessageBox,
    QSlider,
    QTabWidget,
    QLineEdit,
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from music_manager import get_child_available_musics, get_music_by_id
from play_history_manager import add_child_recent_play, get_child_recent_plays
from favorite_manager import (
    add_child_favorite,
    remove_child_favorite,
    get_child_favorites,
)
from log_manager import log_child_play
import pygame
import os
import random


# 播放模式枚举
class PlayMode:
    ORDER = 0  # 顺序播放
    SINGLE_LOOP = 1  # 单曲循环
    RANDOM = 2  # 随机播放


class ChildPlayerWindow(QMainWindow):
    def __init__(self, child_id: int, db, parent_id: int):
        super().__init__()
        self.child_id = child_id
        self.parent_id = parent_id  # 关联的家长ID
        self.db = db
        self.current_music = None  # 当前播放的音乐对象
        self.current_music_index = -1  # 当前播放音乐在播放列表中的索引
        self.play_start_time = None  # 播放开始时间（毫秒）
        self.pause_position = 0  # 暂停时的播放位置（毫秒）
        self.is_playing = False  # 播放状态标记
        self.play_mode = PlayMode.ORDER  # 播放模式
        self.original_playlist = []  # 原始播放列表
        self.shuffled_indices = []  # 随机播放时的索引列表

        # 拖动进度条相关
        self.is_dragging_progress = False
        self.was_playing_before_drag = False

        # 初始化pygame音频
        pygame.mixer.init(frequency=44100, channels=2, buffer=1024)
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

        # 窗口配置
        self.setWindowTitle("孩子音乐播放器")
        self.setFixedSize(900, 650)  # 增加窗口尺寸以容纳更多控件
        self.init_ui()
        self.load_available_musics()  # 加载家长共享的音乐
        self.load_recent_plays()  # 加载最近播放
        self.load_favorites()  # 加载喜欢歌曲

        # 定时器：用于更新进度条
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(200)

    def init_ui(self):
        """初始化界面布局（与家长播放器相似）"""
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

        # 喜欢/取消喜欢按钮
        self.favorite_btn = QPushButton("❤️ 添加到喜欢")
        self.favorite_btn.setFixedSize(120, 40)
        self.favorite_btn.setStyleSheet("font-size: 14px;")
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.favorite_btn.setEnabled(False)
        left_layout.addWidget(self.favorite_btn)

        # 音量调节
        volume_label = QLabel("音量：")
        volume_label.setStyleSheet("font-size: 14px;")
        left_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedSize(120, 20)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        left_layout.addWidget(self.volume_slider)

        # 搜索功能
        search_label = QLabel("搜索：")
        search_label.setStyleSheet("font-size: 14px;")
        left_layout.addWidget(search_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入标题或情绪类型")
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

        # 右侧：音乐列表区
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("font-size: 14px;")

        # 1. 可用音乐标签（家长共享的）
        self.music_list_widget = QListWidget()
        self.music_list_widget.itemClicked.connect(self.on_music_selected)
        self.music_list_widget.itemDoubleClicked.connect(self.play_music)
        self.music_list_widget.setStyleSheet(
            """
            QListWidget { font-size: 13px; }
            QListWidget::item:selected { background-color: #4CAF50; color: white; }
        """
        )
        tab_widget.addTab(self.music_list_widget, "可用音乐")

        # 2. 最近播放标签
        self.recent_play_widget = QListWidget()
        self.recent_play_widget.itemDoubleClicked.connect(self.play_recent_music)
        self.recent_play_widget.setStyleSheet("QListWidget { font-size: 13px; }")
        tab_widget.addTab(self.recent_play_widget, "最近播放")

        # 3. 喜欢歌曲标签
        self.favorite_widget = QListWidget()
        self.favorite_widget.itemDoubleClicked.connect(self.play_favorite_music)
        self.favorite_widget.setStyleSheet("QListWidget { font-size: 13px; }")
        tab_widget.addTab(self.favorite_widget, "喜欢的歌曲")

        top_layout.addLayout(left_layout)
        top_layout.addWidget(tab_widget, stretch=1)
        main_layout.addLayout(top_layout)

        # 下半部分：播放控制区（与家长播放器相似）
        control_layout = QVBoxLayout()
        control_layout.setSpacing(10)

        # 播放信息标签 + 进度条
        progress_layout = QVBoxLayout()

        self.current_play_label = QLabel("未播放音乐")
        self.current_play_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.current_play_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.current_play_label)

        # 进度条布局
        progress_bar_layout = QHBoxLayout()
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        # 连接拖动信号
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

        # 上一首按钮
        self.prev_btn = QPushButton("⏮️ 上一首")
        self.prev_btn.setFixedSize(90, 40)
        self.prev_btn.setStyleSheet("font-size: 14px;")
        self.prev_btn.clicked.connect(self.play_previous)
        button_layout.addWidget(self.prev_btn)

        # 播放按钮
        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.setFixedSize(80, 40)
        self.play_btn.setStyleSheet("font-size: 14px;")
        self.play_btn.clicked.connect(self.toggle_play)
        button_layout.addWidget(self.play_btn)

        # 暂停按钮
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setFixedSize(80, 40)
        self.pause_btn.setStyleSheet("font-size: 14px;")
        self.pause_btn.clicked.connect(self.pause_play)
        button_layout.addWidget(self.pause_btn)

        # 停止按钮
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setFixedSize(80, 40)
        self.stop_btn.setStyleSheet("font-size: 14px;")
        self.stop_btn.clicked.connect(self.stop_play)
        button_layout.addWidget(self.stop_btn)

        # 下一首按钮
        self.next_btn = QPushButton("⏭️ 下一首")
        self.next_btn.setFixedSize(90, 40)
        self.next_btn.setStyleSheet("font-size: 14px;")
        self.next_btn.clicked.connect(self.play_next)
        button_layout.addWidget(self.next_btn)

        # 播放模式按钮
        self.mode_btn = QPushButton("🔁 顺序播放")
        self.mode_btn.setFixedSize(120, 40)
        self.mode_btn.setStyleSheet("font-size: 14px;")
        self.mode_btn.clicked.connect(self.switch_play_mode)
        button_layout.addWidget(self.mode_btn)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)
        main_layout.addLayout(control_layout)

    def load_available_musics(self):
        """加载家长共享的音乐（无路径）"""
        self.music_list_widget.clear()
        musics = get_child_available_musics(self.db, self.parent_id)
        self.original_playlist = musics  # 保存原始播放列表

        for music in musics:
            item_text = f"【{music.emotion}】- {music.title}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, music.id)
            self.music_list_widget.addItem(item)

    def load_recent_plays(self):
        """加载孩子最近播放（无路径）"""
        self.recent_play_widget.clear()
        recent_plays = get_child_recent_plays(self.db, self.child_id)
        for play in recent_plays:
            item_text = f"【{play['emotion']}】- {play['title']} ({play['play_time']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, play["music_id"])
            self.recent_play_widget.addItem(item)

    def load_favorites(self):
        """加载孩子喜欢的歌曲（无路径）"""
        self.favorite_widget.clear()
        favorites = get_child_favorites(self.db, self.child_id)
        for fav in favorites:
            item_text = f"【{fav['emotion']}】- {fav['title']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, fav["music_id"])
            self.favorite_widget.addItem(item)

    def on_music_selected(self, item):
        """选中音乐时启用按钮"""
        self.favorite_btn.setEnabled(True)
        # 检查是否已喜欢，更新按钮文本
        music_id = int(item.data(Qt.ItemDataRole.UserRole))
        from models import ChildFavorite

        is_favorite = (
            self.db.query(ChildFavorite)
            .filter(
                ChildFavorite.child_id == self.child_id,
                ChildFavorite.music_id == music_id,
            )
            .first()
        )
        self.favorite_btn.setText("💔 取消喜欢" if is_favorite else "❤️ 添加到喜欢")

    def toggle_favorite(self):
        """添加/取消喜欢"""
        selected_item = self.music_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一首音乐！")
            return

        music_id = int(selected_item.data(Qt.ItemDataRole.UserRole))
        music = get_music_by_id(self.db, music_id)
        if not music:
            QMessageBox.warning(self, "警告", "该音乐不存在或已被删除！")
            self.load_available_musics()
            return

        # 检查是否已喜欢
        from models import ChildFavorite

        is_favorite = (
            self.db.query(ChildFavorite)
            .filter(
                ChildFavorite.child_id == self.child_id,
                ChildFavorite.music_id == music_id,
            )
            .first()
        )

        if is_favorite:
            # 取消喜欢
            success, msg = remove_child_favorite(self.db, self.child_id, music_id)
            self.favorite_btn.setText("❤️ 添加到喜欢")
        else:
            # 添加喜欢
            success, msg = add_child_favorite(self.db, self.child_id, music_id)
            self.favorite_btn.setText("💔 取消喜欢")

        QMessageBox.information(self, "操作结果", msg)
        self.load_favorites()  # 刷新喜欢列表

    def play_music(self, item=None, music_id=None):
        """播放选中的音乐（pygame实现，仅共享音乐）"""
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
                self.load_available_musics()
                return False

        # 验证是否已共享
        if not music or not music.is_shared:
            QMessageBox.warning(self, "警告", "该歌曲不可播放！")
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
            add_child_recent_play(self.db, self.child_id, music_id)
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
        """播放喜欢的音乐"""
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
        """停止播放（记录孩子播放日志）"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.pause_position = 0

        # 记录孩子播放时长到数据库和日志文件
        if self.play_start_time and self.current_music:
            play_duration = int(
                (QDateTime.currentMSecsSinceEpoch() - self.play_start_time) / 1000
            )
            if play_duration > 0:  # 仅记录有效播放时长（>0秒）
                log_child_play(
                    self.db, self.child_id, self.current_music.id, play_duration
                )
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
            self.load_available_musics()
            return

        self.music_list_widget.clear()
        musics = get_child_available_musics(self.db, self.parent_id)

        for music in musics:
            # 检查标题和情绪类型是否匹配
            title_match = search_text in music.title.lower()
            emotion_match = search_text in music.emotion.lower()

            if title_match or emotion_match:
                item_text = f"【{music.emotion}】- {music.title}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, music.id)
                self.music_list_widget.addItem(item)

    def clear_search(self):
        """清除搜索并显示所有音乐"""
        self.search_input.clear()
        self.load_available_musics()

    def update_progress(self):
        """更新进度条和时间显示"""
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


# 测试孩子窗口
if __name__ == "__main__":
    import sys
    from db_utils import get_db

    app = QApplication(sys.argv)
    db = next(get_db())
    window = ChildPlayerWindow(child_id=2, db=db, parent_id=1)
    window.show()
    sys.exit(app.exec())
