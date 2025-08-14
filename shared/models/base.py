# 从sqlalchemy.ext.declarative中导入declarative_base函数
# 这个函数是SQLAlchemy声明式映射的核心。
from sqlalchemy.orm import declarative_base

# 调用declarative_base()来创建一个Base类
# 我们项目中的所有ORM模型（即数据表对应的Python类）都将继承自这个Base类。
# 这使得SQLAlchemy的声明式系统能够发现我们所有的模型，并将它们与数据库中的表关联起来。
Base = declarative_base()
