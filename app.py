from NewApp import create_app
from flask import send_from_directory, current_app
import os

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)