import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from produs_funcs import generate_api_key


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    api = sqlalchemy.Column(sqlalchemy.String, default=generate_api_key())
    number_of_files = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    tg_name = sqlalchemy.Column(sqlalchemy.String)

    tasks = orm.relationship("Task", back_populates="user", foreign_keys="Task.user_id")
    projects = orm.relationship("Project", back_populates="user", foreign_keys="Project.user_id")

    def __repr__(self):
        return f'<User > {self.id} {self.name} {self.email}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
