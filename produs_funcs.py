from data import db_session
from datetime import datetime
from data.tasks import Task
from sqlalchemy import func
import secrets

def update_deadline():
    db_sess = db_session.create_session()
    for i in db_sess.query(Task).filter(Task.deadline < datetime.now().date()):
        i.late = True
        db_sess.commit()
    for i in db_sess.query(Task).filter(Task.deadline >= datetime.now().date()):
        i.late = False
        db_sess.commit()


def generate_api_key(length=16):
    return secrets.token_hex(length)
