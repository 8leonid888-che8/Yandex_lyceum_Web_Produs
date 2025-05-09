from flask_wtf import FlaskForm
from data import db_session
from data.projects import Project
from wtforms import StringField, SubmitField, ValidationError, DateField
from wtforms.validators import DataRequired, Optional
from datetime import datetime


class AddTask(FlaskForm):
    name = StringField("Task", validators=[DataRequired()])
    description = StringField("Description", validators=[Optional()])
    deadline = DateField("Deadline", format='%Y-%m-%d', validators=[DataRequired()])
    reminders = StringField("Reminder", validators=[Optional()])
    project = StringField("Project", validators=[Optional()], default=None)
    def validate_project(self, project):
        db_sess = db_session.create_session()
        if not db_sess.query(Project).filter(Project.name == project.data).first():
            raise ValidationError(f'Not found project with name {project}')

    def validate_deadline(self, deadline):
        if deadline.data < datetime.now().date():
            raise ValidationError("In the last")

    def validate_reminders(self, reminders):
        if datetime.strptime(reminders.data, "%Y-%m-%dT%H:%M").date() < datetime.now().date():
            raise ValidationError("In the last or --0-0")
        if datetime.strptime(reminders.data, "%Y-%m-%dT%H:%M").date() == datetime.now().date():
            if datetime.strptime(reminders.data, "%Y-%m-%dT%H:%M").time() <= datetime.now().time():
                raise ValidationError("In the last or --0-0")
        if datetime.strptime(reminders.data, "%Y-%m-%dT%H:%M").date() > self.deadline.data:
            raise ValidationError("In the last or --0-0")

    submit = SubmitField("Submit")
