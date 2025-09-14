"""Insta485 package initializer."""
import flask
from flask import abort, send_from_directory, session
import os

# app is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name

# Read settings from config module (insta485/config.py)
app.config.from_object('insta485.config')

# Overlay settings read from a Python file whose path is set in the environment
# variable INSTA485_SETTINGS. Setting this environment variable is optional.
# Docs: http://flask.pocoo.org/docs/latest/config/
#
# EXAMPLE:
# $ export INSTA485_SETTINGS=secret_key_config.py
app.config.from_envvar('INSTA485_SETTINGS', silent=True)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files with login required."""
    # TODO: replace hardcoded login with session-based login
    #if "username" not in session:
       # abort(403)  # Forbidden if not logged in

    folder = str(app.config["UPLOAD_FOLDER"])
    path = os.path.join(folder, filename)

    if not os.path.isfile(path):
        abort(404)  # File not found

    return send_from_directory(folder, filename)

# Tell our app about views and model.  This is dangerously close to a
# circular import, which is naughty, but Flask was designed that way.
# (Reference http://flask.pocoo.org/docs/patterns/packages/)  We're
# going to tell pylint and pycodestyle to ignore this coding style violation.
import insta485.views  # noqa: E402  pylint: disable=wrong-import-position
import insta485.model  # noqa: E402  pylint: disable=wrong-import-position

