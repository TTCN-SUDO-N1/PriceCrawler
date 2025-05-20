from flask_restx import Resource, Namespace
from flask import send_from_directory, current_app
import os

ns = Namespace("")

@ns.route("/")
class Hello (Resource):
    def get(self):
        return send_from_directory(
            os.path.dirname(os.path.abspath(__file__)),
            "main.html",
        )
