from data import db_session
from data.projects import Project

db_session.global_init("db/produs.db")

db_sess = db_session.create_session()
