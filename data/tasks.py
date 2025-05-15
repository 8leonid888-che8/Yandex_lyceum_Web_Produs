from email.policy import default

import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin


class Task(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "tasks"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    deadline = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    creation_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    reminders = sqlalchemy.Column(sqlalchemy.String)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship("User", back_populates="tasks", foreign_keys=[user_id])
    project = orm.relationship("Project",
                               secondary="association",
                               backref="tasks")
    completed = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    late = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    file = sqlalchemy.Column(sqlalchemy.String)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __str__(self):
        return f"{self.id} {self.name}"
