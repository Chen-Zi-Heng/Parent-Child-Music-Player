from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base
from config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False)  # echo=True开启SQL日志（调试用）

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化数据库（创建所有表）"""
    try:
        Base.metadata.create_all(bind=engine)
        print("数据库初始化成功！")
    except SQLAlchemyError as e:
        print(f"数据库初始化失败：{str(e)}")

def get_db():
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库（首次运行自动创建表）
if __name__ == "__main__":
    init_db()