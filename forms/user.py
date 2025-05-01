from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, ValidationError, BooleanField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    username = StringField("Surname", validators=[DataRequired()])
    tg_name = StringField("Telegram", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_again = PasswordField("Repeat password", validators=[DataRequired()])

    def validate_tg_name(self, tg_name):
        if '@' not in tg_name.data:
            raise ValidationError('Telegram name must contain the "@" symbol.')

    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Enter")