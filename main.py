from flask import Flask, render_template, redirect, flash
from data import db_session
from data.projects import Project
from data.users import User
from data.tasks import Task
from forms.user import RegisterForm, LoginForm
from forms.task import AddTask
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy import func
from produs_funcs import update_deadline
app = Flask(__name__)
app.config["SECRET_KEY"] = "produs_private_key"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


def main():
    db_session.global_init("db/produs.db")
    # db_sess = db_session.create_session()
    # task = Task()
    # task.user_id = 1
    # task.description = "first task"
    # # task.project = "project1"
    # db_sess.add(task)
    # db_sess.commit()
    app.run()


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация", form=form, massage="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   massage="Такой пользователь уже существует")
        user = User(
            username=form.username.data,
            email=form.email.data,
            tg_name=form.tg_name.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Registrations', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html", massage="Incorrect login or password", form=form, title='Authorization')
    return render_template('login.html', title='Authorization', form=form)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    incomplete_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(), Task.completed == False).all()
    completed_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(), Task.completed == True).all()
    return render_template("index.html", title="Today",incomplete_tasks= incomplete_tasks, completed_tasks=completed_tasks)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/add_task", methods=["GET", "POST"])
@login_required
def add_task():
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).all()
    form = AddTask()

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        # Создание задачи
        task_t = Task(
            name=form.name.data,
            description=form.description.data,
            deadline=form.deadline.data,
            reminders=form.reminders.data,
            user=user,  # Используем объект пользователя, а не его id
        )

        # Добавление задачи в сессию
        db_sess.add(task_t)
        project = db_sess.query(Project).filter(Project.name == form.project.data).first()
        if project:
            task_t.project.append(project)  # Добавление проекта к задаче

        db_sess.commit()
        return redirect('/')

    return render_template('add_task.html', title='Add task', form=form, projects=projects)


@app.route("/all_tasks", methods=["GET", "POST"])
def show_all_tasks():
    update_deadline()
    db_sess = db_session.create_session()
    incomplete_tasks = sorted(db_sess.query(Task).filter(Task.completed == False).all(), key=lambda x: x.deadline)
    completed_tasks = sorted(db_sess.query(Task).filter(Task.completed == True).all(), key=lambda x: x.deadline)
    return render_template("list_of_tasks.html", title="All tasks", incomplete_tasks=incomplete_tasks,
                           completed_tasks=completed_tasks)


# # выполнить задачу
# @app.route("/update_task_completed/<int:id_task>", methods=["GET", "POST"])
# def update_completed_task(id_task):
#     db_sess = db_session.create_session()
#     task = db_sess.query(Task).filter(Task.id == id_task).first()
#     task.completed = False
#     db_sess.commit()
#     return redirect("/")
#
# # вернуть
@app.route("/update_task/<string:status>/<string:page>/<int:id_task>", methods=["GET", "POST"])
def update_checkbox_task(status, page, id_task):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == id_task).first()
    if status == "completed":
        task.completed = False
    if status == "uncompleted":
        task.completed = True
    db_sess.commit()
    if page in "all":
        return redirect("/all_tasks")
    if page in "today":
        return redirect("/")


if __name__ == "__main__":
    main()
