"""insta485 accounts views"""
import pathlib
import hashlib
import uuid
import flask
from flask import abort, session
import insta485

@insta485.app.route('/accounts/login/')
def show_login():
    """Show accounts/ login page"""
    if 'logname' in session:
        return flask.redirect(flask.url_for('show_index'))

    return flask.render_template('login.html')


@insta485.app.route('/accounts/create/')
def show_create():
    """show accounts/create page"""
    if 'logname' in session:
        return flask.redirect(flask.url_for('show_edit'))
    return flask.render_template('create.html')


@insta485.app.route('/accounts/delete/')
def show_delete():
    """show acounts deletion page"""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    return flask.render_template('delete.html', logname=session['logname'])


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Show accounts/edit page"""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    logname = session['logname']
    connection = insta485.model.get_db()

    user_info_row = connection.execute(
        "SELECT username, fullname, "
        "email, filename AS user_filename "
        "FROM users "
        "Where username = ?",
        (logname,)
    ).fetchone()

    context = {
        'logname': logname, 
        'username': user_info_row['username'],
        'fullname': user_info_row['fullname'],
        'email': user_info_row['email'],
        'user_filename': user_info_row['user_filename']
        }
    return flask.render_template('edit.html', **context)


@insta485.app.route('/accounts/password/')
def show_password():
    """Show accounts/delete page"""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    return flask.render_template('password.html', logname=session['logname'])

@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """Log out user and redirect to login page."""

    session.clear()

    return flask.redirect(flask.url_for('show_login'))


def create_password(password):
    """Create a hashed and salted password to store in the db"""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def create_file(fileobj):
    """create a uuid file for the db and return the new filename"""

    if fileobj is None:
        abort(400)
    filename = fileobj.filename

    # Compute base name (filename without directory).  We use a UUID to avoid
    # clashes with existing files, and ensure that the name is compatible with the
    # filesystem. For best practive, we ensure uniform file extensions (e.g.
    # lowercase).

        
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"

    # Save to disk
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    fileobj.save(path)
    return uuid_basename


def login_account(target):
    """handle login post requests"""
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')


    if not username or not password:
        abort(400)

    connection = insta485.model.get_db()

    login_info = connection.execute(
        "SELECT password "
        "FROM users "
        "WHERE username = ?",
        (username,)
    ).fetchone()

    # No matching username
    if login_info is None:
        abort(403)

    algorithm, salt, true_hashed_password = login_info['password'].split('$',2)

    m = hashlib.new(algorithm)
    password_salted = salt + password
    m.update(password_salted.encode('utf-8'))
    password_hash = m.hexdigest()

    if password_hash != true_hashed_password:
        abort(403)

    session['logname'] = username
    return flask.redirect(target)


def create_account(target):
    """handle account creation"""
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    email = flask.request.form.get('email')
    fullname = flask.request.form.get('fullname')
    file = flask.request.files["file"]

    if not username or not password or not fullname or not file or not email:
        abort(400)

    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT * "
        "FROM users "
        "WHERE username = ?",
        (username,)
    ).fetchone()

    if user is not None:
        abort(409)

    password_db_string = create_password(password)
    filename = create_file(file)

    connection.execute(
        "INSERT INTO "
        "users(username, fullname, email, filename, password) "
        "VALUES (?, ?, ?, ?, ?)",
        (username, fullname, email, filename, password_db_string)
    )

    session['logname'] = username
    return flask.redirect(target)

def delete_account(target):
    """handle account deletion post requests from the form"""
    if 'logname' not in session:
        abort(403)

    logname = session['logname']
    connection = insta485.model.get_db()

    post_file_rows = connection.execute(
        "SELECT filename "
        "FROM posts "
        "WHERE owner = ?",
        (logname,)
    ).fetchall()

    for post_file_row in post_file_rows:
        filepath = pathlib.Path(
            insta485.app.config["UPLOAD_FOLDER"]
        ) / post_file_row["filename"]
        if filepath.is_file():
            filepath.unlink()

    user_file_rows = connection.execute(
        "SELECT filename "
        "FROM users "
        "WHERE username = ?",
        (logname,)
    ).fetchall()

    for user_file_row in user_file_rows:
        filepath = pathlib.Path(
            insta485.app.config["UPLOAD_FOLDER"]
        ) / user_file_row["filename"]
        if filepath.is_file():
            filepath.unlink()

    connection.execute(
        "DELETE FROM users WHERE username = ?", (logname,)
    )

    session.clear()
    return flask.redirect(target)

def edit_account(target):
    """handle account editing"""
    if 'logname' not in session:
        abort(403)
    logname = session['logname']

    email = flask.request.form.get('email')
    fullname = flask.request.form.get('fullname')
    file = flask.request.files.get("file")
    if not email or not fullname:
        abort(400)

    connection = insta485.model.get_db()

    if file:
        # get old filename
        filename_to_delete = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (logname,)
        ).fetchone()['filename']

        # delete old file
        filepath = pathlib.Path(
            insta485.app.config["UPLOAD_FOLDER"]
        ) / filename_to_delete
        if filepath.is_file():
            filepath.unlink()

        # upload new profile pic and update database
        filename = create_file(file)
        connection.execute(
            "UPDATE users "
            "SET filename = ? "
            "WHERE username = ?",
            (filename, logname)
        )

    connection.execute(
            "UPDATE users "
            "SET email = ?, fullname = ? "
            "WHERE username = ?",
            (email, fullname , logname)
        )

    return flask.redirect(target)

def update_password_account(target):
    """handle password update post requests from the form"""
    if 'logname' not in session:
        abort(403)

    logname = session['logname']
    password = flask.request.form.get('password')
    new_password1 = flask.request.form.get('new_password1')
    new_password2 = flask.request.form.get('new_password2')

    if not password or not new_password1 or not new_password2:
        abort(400)
    connection = insta485.model.get_db()

    login_info = connection.execute(
        "SELECT password "
        "FROM users "
        "WHERE username = ?",
        (logname,)
    ).fetchone()


    algorithm, salt, true_hashed_password = login_info['password'].split('$',2)

    m = hashlib.new(algorithm)
    password_salted = salt + password
    m.update(password_salted.encode('utf-8'))
    password_hash = m.hexdigest()

    if password_hash != true_hashed_password:
        abort(403)

    if new_password1 != new_password2:
        abort(401)

    password_db = create_password(new_password1)

    connection.execute(
        "UPDATE users "
        "SET password = ? "
        "WHERE username = ?",
        (password_db,logname)
    )

    return flask.redirect(target)



@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """Perform account operations and redirect."""

    operation = flask.request.form.get('operation')
    target = flask.request.args.get('target', flask.url_for('show_index'))

    if operation == "login":
        return login_account(target)

    if operation == "create":
        return create_account(target)

    if operation == "delete":
        return delete_account(target)

    if operation == "edit_account":
        return edit_account(target)

    if operation == "update_password":
        return update_password_account(target)


    # Invalid operation
    abort(400)


@insta485.app.route('/accounts/auth/')
def show_auth():
    if 'logname' not in session:
        abort(403)
    return flask.Response(status=200)