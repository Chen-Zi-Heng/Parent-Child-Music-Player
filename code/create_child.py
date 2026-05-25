# create_child.py：创建孩子用户（需指定家长ID）
import argparse
from db_utils import get_db
from user_manager import create_user
from config import UserType


def create_child_user():
    parser = argparse.ArgumentParser(description="创建孩子用户（需关联家长）")
    parser.add_argument("--username", required=True, help="孩子用户名")
    parser.add_argument("--password", required=True, help="孩子密码")
    parser.add_argument("--parent-id", required=True, type=int, help="家长用户ID（默认是1）")
    args = parser.parse_args()

    db = next(get_db())
    success, msg = create_user(
        db,
        username=args.username,
        password=args.password,
        user_type=UserType.CHILD,
        parent_id=args.parent_id
    )
    print(msg)


if __name__ == "__main__":
    # 运行示例：python create_child.py --username child1 --password 123456 --parent-id 1
    create_child_user()