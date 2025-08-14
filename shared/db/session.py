# 导入SQLAlchemy的核心组件
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 从我们共享的配置模块中导入全局的settings实例
from shared.config import settings

# 创建数据库引擎 (the Engine)
# 引擎是SQLAlchemy应用中所有数据库操作的起点。
# 它负责处理与数据库的连接池和方言。
# settings.DATABASE_URL 来自我们的配置文件，指向PostgreSQL数据库。
# pool_pre_ping=True 是一个好习惯，它会在每次从连接池中获取连接时，
# 发送一个简单的查询来测试连接是否仍然有效，以避免因数据库重启等原因导致的连接失效问题。
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 创建一个SessionLocal类
# 这个类本身不是一个数据库会话，而是一个会话的“工厂”或“构造器”。
# 当我们需要一个数据库会话时，我们会实例化这个类。
# autocommit=False 和 autoflush=False 是推荐的默认设置。
#   - autocommit=False 表示我们希望手动控制事务的提交。
#   - autoflush=False 表示在查询前，SQLAlchemy不会自动将会话中的“脏”对象刷新到数据库。
# bind=engine 将这个会话工厂与我们创建的数据库引擎绑定起来。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    一个FastAPI依赖项，用于为每个请求提供一个数据库会话。
    它使用Python的 'yield' 关键字来实现一个生成器，
    这确保了无论请求处理成功还是失败，数据库会话最终都会被关闭。
    这是管理数据库会话生命周期的标准、可靠模式。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
