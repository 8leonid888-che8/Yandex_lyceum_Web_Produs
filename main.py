from flask import Flask, render_template, redirect, flash, request, abort
from flask_restful import reqparse, abort, Api, Resource
from sqlalchemy.testing.suite.test_reflection import users

from data import db_session
from data.projects import Project
from data.users import User
from data.tasks import Task
from forms.user import RegisterForm, LoginForm
from forms.task import AddTask
from forms.project import AddProject
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy import func
from produs_funcs import update_deadline, generate_api_key
from api import tasks_resource
from api import projects_resource
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
api = Api(app)
app.config["SECRET_KEY"] = "produs_private_key"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


def main():
    db_session.global_init("db/produs.db")
    api.add_resource(tasks_resource.TaskResource, "/api/<string:user_api>/task/<path:args>/")
    api.add_resource(projects_resource.ProjectResource, "/api/<string:user_api>/project/<path:args>/")

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
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        incomplete_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(),
                                                      Task.completed == False, Task.user == current_user).all()
        completed_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(),
                                                     Task.completed == True, Task.user == current_user).all()
        return render_template("index.html", title="Today", incomplete_tasks=incomplete_tasks,
                               completed_tasks=completed_tasks)
    else:
        return render_template("information.html", title="Produs")


@app.route('/edit/<string:page>/<string:obj>/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_obj(page, obj, id):
    if obj in "task":
        db_sess = db_session.create_session()
        projects = db_sess.query(Project).all()
        form = AddTask()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if request.method == "GET":
            db_sess = db_session.create_session()
            task = db_sess.query(Task).filter(Task.id == id, Task.user == current_user).first()
            if task:
                form.name.data = task.name
                form.description.data = task.description
                form.deadline.data = task.deadline
                form.reminders.data = task.reminders
                form.project.data = task.project
                form.file.data = task.file
                if task.file:
                    user.number_of_files += 1
                    db_sess.merge(user)
                    db_sess.commit()
            else:
                abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            task = db_sess.query(Task).filter(Task.id == id,
                                              Task.user == current_user
                                              ).first()
            if task:
                task.name = form.name.data
                task.description = form.description.data
                task.deadline = form.deadline.data
                task.reminders = form.reminders.data
                if form.file.data and user.number_of_files > 0:
                    file = form.file.data
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('static/img', filename)
                    task_file = f'static/img/{filename}'
                    if task.file and task_file != task.file:
                        try:
                            os.remove(task.file)
                        except FileNotFoundError:
                            pass
                    file.save(file_path)
                    task.file = task_file
                    user.number_of_files -= 1
                db_sess.merge(task)
                db_sess.merge(user)
                project = db_sess.query(Project).filter(Project.name == form.project.data,
                                                        Project.user == current_user).first()
                if project:
                    task.project.append(project)  # Добавление проекта к задаче
                db_sess.commit()
                if page in "all":
                    return redirect("/all_tasks")
                if page in "today":
                    return redirect("/")

            else:
                abort(404)
        return render_template('add_task.html',
                               title='Edit task',
                               form=form, projects=projects
                               )
    if obj in "project":
        form = AddProject()
        if request.method == "GET":
            db_sess = db_session.create_session()
            project = db_sess.query(Project).filter(Project.id == id, Project.user == current_user).first()
            if project:
                form.name.data = project.name
            else:
                abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            project = db_sess.query(Project).filter(Project.id == id,
                                                    Project.user == current_user
                                                    ).first()
            if project:
                project.name = form.name.data
                db_sess.merge(project)
                db_sess.commit()
                return redirect("/projects")

            else:
                abort(404)
        return render_template('add_project.html',
                               title='Edit project',
                               form=form
                               )


@app.route('/delete/<string:page>/<string:obj>/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_obj(page, obj, id):
    print(obj)
    if obj in "task":
        db_sess = db_session.create_session()
        task = db_sess.query(Task).filter(Task.id == id,
                                          Task.user == current_user
                                          ).first()
        if task:
            if task.file:
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                try:
                    os.remove(task.file)
                    user.number_of_files += 1
                    db_sess.merge(user)
                except FileNotFoundError:
                    pass

            db_sess.delete(task)
            db_sess.commit()
        else:
            abort(404)
        if page in "all":
            return redirect("/all_tasks")
        if page in "today":
            return redirect("/")

    if obj in "project":
        db_sess = db_session.create_session()
        project = db_sess.query(Project).filter(Project.id == id,
                                                Project.user == current_user
                                                ).first()
        if project:
            db_sess.delete(project)
            db_sess.commit()
        else:
            abort(404)
        return redirect("/projects")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/add_task", methods=["GET", "POST"])
@login_required
def add_task():
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).filter(Project.user == current_user)
    form = AddTask()

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        # Создание задачи
        task_t = Task(
            name=form.name.data,
            description=form.description.data,
            deadline=form.deadline.data,
            reminders=form.reminders.data,
            user=user
        )
        if form.file.data and user.number_of_files > 0:
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/img', filename)
            file.save(file_path)
            task_t.file = f'static/img/{filename}'
            user.number_of_files -= 1
            db_sess.merge(user)

        db_sess.add(task_t)
        project = db_sess.query(Project).filter(Project.name == form.project.data, Project.user == current_user).first()
        if project:
            task_t.project.append(project)  # Добавление проекта к задаче

        db_sess.commit()
        return redirect('/')

    return render_template('add_task.html', title='Add task', form=form, projects=projects)


@app.route("/all_tasks", methods=["GET", "POST"])
def show_all_tasks():
    update_deadline()
    db_sess = db_session.create_session()
    incomplete_tasks = sorted(db_sess.query(Task).filter(Task.completed == False, Task.user == current_user).all(),
                              key=lambda x: x.deadline)
    completed_tasks = sorted(db_sess.query(Task).filter(Task.completed == True, Task.user == current_user).all(),
                             key=lambda x: x.deadline)
    return render_template("all_tasks.html", title="All tasks", incomplete_tasks=incomplete_tasks,
                           completed_tasks=completed_tasks)


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
    if "project" in page:
        new_page = page.split("_")
        return redirect(f"/{new_page[0]}/{new_page[1]}")


@app.route("/projects", methods=["GET", "POST"])
def show_projects():
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).filter(Project.user == current_user)
    return render_template("projects.html", title="Projects", projects=projects)


