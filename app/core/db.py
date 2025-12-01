# app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/llmagent?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    echo=False,  # 디버깅용으로 보고 싶으면 True
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_conn():
    """
    기존에는 connection_pool.PymysqlConnectionPool 에서 커넥션을 가져왔지만,
    이제는 SQLAlchemy Session을 반환함.
    함수 이름을 그대로 두는 이유:
    - 기존 서비스/레포지토리 코드와의 호환성을 유지하기 위해
    - DB 구현체(pymysql → sqlalchemy)를 숨기기 위해
    """
    return SessionLocal()


def release_conn(conn):
    """
    기존에는 pool.release_connection(conn)을 호출했지만,
    이제는 SQLAlchemy Session을 닫기만 하면 됨.
    """
    conn.close()
