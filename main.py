from flask import Flask, render_template, redirect, flash, request, abort
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
    incomplete_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(),
                                                  Task.completed == False).all()
    completed_tasks = db_sess.query(Task).filter(func.date(Task.deadline) == datetime.now().date(),
                                                 Task.completed == True).all()
    return render_template("index.html", title="Today", incomplete_tasks=incomplete_tasks,
                           completed_tasks=completed_tasks)


@app.route('/edit/<string:page>/<string:obj>/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_obj(page, obj, id):
    if obj in "task":
        db_sess = db_session.create_session()
        projects = db_sess.query(Project).all()
        form = AddTask()
        if request.method == "GET":
            db_sess = db_session.create_session()
            task = db_sess.query(Task).filter(Task.id == id, Task.user == current_user).first()
            if task:
                form.name.data = task.name
                form.description.data = task.description
                form.deadline.data = task.deadline
                form.reminders.data = task.reminders
                form.project.data = task.project

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
                db_sess.merge(task)
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
    return render_template("all_tasks.html", title="All tasks", incomplete_tasks=incomplete_tasks,
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


@app.route("/projects", methods=["GET", "POST"])
def show_projects():
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).all()
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
    project = db_sess.query(Project).filter(Project.id == id).first()

    if not project:
        return "Project not found", 404  # Handle case where project is not found

    # Get incomplete tasks associated with the project
    incomplete_tasks = db_sess.query(Task).filter(
        Task.completed == False,
        Task.project.contains(project)  # Use contains() for membership check
    ).all()

    # Get completed tasks associated with the project
    completed_tasks = db_sess.query(Task).filter(
        Task.completed == True,
        Task.project.contains(project)  # Use contains() for membership check
    ).all()

    return render_template("info_of_project.html", title=project.name, completed_tasks=completed_tasks,
                           incomplete_tasks=incomplete_tasks)


if __name__ == "__main__":
    main()