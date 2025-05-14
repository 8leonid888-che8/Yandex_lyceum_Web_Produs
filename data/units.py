from data import db_session
from data.projects import Project
from data.users import User
from flask_restful import abort


def abort_if_users_not_found(user_api):
    session = db_session.create_session()
    users = session.query(User).filter(User.api == user_api).first()
    if not users:
        abort(404, message=f"Users not found")


def abort_if_project_not_found(name_project):
    session = db_session.create_session()
    project = session.query(Project).filter(Project.name == name_project).first()
    print(project)
    if not project:
        abort(404, message=f"Project {name_project} not found")
