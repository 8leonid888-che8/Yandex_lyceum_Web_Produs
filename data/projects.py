import sqlalchemy
from .db_session import SqlAlchemyBase

association_table = sqlalchemy.Table(
    'association',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('tasks', sqlalchemy.Integer, sqlalchemy.ForeignKey('tasks.id')),
    sqlalchemy.Column('projects', sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id'))
)


class Project(SqlAlchemyBase):
    __tablename__ = 'projects'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
