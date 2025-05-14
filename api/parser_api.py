from email.policy import default

from flask_restful import reqparse

from flask_restful import reqparse
from datetime import datetime


def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return date_string
    except ValueError:
        raise ValueError("Некорректный формат даты. Ожидается YYYY-MM-DDTHH:MM.")


from flask_restful import reqparse
from datetime import datetime


def validate_date_time(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%dT%H:%M')
        return date_string
    except ValueError:
        raise ValueError("Некорректный формат даты. Ожидается YYYY-MM-DDTHH:MM.")


parser_tasks = reqparse.RequestParser()
parser_tasks.add_argument("name", required=True)
parser_tasks.add_argument("description", required=False)
parser_tasks.add_argument("deadline", required=True, type=validate_date)
parser_tasks.add_argument("reminders", required=False, type=validate_date_time)
parser_tasks.add_argument("project", required=False)

parser_edited_tasks = reqparse.RequestParser()
parser_tasks.add_argument("name", required=False)
parser_tasks.add_argument("description", required=False)
parser_tasks.add_argument("deadline", required=False, type=validate_date)
parser_tasks.add_argument("reminders", required=False, type=validate_date_time)
parser_tasks.add_argument("project", required=False)




parser_projects = reqparse.RequestParser()
parser_projects.add_argument("name", required=True)

parser_edited_projects = reqparse.RequestParser()
parser_edited_projects.add_argument("name", required=False)