@app.route("/add_project", methods=["GET", "POST"])
@login_required
def add_project():
    db_sess = db_session.create_session()
    form = AddProject()

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        project = Project(
            name=form.name.data,
            user=user
        )

        db_sess.add(project)
        db_sess.commit()
        return redirect('/projects')

    return render_template('add_project.html', title='Add project', form=form)


@app.route("/project/<int:id>", methods=["GET", "POST"])
def info_of_project(id):
    db_sess = db_session.create_session()
    project = db_sess.query(Project).filter(Project.id == id, Project.user == current_user).first()

    if not project:
        return "Project not found"

    incomplete_tasks = db_sess.query(Task).filter(
        Task.completed == False,
        Task.project.contains(project), Task.user == current_user
    ).all()

    completed_tasks = db_sess.query(Task).filter(
        Task.completed == True, Task.user == current_user,
    Task.project.contains(project)
    ).all()

    return render_template("info_of_project.html", title=project.name, completed_tasks=completed_tasks,
                           incomplete_tasks=incomplete_tasks, project=project)


@app.route("/produs_api")
def get_api():
    if current_user.is_authenticated:
        user_api = current_user.api
        return render_template("produs_api.html", user_api=user_api)


@app.route("/new_api")
def generate_new_api():
    if current_user.is_authenticated:
        new_api = generate_api_key(16)
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        user.api = new_api
        db_sess.merge(user)
        db_sess.commit()
        return redirect("produs_api")


if __name__ == "__main__":
    main()
