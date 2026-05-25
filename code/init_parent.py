"""首次运行时创建家长用户（仅允许创建一个家长）"""
import argparse
from db_utils import get_db
from user_manager import create_user
from config import UserType


def init_parent():
    parser = argparse.ArgumentParser(description="初始化家长用户")
    parser.add_argument("--username", required=True, help="家长用户名")
    parser.add_argument("--password", required=True, help="家长密码")
    args = parser.parse_args()

    db = next(get_db())

    # 检查是否已存在家长用户
    from models import User
    existing_parent = db.query(User).filter(User.user_type == UserType.PARENT).first()
    if existing_parent:
        print(f"已存在家长用户：{existing_parent.username}，无需重复创建！")
        return

    # 创建家长用户
    success, msg = create_user(db, args.username, args.password, UserType.PARENT)
    print(msg)


if __name__ == "__main__":
    # 运行命令示例：python init_parent.py --username Mom --password 123456
    init_parent()