import logging
from sqlalchemy.orm import Session
from models import ChildPlayLog
from config import LOG_FILE, LOG_FORMAT, LOG_LEVEL
from datetime import datetime
import pytz

# 配置日志器
logger = logging.getLogger("child_play_logger")
logger.setLevel(getattr(logging, LOG_LEVEL))

# 文件处理器（按时间轮转可选，此处简化为单个文件）
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.propagate = False  # 避免重复输出到控制台


def get_china_time():
    """获取中国时间（北京时间）"""
    china_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(china_tz)


def log_child_play(db: Session, child_id: int, music_id: int, play_duration: int) -> tuple[bool, str]:
    """记录孩子播放日志（数据库+文件双存储）- 使用中国时区"""
    try:
        # 使用中国时区
        china_time = get_china_time()

        # 1. 写入数据库
        log = ChildPlayLog(
            child_id=child_id,
            music_id=music_id,
            play_duration=play_duration,
            play_time=china_time  # 使用中国时间
        )
        db.add(log)
        db.commit()

        # 2. 写入日志文件
        logger.info(
            f"孩子播放记录 - 时间: {china_time}, 孩子ID: {child_id}, 音乐ID: {music_id}, 播放时长: {play_duration}秒",
            extra={
                "child_id": child_id,
                "music_id": music_id,
                "play_duration": play_duration,
                "play_time": china_time.isoformat()
            }
        )

        return True, "日志记录成功"
    except Exception as e:
        db.rollback()
        logger.error(
            f"日志记录失败：{str(e)} - 孩子ID: {child_id}, 音乐ID: {music_id}, 播放时长: {play_duration}秒",
            extra={
                "child_id": child_id,
                "music_id": music_id,
                "play_duration": play_duration
            }
        )
        return False, f"日志记录失败：{str(e)}"


def get_child_play_stats(db: Session, child_id: int, days: int = 7) -> dict:
    """获取孩子最近N天播放统计（使用中国时区）"""
    from datetime import timedelta
    china_tz = pytz.timezone('Asia/Shanghai')

    # 使用中国时区的当前时间
    china_now = datetime.now(china_tz)
    start_date = china_now - timedelta(days=days)

    # 查询时考虑时区转换
    logs = db.query(ChildPlayLog).filter(
        ChildPlayLog.child_id == child_id,
        ChildPlayLog.play_time >= start_date
    ).all()

    total_duration = sum(log.play_duration for log in logs)  # 总播放时长（秒）
    total_songs = len(set(log.music_id for log in logs))  # 播放歌曲总数（去重）
    total_plays = len(logs)  # 总播放次数

    return {
        "days": days,
        "total_duration": total_duration,
        "total_songs": total_songs,
        "total_plays": total_plays,
        "avg_duration_per_play": total_duration / total_plays if total_plays > 0 else 0
    }


def get_child_daily_stats(db: Session, parent_id: int, days: int = 30) -> list:
    """获取家长所有孩子的每日播放统计（中国时区）"""
    from datetime import timedelta
    from models import User, ChildPlayLog
    import pytz

    china_tz = pytz.timezone('Asia/Shanghai')
    china_now = datetime.now(china_tz)
    start_date = china_now - timedelta(days=days)

    # 获取家长的所有孩子
    children = db.query(User).filter(
        User.parent_id == parent_id,
        User.user_type == "CHILD"
    ).all()

    daily_stats = []

    for child in children:
        # 查询该孩子的播放记录
        logs = db.query(ChildPlayLog).filter(
            ChildPlayLog.child_id == child.id,
            ChildPlayLog.play_time >= start_date
        ).all()

        # 按日期分组统计
        date_stats = {}
        for log in logs:
            # 转换为中国时区的日期
            play_date = log.play_time.astimezone(china_tz).date()
            date_str = play_date.isoformat()

            if date_str not in date_stats:
                date_stats[date_str] = {
                    "date": play_date,
                    "play_count": 0,
                    "total_duration": 0,
                    "songs_played": set()
                }

            date_stats[date_str]["play_count"] += 1
            date_stats[date_str]["total_duration"] += log.play_duration
            date_stats[date_str]["songs_played"].add(log.music_id)

        # 整理数据
        for date_str, stats in date_stats.items():
            daily_stats.append({
                "child_id":child.id,
                "child_name": child.username,
                "date": stats["date"],
                "play_count": stats["play_count"],
                "total_duration": stats["total_duration"],
                "songs_count": len(stats["songs_played"])
            })

    # 按日期排序
    daily_stats.sort(key=lambda x: x["date"], reverse=True)
    return daily_stats


def cleanup_old_logs(db: Session, days: int = 30):
    """清理指定天数前的日志记录（每月清理一次）"""
    from datetime import timedelta
    import pytz

    china_tz = pytz.timezone('Asia/Shanghai')
    cutoff_date = datetime.now(china_tz) - timedelta(days=days)

    try:
        # 删除旧记录
        deleted_count = db.query(ChildPlayLog).filter(
            ChildPlayLog.play_time < cutoff_date
        ).delete()

        db.commit()

        # 记录清理操作
        logger.info(f"日志清理完成，删除了 {deleted_count} 条 {days} 天前的记录")

        return True, f"成功清理 {deleted_count} 条旧日志记录"
    except Exception as e:
        db.rollback()
        logger.error(f"日志清理失败：{str(e)}")
        return False, f"日志清理失败：{str(e)}"