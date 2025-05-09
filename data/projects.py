import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

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
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship("User", back_populates="projects", foreign_keys=[user_id])
