from sqlalchemy.orm import Session
from models import ParentRecentPlay, ChildRecentPlay, Music
from datetime import datetime


def add_parent_recent_play(db: Session, parent_id: int, music_id: int):
    """添加家长最近播放记录（存在则更新时间）"""
    # 先查询是否已存在
    existing = db.query(ParentRecentPlay).filter(
        ParentRecentPlay.parent_id == parent_id,
        ParentRecentPlay.music_id == music_id
    ).first()

    if existing:
        existing.play_time = datetime.utcnow()
    else:
        existing = ParentRecentPlay(parent_id=parent_id, music_id=music_id)
        db.add(existing)

    db.commit()
    return existing


def add_child_recent_play(db: Session, child_id: int, music_id: int):
    """添加孩子最近播放记录（存在则更新时间）"""
    existing = db.query(ChildRecentPlay).filter(
        ChildRecentPlay.child_id == child_id,
        ChildRecentPlay.music_id == music_id
    ).first()

    if existing:
        existing.play_time = datetime.utcnow()
    else:
        existing = ChildRecentPlay(child_id=child_id, music_id=music_id)
        db.add(existing)

    db.commit()
    return existing


def get_parent_recent_plays(db: Session, parent_id: int, limit: int = 10) -> list[dict]:
    """家长获取最近播放（带路径）"""
    history = db.query(ParentRecentPlay, Music).join(
        Music, ParentRecentPlay.music_id == Music.id
    ).filter(ParentRecentPlay.parent_id == parent_id).order_by(
        ParentRecentPlay.play_time.desc()
    ).limit(limit).all()

    return [
        {
            "id": item[0].id,
            "music_id": item[1].id,
            "title": item[1].title,
            "emotion": item[1].emotion,
            "file_path": item[1].file_path,
            "play_time": item[0].play_time.strftime("%Y-%m-%d %H:%M:%S")
        } for item in history
    ]


def get_child_recent_plays(db: Session, child_id: int, limit: int = 10) -> list[dict]:
    """孩子获取最近播放（不带路径）"""
    history = db.query(ChildRecentPlay, Music).join(
        Music, ChildRecentPlay.music_id == Music.id
    ).filter(
        ChildRecentPlay.child_id == child_id,
        Music.is_shared == True  # 只显示已共享的
    ).order_by(
        ChildRecentPlay.play_time.desc()
    ).limit(limit).all()

    return [
        {
            "id": item[0].id,
            "music_id": item[1].id,
            "title": item[1].title,
            "emotion": item[1].emotion,
            "play_time": item[0].play_time.strftime("%Y-%m-%d %H:%M:%S")
        } for item in history
    ]