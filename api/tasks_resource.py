from flask import jsonify
from flask_restful import Resource, abort
from api.parser_api import parser_tasks, parser_edited_tasks
from data.units import abort_if_users_not_found, abort_if_project_not_found
from data import db_session
from data.users import User
from data.tasks import Task
from data.projects import Project
from sqlalchemy import func
from datetime import datetime
from sqlalchemy.orm import joinedload


class TaskResource(Resource):
    def get(self, user_api, args):
        abort_if_users_not_found(user_api)
        args = args.split("/")
        session = db_session.create_session()
        user = session.query(User).filter(User.api == user_api).first()
        title = None
        tasks = []
        if args[0] == "all":
            title = "all"
            tasks = session.query(Task).filter(Task.user_id == user.id).all()

        if args[0] == "today":
            title = "today"
            tasks = session.query(Task).filter(Task.user_id == user.id,
                                               func.date(Task.deadline) == datetime.now().date()).all()
        if args[0].isdigit():
            try:
                task_id = int(args[0])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid task ID'})
            tasks = [session.query(Task).get(task_id)]
            if not tasks[0]:
                return jsonify({'error': 'not found task'})
            title = f"Id {task_id}"

        if args[0] == "tasks_from_project":
            project_id = args[1]
            try:
                project_id = int(project_id)
            except Exception as e:
                pass
            print(args)
            abort_if_project_not_found(project_id)
            tasks = session.query(Task).join(Task.project).filter(Project.id == project_id,  Task.user == user).all()
            project = session.query(Project).get(project_id)
            title = "project"

        if title and tasks:
            return jsonify({
                f'{title} task': [
                    {
                        'id': task.id,
                        'name': task.name,
                        'description': task.description,
                        'deadline': task.deadline,
                        'reminders': task.reminders,
                        'completed': task.completed,
                        'project_names': task.project[0].name if task.project else None
                    } for task in tasks
                ]
            })
        else:
            return jsonify({'status': 'bad request'})

    def post(self, user_api, args):
        abort_if_users_not_found(user_api)
        args = args.split("/")
        if args[0] == "new_task":
            session = db_session.create_session()
            user = session.query(User).filter(User.api == user_api).first()
            parsed_args = parser_tasks.parse_args()
            deadline_date = datetime.strptime(parsed_args["deadline"], "%Y-%m-%d").date()
            reminders_date = ""
            if parsed_args["reminders"]:
                reminders_date = datetime.strptime(parsed_args["reminders"], "%Y-%m-%dT%H:%M").date()

            if deadline_date < datetime.now().date():
                return jsonify({"error": "The deadline should be set for today or later. Please change the date."})

            if reminders_date and reminders_date < datetime.now().date():
                return jsonify({"error": "The reminder must be set for today or later. Please change the date."})

            if reminders_date and reminders_date > deadline_date:
                return jsonify(
                    {"error": "The reminder must be set before the deadline. Please change the reminder."})

            if parsed_args["project"]:
                abort_if_project_not_found(parsed_args["project"])
            task = Task()
            task.name = parsed_args["name"]
            task.description = parsed_args["description"]
            if not parsed_args["description"]:
                task.description = ""
            task.deadline = deadline_date
            task.reminders = reminders_date
            task.user = user
            session.add(task)
            project = session.query(Project).filter(Project.name == parsed_args["project"]).first()
            if project:
                task.project.append(project)

            session.commit()

            return jsonify({"task id": task.id})

        if args[0] == "close":
            try:
                task_id = int(args[1])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid task ID'})
            session = db_session.create_session()
            task = session.query(Task).get(task_id)
            print(task)
            if not task:
                return jsonify({'status': 'not found task'})
            task.completed = True
            session.merge(task)
            session.commit()
            return jsonify({'success': 'OK'})


        if args[0] == "reopen":
            try:
                task_id = int(args[1])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid task ID'})
            session = db_session.create_session()
            task = session.query(Task).get(task_id)
            if not task:
                return jsonify({'status': 'not found task'})
            task.completed = False
            session.merge(task)
            session.commit()
            return jsonify({'success': 'OK'})

        if args[0] == "edit":
            try:
                task_id = int(args[1])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid task ID'})

            session = db_session.create_session()
            task = session.query(Task).get(task_id)
            if not task:
                return jsonify({'status': 'not found'})

            parsed_args = parser_edited_tasks.parse_args()
            if "name" in parsed_args and parsed_args["name"]:
                task.name = parsed_args["name"]
            if "description" in parsed_args:
                task.description = parsed_args["description"] if parsed_args["description"] else ""
            if "deadline" in parsed_args:
                deadline_date = datetime.strptime(parsed_args["deadline"], "%Y-%m-%d").date()
                if deadline_date < datetime.now().date():
                    return jsonify({"error": "The deadline should be set for today or later. Please change the date."})
                task.deadline = deadline_date
            if "reminders" in parsed_args and parsed_args["reminders"]:
                reminders_date = datetime.strptime(parsed_args["reminders"], "%Y-%m-%dT%H:%M").date()
                if reminders_date < datetime.now().date():
                    return jsonify({"error": "The reminder must be set for today or later. Please change the date."})
                if reminders_date > task.deadline:
                    return jsonify(
                        {"error": "The reminder must be set before the deadline. Please change the reminder."})
                task.reminders = reminders_date

            if "project" in parsed_args and parsed_args["project"]:
                abort_if_project_not_found(parsed_args["project"])
                project = session.query(Project).filter(Project.name == parsed_args["project"]).first()
                if project:
                    task.project.clear()
                    task.project.append(project)

            session.commit()
            return jsonify({'success': 'Task updated successfully', 'task_id': task.id})
        else:
            return jsonify({'status': 'bad request'})

    def delete(self, user_api, args):
        abort_if_users_not_found(user_api)
        task_id = args.split("/")[0]
        session = db_session.create_session()
        task = session.query(Task).get(task_id)
        if not task:
            return jsonify({'error': 'not found task'})
        session.delete(task)
        session.commit()
        return jsonify({'success': 'OK'})


