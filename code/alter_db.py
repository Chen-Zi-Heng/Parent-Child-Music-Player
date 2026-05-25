# alter_db.py：更新数据库表结构
from db_utils import engine
from sqlalchemy import text

def add_unique_constraint():
    with engine.connect() as conn:
        # 添加parent_id和file_path的联合唯一约束
        conn.execute(text("""
            ALTER TABLE musics 
            ADD CONSTRAINT unique_parent_file_path 
            UNIQUE (parent_id, file_path);
        """))
        conn.commit()
        print("成功添加音乐表联合唯一约束！")

if __name__ == "__main__":
    add_unique_constraint()