from sqlalchemy.orm import Session
from models import Music, User
from config import UserType
from datetime import datetime


def add_music(
    db: Session, parent_id: int, title: str, emotion: str, file_path: str
) -> tuple[bool, str]:
    """家长添加本地音乐"""
    # 验证是否为家长
    parent = (
        db.query(User)
        .filter(User.id == parent_id, User.user_type == UserType.PARENT)
        .first()
    )
    if not parent:
        return False, "仅家长可添加音乐！"

    try:
        music = Music(
            title=title,
            emotion=emotion,
            file_path=file_path,
            is_shared=False,  # 默认不共享
            parent_id=parent_id,
        )
        db.add(music)
        db.commit()
        db.refresh(music)
        return True, f"音乐添加成功！ID：{music.id}"
    except Exception as e:
        db.rollback()
        return False, f"添加失败：{str(e)}"


def update_music(
    db: Session, music_id: int, parent_id: int, **kwargs
) -> tuple[bool, str]:
    """家长更新音乐信息（标题、情绪类型、共享状态）"""
    music = (
        db.query(Music)
        .filter(Music.id == music_id, Music.parent_id == parent_id)
        .first()
    )
    if not music:
        return False, "音乐不存在或无权限修改！"

    try:
        # 允许更新的字段：title, emotion, is_shared
        for key, value in kwargs.items():
            if key in ["title", "emotion", "is_shared"]:
                setattr(music, key, value)
        db.commit()
        db.refresh(music)
        return True, "音乐信息更新成功！"
    except Exception as e:
        db.rollback()
        return False, f"更新失败：{str(e)}"


def delete_music(db: Session, music_id: int, parent_id: int) -> tuple[bool, str]:
    """家长删除音乐"""
    music = (
        db.query(Music)
        .filter(Music.id == music_id, Music.parent_id == parent_id)
        .first()
    )
    if not music:
        return False, "音乐不存在或无权限删除！"

    try:
        db.delete(music)
        db.commit()
        return True, "音乐删除成功！"
    except Exception as e:
        db.rollback()
        return False, f"删除失败：{str(e)}"


def get_parent_musics(db: Session, parent_id: int) -> list[Music]:
    """家长获取所有自己添加的音乐"""
    return (
        db.query(Music)
        .filter(Music.parent_id == parent_id)
        .order_by(Music.added_at.desc())
        .all()
    )


def get_child_available_musics(db: Session, parent_id: int) -> list[Music]:
    """孩子获取家长共享的音乐（不包含路径，前端仅显示标题/艺术家）"""
    return (
        db.query(Music)
        .filter(Music.parent_id == parent_id, Music.is_shared == True)
        .order_by(Music.added_at.desc())
        .all()
    )


def get_music_by_id(db: Session, music_id: int) -> Music | None:
    """通过ID获取音乐（用于播放、收藏）"""
    return db.query(Music).filter(Music.id == music_id).first()
