# models.py 顶部导入部分（补充 UniqueConstraint）
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    UniqueConstraint,  # 直接导入 UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from config import UserType

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(64), nullable=False)  # SHA256哈希（64位）
    salt = Column(String(32), nullable=False)  # 随机盐值（32位）
    user_type = Column(SQLAlchemyEnum(UserType), nullable=False)
    parent_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # 新增：关联家长ID（孩子非空，家长为空）
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系（补充亲子关联）
    parent = relationship(
        "User", remote_side=[id], backref="children"
    )  # 孩子关联家长，家长反向查孩子
    parent_musics = relationship(
        "Music", back_populates="parent", cascade="all, delete-orphan"
    )
    parent_recent_plays = relationship(
        "ParentRecentPlay", back_populates="parent", cascade="all, delete-orphan"
    )
    parent_favorites = relationship(
        "ParentFavorite", back_populates="parent", cascade="all, delete-orphan"
    )
    child_recent_plays = relationship(
        "ChildRecentPlay", back_populates="child", cascade="all, delete-orphan"
    )
    child_favorites = relationship(
        "ChildFavorite", back_populates="child", cascade="all, delete-orphan"
    )
    child_play_logs = relationship(
        "ChildPlayLog", back_populates="child", cascade="all, delete-orphan"
    )


# 音乐表（家长添加，支持共享）
# models.py 中的 Music 类修改
class Music(Base):
    __tablename__ = "musics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    emotion = Column(String(100), default="未知情绪类型")
    file_path = Column(String(255), nullable=False)  # 本地路径（孩子不可见）
    is_shared = Column(Boolean, default=False)  # 是否共享给孩子
    added_at = Column(DateTime, default=datetime.utcnow)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 新增：联合唯一约束（同一家长不能重复添加同一文件）
    __table_args__ = (
        UniqueConstraint("parent_id", "file_path", name="unique_parent_file_path"),
        {"extend_existing": True},
    )

    # 关联关系
    parent = relationship("User", back_populates="parent_musics")
    parent_recent_plays = relationship(
        "ParentRecentPlay", back_populates="music", cascade="all, delete-orphan"
    )
    child_recent_plays = relationship(
        "ChildRecentPlay", back_populates="music", cascade="all, delete-orphan"
    )
    parent_favorites = relationship(
        "ParentFavorite", back_populates="music", cascade="all, delete-orphan"
    )
    child_favorites = relationship(
        "ChildFavorite", back_populates="music", cascade="all, delete-orphan"
    )
    child_play_logs = relationship(
        "ChildPlayLog", back_populates="music", cascade="all, delete-orphan"
    )


# 家长最近播放表
class ParentRecentPlay(Base):
    __tablename__ = "parent_recent_plays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("musics.id"), nullable=False)
    play_time = Column(DateTime, default=datetime.utcnow)  # 最近播放时间

    # 关联关系
    parent = relationship("User", back_populates="parent_recent_plays")
    music = relationship("Music", back_populates="parent_recent_plays")

    # 联合唯一约束（同一首歌不重复记录，只更新时间）
    __table_args__ = ({"extend_existing": True},)


# 孩子最近播放表（不存储路径，关联音乐ID）
class ChildRecentPlay(Base):
    __tablename__ = "child_recent_plays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("musics.id"), nullable=False)
    play_time = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    child = relationship("User", back_populates="child_recent_plays")
    music = relationship("Music", back_populates="child_recent_plays")

    __table_args__ = ({"extend_existing": True},)


# 家长喜欢歌曲表（修复 UniqueConstraint 使用）
class ParentFavorite(Base):
    __tablename__ = "parent_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("musics.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # 联合唯一约束（直接使用 UniqueConstraint，无需 db. 前缀）
    __table_args__ = (
        UniqueConstraint("parent_id", "music_id", name="unique_parent_favorite"),
        {"extend_existing": True},
    )

    parent = relationship("User", back_populates="parent_favorites")
    music = relationship("Music", back_populates="parent_favorites")


# 孩子喜欢歌曲表（同样修复）
class ChildFavorite(Base):
    __tablename__ = "child_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("musics.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # 联合唯一约束（直接使用 UniqueConstraint）
    __table_args__ = (
        UniqueConstraint("child_id", "music_id", name="unique_child_favorite"),
        {"extend_existing": True},
    )

    child = relationship("User", back_populates="child_favorites")
    music = relationship("Music", back_populates="child_favorites")


# 孩子播放日志表（用于分级控制）
class ChildPlayLog(Base):
    __tablename__ = "child_play_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("musics.id"), nullable=False)
    play_duration = Column(Integer, nullable=False)  # 播放时长（秒）
    play_time = Column(DateTime, default=datetime.utcnow)  # 播放时间点

    child = relationship("User", back_populates="child_play_logs")
    music = relationship("Music", back_populates="child_play_logs")


# 补充：修复导入依赖（models.py顶部需添加）
from sqlalchemy import UniqueConstraint as db_UniqueConstraint
