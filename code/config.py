import os
from enum import Enum
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置（优先从.env读取）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
)

# 日志配置
LOG_FILE = "child_play_logs.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - ChildID:%(child_id)s - MusicID:%(music_id)s - PlayDuration:%(play_duration)s - Message:%(message)s"
LOG_LEVEL = "INFO"

# 用户类型枚举
class UserType(Enum):
    PARENT = "parent"
    CHILD = "child"