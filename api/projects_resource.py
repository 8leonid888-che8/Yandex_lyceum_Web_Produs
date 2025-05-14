from flask import jsonify
from flask_restful import Resource, abort
from api.parser_api import parser_projects, parser_edited_projects
from data.units import abort_if_users_not_found, abort_if_project_not_found
from data import db_session
from data.users import User
from data.projects import Project


class ProjectResource(Resource):
    def get(self, user_api, args):
        abort_if_users_not_found(user_api)
        args = args.split("/")
        session = db_session.create_session()
        user = session.query(User).filter(User.api == user_api).first()
        title = None
        projects = []
        if args[0] == "all":
            title = "all"
            projects = session.query(Project).filter(Project.user_id == user.id).all()

        if args[0].isdigit():
            try:
                project_id = int(args[0])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid project ID'})
            projects = [session.query(Project).get(project_id)]
            print(projects)
            if not projects[0]:
                return jsonify({'error': 'not found project'})
            title = f"Id {project_id}"

        if title and projects:
            return jsonify({
                f'{title} project': [
                    {
                        'name': project.name,
                    } for project in projects
                ]
            })
        else:
            return jsonify({'status': 'bad request'})

    def post(self, user_api, args):
        abort_if_users_not_found(user_api)
        args = args.split("/")
        if args[0] == "new_project":
            session = db_session.create_session()
            user = session.query(User).filter(User.api == user_api).first()
            parsed_args = parser_projects.parse_args()

            project = Project()
            project.name = parsed_args["name"]
            project.user = user
            session.add(project)
            session.commit()

            return jsonify({"project id": project.id})

        if args[0] == "edit":
            try:
                project_id = int(args[1])
            except Exception as e:
                print(e)
                return jsonify({'error': 'Invalid project ID'})

            session = db_session.create_session()
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({'status': 'not found project'})

            parsed_args = parser_edited_projects.parse_args()
            if "name" in parsed_args and parsed_args["name"]:
                project.name = parsed_args["name"]
            session.merge(project)
            session.commit()
            return jsonify({'success': 'Task updated successfully', 'project id': project.id})
        else:
            return jsonify({'status': 'bad request'})

    def delete(self, user_api, args):
        abort_if_users_not_found(user_api)
        project_id = args.split("/")[0]
        session = db_session.create_session()
        project = session.query(Project).get(project_id)
        if not project:
            return jsonify({'error': 'not found project'})
        session.delete(project)
        session.commit()
        return jsonify({'success': 'OK'})
