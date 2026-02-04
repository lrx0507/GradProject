from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL 数据库连接 URL（适配项目专属库 trailSystem）
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123456@localhost:5432/trailSystem"

# 创建数据库引擎（建立基础连接）
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建会话工厂（手动控制事务，关闭自动提交/自动刷新）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类（所有数据库模型需继承此类，自动生成数据表）
Base = declarative_base()