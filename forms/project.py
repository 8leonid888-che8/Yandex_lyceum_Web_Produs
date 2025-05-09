from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, ValidationError, BooleanField
from wtforms.validators import DataRequired


class AddProject(FlaskForm):
    name = StringField("Project", validators=[DataRequired()])
    submit = SubmitField("Submit")

