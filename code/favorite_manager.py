from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import ParentFavorite, ChildFavorite, Music
from config import UserType


def add_parent_favorite(db: Session, parent_id: int, music_id: int) -> tuple[bool, str]:
    """家长添加喜欢的歌曲"""
    try:
        favorite = ParentFavorite(parent_id=parent_id, music_id=music_id)
        db.add(favorite)
        db.commit()
        return True, "添加到喜欢成功！"
    except IntegrityError:
        db.rollback()
        return False, "该歌曲已在喜欢列表中！"
    except Exception as e:
        db.rollback()
        return False, f"添加失败：{str(e)}"


def add_child_favorite(db: Session, child_id: int, music_id: int) -> tuple[bool, str]:
    """孩子添加喜欢的歌曲（仅共享歌曲）"""
    # 验证歌曲是否已共享
    music = db.query(Music).filter(Music.id == music_id, Music.is_shared == True).first()
    if not music:
        return False, "仅能收藏家长共享的歌曲！"

    try:
        favorite = ChildFavorite(child_id=child_id, music_id=music_id)
        db.add(favorite)
        db.commit()
        return True, "添加到喜欢成功！"
    except IntegrityError:
        db.rollback()
        return False, "该歌曲已在喜欢列表中！"
    except Exception as e:
        db.rollback()
        return False, f"添加失败：{str(e)}"


def remove_parent_favorite(db: Session, parent_id: int, music_id: int) -> tuple[bool, str]:
    """家长取消喜欢"""
    favorite = db.query(ParentFavorite).filter(
        ParentFavorite.parent_id == parent_id,
        ParentFavorite.music_id == music_id
    ).first()
    if not favorite:
        return False, "该歌曲不在喜欢列表中！"

    try:
        db.delete(favorite)
        db.commit()
        return True, "取消喜欢成功！"
    except Exception as e:
        db.rollback()
        return False, f"取消失败：{str(e)}"


def remove_child_favorite(db: Session, child_id: int, music_id: int) -> tuple[bool, str]:
    """孩子取消喜欢"""
    favorite = db.query(ChildFavorite).filter(
        ChildFavorite.child_id == child_id,
        ChildFavorite.music_id == music_id
    ).first()
    if not favorite:
        return False, "该歌曲不在喜欢列表中！"

    try:
        db.delete(favorite)
        db.commit()
        return True, "取消喜欢成功！"
    except Exception as e:
        db.rollback()
        return False, f"取消失败：{str(e)}"


def get_parent_favorites(db: Session, parent_id: int) -> list[dict]:
    """家长获取喜欢的歌曲（带路径）"""
    favorites = db.query(ParentFavorite, Music).join(
        Music, ParentFavorite.music_id == Music.id
    ).filter(ParentFavorite.parent_id == parent_id).order_by(
        ParentFavorite.added_at.desc()
    ).all()

    return [
        {
            "id": item[0].id,
            "music_id": item[1].id,
            "title": item[1].title,
            "emotion": item[1].emotion,
            "file_path": item[1].file_path,
            "added_at": item[0].added_at.strftime("%Y-%m-%d %H:%M:%S")
        } for item in favorites
    ]


def get_child_favorites(db: Session, child_id: int) -> list[dict]:
    """孩子获取喜欢的歌曲（不带路径）"""
    favorites = db.query(ChildFavorite, Music).join(
        Music, ChildFavorite.music_id == Music.id
    ).filter(
        ChildFavorite.child_id == child_id,
        Music.is_shared == True
    ).order_by(
        ChildFavorite.added_at.desc()
    ).all()

    return [
        {
            "id": item[0].id,
            "music_id": item[1].id,
            "title": item[1].title,
            "emotion": item[1].emotion,
            "added_at": item[0].added_at.strftime("%Y-%m-%d %H:%M:%S")
        } for item in favorites
    ]