"""Handle Requests for follow, commment, post buttons."""
import pathlib
import flask
from flask import session, abort
import insta485
from insta485.views.accounts import create_file

LOGGER = flask.logging.create_logger(insta485.app)


def like(target, postid, logname):
    """Like a post."""
    connection = insta485.model.get_db()

    liked_row = connection.execute(
        "SELECT * "
        "FROM likes "
        "WHERE owner = ? AND postid = ?",
        (logname, postid)
    ).fetchone()

    if liked_row:
        abort(409)

    connection.execute(
        "INSERT INTO "
        "likes(owner, postid) "
        "VALUES (?, ?)",
        (logname, postid)
    )

    return flask.redirect(target)


def unlike(target, postid, logname):
    """Unlike a post."""
    connection = insta485.model.get_db()
    liked_row = connection.execute(
        "SELECT * "
        "FROM likes "
        "WHERE owner = ? AND postid = ?",
        (logname, postid)
    ).fetchone()

    if not liked_row:
        abort(409)

    connection.execute(
        "DELETE "
        "FROM likes "
        "WHERE owner = ? AND postid = ?",
        (logname, postid)
    )

    return flask.redirect(target)


@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    """Handle likes post requests."""
    LOGGER.debug("operation = %s", flask.request.form["operation"])
    LOGGER.debug("postid = %s", flask.request.form["postid"])

    logname = session.get('logname')
    if logname is None:
        abort(403)

    target = flask.request.args.get('target', flask.url_for('show_index'))
    operation = flask.request.form.get("operation")
    postid = int(flask.request.form.get("postid"))

    if operation == 'like':
        return like(target, postid, logname)

    return unlike(target, postid, logname)


def create_comment(target, logname):
    """Create a comment."""
    text = flask.request.form.get('text')
    postid = int(flask.request.form.get('postid'))

    if not text:
        abort(400)

    connection = insta485.model.get_db()
    connection.execute(
        "INSERT INTO "
        "comments(owner, postid, text) "
        "VALUES (?, ?, ?)",
        (logname, postid, text)
    )

    return flask.redirect(target)


def delete_comment(target, logname):
    """Delete a comment."""
    commentid = int(flask.request.form["commentid"])

    connection = insta485.model.get_db()
    comment_row = connection.execute(
        "SELECT 1 FROM comments WHERE commentid = ? AND owner = ?",
        (commentid, logname)
    ).fetchone()

    if comment_row is None:
        abort(403)

    connection.execute(
        "DELETE FROM comments WHERE commentid = ? AND owner = ?",
        (commentid, logname)
    )

    return flask.redirect(target)


@insta485.app.route("/comments/", methods=["POST"])
def update_comments():
    """Update comments via Post request."""
    LOGGER.debug("operation = %s", flask.request.form["operation"])

    target = flask.request.args.get('target', flask.url_for('show_index'))
    operation = flask.request.form.get('operation')

    logname = session.get('logname')
    if logname is None:
        abort(403)

    if operation == 'create':
        return create_comment(target, logname)

    if operation == 'delete':
        return delete_comment(target, logname)

    abort(400)


def create_post(target, logname):
    """Create a post."""
    file = flask.request.files.get('file')
    filename = create_file(file)

    connection = insta485.model.get_db()
    connection.execute(
        "INSERT into posts(filename, owner) "
        "VALUES (?, ?)",
        (filename, logname)
    )

    return flask.redirect(target)


def delete_post(target, logname):
    """Delete a post."""
    postid = flask.request.form.get('postid')

    connection = insta485.model.get_db()
    post_row = connection.execute(
        "SELECT owner, filename "
        "FROM posts "
        "WHERE postid = ?",
        (postid,)
    ).fetchone()

    if not post_row or post_row['owner'] != logname:
        abort(403)

    filepath = pathlib.Path(
        insta485.app.config["UPLOAD_FOLDER"]) / post_row["filename"]
    if filepath.is_file():
        filepath.unlink()

    connection.execute(
        "DELETE FROM posts "
        "WHERE postid = ?",
        (postid,)
    )

    return flask.redirect(target)


@insta485.app.route('/posts/', methods=["POST"])
def update_post():
    """Update post via handling a POST request."""
    LOGGER.debug("operation = %s", flask.request.form["operation"])
    operation = flask.request.form.get('operation')
    logname = session.get('logname')
    target = flask.request.args.get(
        'target',
        flask.url_for('show_users', user_url_slug=logname)
    )

    if logname is None:
        abort(403)

    if operation == 'create':
        return create_post(target, logname)

    return delete_post(target, logname)


def follow(target, logname, username):
    """Make logname follow username."""
    connection = insta485.model.get_db()

    follow_row = connection.execute(
        "SELECT * "
        "FROM following "
        "WHERE follower = ? AND followee = ?",
        (logname, username)
    ).fetchone()

    if follow_row:
        abort(409)

    connection.execute(
        "INSERT INTO following (follower, followee) "
        "VALUES (?, ?)",
        (logname, username)
    )

    return flask.redirect(target)


def unfollow(target, logname, username):
    """Make logname unfollow username."""
    connection = insta485.model.get_db()

    follow_row = connection.execute(
        "SELECT * "
        "FROM following "
        "WHERE follower = ? AND followee = ?",
        (logname, username)
    ).fetchone()

    if not follow_row:
        abort(409)

    connection.execute(
        "DELETE FROM following "
        "WHERE follower = ? AND followee = ?",
        (logname, username)
    )

    return flask.redirect(target)


@insta485.app.route('/following/', methods=["POST"])
def update_following():
    """Update following via handling a POST request."""
    target = flask.request.args.get('target', flask.url_for('show_index'))
    logname = session.get('logname')
    username = flask.request.form.get('username')
    operation = flask.request.form.get('operation')

    if logname is None:
        abort(403)

    if operation == 'follow':
        return follow(target, logname, username)

    if operation == 'unfollow':
        return unfollow(target, logname, username)

    abort(400)
