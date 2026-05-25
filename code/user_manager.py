import hashlib
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User
from config import UserType

def verify_user(db: Session, username: str, password: str) -> tuple[User | None, str]:
    """验证用户登录（返回用户对象或错误信息）"""
    # 1. 查询用户
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None, "用户名不存在"

    # 2. 验证密码
    expected_hash = hash_password(password, user.salt)
    if user.password_hash != expected_hash:
        return None, "密码错误"

    return user, "登录成功"

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """通过ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def generate_salt() -> str:
    """生成32位随机盐值"""
    return secrets.token_hex(16)  # 16字节=32位十六进制字符串


def hash_password(password: str, salt: str) -> str:
    """密码加密：SHA256(密码+盐值)"""
    combined = (password + salt).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

# user_manager.py 中的 create_user 函数修改
def create_user(db: Session, username: str, password: str, user_type: UserType, parent_id: int = None) -> tuple[
    bool, str]:
    """创建用户（家长/孩子）：孩子必须指定parent_id"""
    try:
        # 验证：孩子用户必须传parent_id
        if user_type == UserType.CHILD and not parent_id:
            return False, "创建孩子用户必须指定家长ID！"

        # 验证：parent_id必须是存在的家长用户
        if parent_id:
            parent = db.query(User).filter(User.id == parent_id, User.user_type == UserType.PARENT).first()
            if not parent:
                return False, f"家长ID {parent_id} 不存在！"

        salt = generate_salt()
        password_hash = hash_password(password, salt)

        user = User(
            username=username,
            password_hash=password_hash,
            salt=salt,
            user_type=user_type,
            parent_id=parent_id  # 新增：传递家长ID
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return True, f"{user_type.value}用户创建成功！用户ID：{user.id}"
    except IntegrityError:
        db.rollback()
        return False, f"用户名{username}已存在！"
    except Exception as e:
        db.rollback()
        return False, f"创建失败：{str(e)}"




# 测试代码
if __name__ == "__main__":
    from db_utils import get_db

    db = next(get_db())

    # 测试创建家长用户
    # success, msg = create_user(db, "parent1", "123456", UserType.PARENT)
    # print(msg)

    # 测试创建孩子用户
    # success, msg = create_user(db, "child1", "123456", UserType.CHILD)
    # print(msg)

    # 测试登录
    # user, msg = verify_user(db, "parent1", "123456")
    # print(f"登录结果：{msg}，用户类型：{user.user_type.value if user else None}")