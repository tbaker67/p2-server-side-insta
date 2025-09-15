"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485
import arrow
from flask import abort, send_from_directory, session
import os


@insta485.app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files with login required."""
    # TODO: replace hardcoded login with session-based login
    # if "username" not in session:
    # abort(403)

    folder = str(insta485.app.config["UPLOAD_FOLDER"])
    path = os.path.join(folder, filename)

    if not os.path.isfile(path):
        abort(404)  # File not found

    return send_from_directory(folder, filename)


@insta485.app.route('/')
def show_index():
    """Display / route."""

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = "awdeorio"
    posts = connection.execute(
        "SELECT posts.postid, posts.filename AS post_filename, "
        "posts.owner, posts.created, users.fullname, "
        "users.filename AS user_filename "
        "FROM posts "
        "JOIN users ON posts.owner = users.username "
        "WHERE posts.owner = ? "
        "OR posts.owner IN "
        "(SELECT followee FROM following WHERE follower = ?) "
        "ORDER BY posts.postid DESC",
        (logname, logname)
    ).fetchall()

    for post in posts:
        postid = post["postid"]
        post["humanized"] = arrow.get(post["created"]).humanize()
        # Likes count
        post["likes"] = connection.execute(
            "SELECT COUNT(*) AS like_count FROM likes "
            "WHERE postid = ?",
            (postid,)
        ).fetchone()["like_count"]
        # Comments
        post["comments"] = connection.execute(
            "SELECT owner, text "
            "FROM comments "
            "WHERE postid = ? ORDER BY commentid ASC",
            (postid,)
        ).fetchall()
    # Add database info to context
    context = {"logname": logname, "posts": posts}
    return flask.render_template("index.html", **context)


@insta485.app.route('/users/<user_url_slug>/')
# TODO: ADD IN EDIT PROFILE, LOGOUT, AND MAKE POST
def show_users(user_url_slug):

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = "awdeorio"

    user = connection.execute(
        "SELECT username, fullname FROM users WHERE username = ?",
        (user_url_slug,)
    ).fetchone()

    if user is None:
        abort(404)

    logname_follows_username = False
    if logname != user_url_slug:
        follow = connection.execute(
            "SELECT 1 FROM following "
            "WHERE follower = ? and followee = ?",
            (logname, user_url_slug)
        ).fetchone()
        if follow:
            logname_follows_username = True

    total_posts = connection.execute(
        "SELECT COUNT(*) AS count FROM posts WHERE posts.owner = ?",
        (user_url_slug,)
    ).fetchone()["count"]

    followers = connection.execute(
        "SELECT COUNT(*) AS count FROM following WHERE followee = ?",
        (user_url_slug,)
    ).fetchone()["count"]

    following = connection.execute(
        "SELECT COUNT(*) AS count FROM following WHERE follower = ?",
        (user_url_slug,)
    ).fetchone()["count"]

    posts = connection.execute(
        "SELECT postid, filename "
        "AS post_filename "
        "FROM posts WHERE owner = ? "
        "ORDER BY postid DESC",
        (user_url_slug,)
    ).fetchall()

    context = {
        "logname": logname,
        "username": user["username"],
        "fullname": user["fullname"],

        "logname_follows_username": logname_follows_username,
        "total_posts": total_posts,
        "followers": followers,
        "following": following,

        "posts": posts
    }

    return flask.render_template("user.html", **context)


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = "awdeorio"

    user = connection.execute(
        "SELECT username, fullname FROM users WHERE username = ?",
        (user_url_slug,)
    ).fetchone()

    if user is None:
        abort(404)

    following_rows = connection.execute(
        "SELECT users.username, users.filename AS user_filename "
        "FROM following "
        "JOIN users ON following.followee = users.username "
        "WHERE following.follower = ?",
        (user_url_slug,)
    ).fetchall()

    following = []
    for row in following_rows:
        info = dict(row)
        # Determine relationship to logged-in user
        logname_follows_username = False
        if logname != row["username"]:
            follow = connection.execute(
                "SELECT 1 FROM following "
                "WHERE follower = ? AND followee = ?",
                (logname, row["username"])
            ).fetchone()
            if follow:
                logname_follows_username = True
        info["logname_follows_username"] = logname_follows_username
        following.append(info)

    context = {"logname": logname, "following": following}
    return flask.render_template("following.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/')
def show_followers(user_url_slug):

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = "awdeorio"

    user = connection.execute(
        "SELECT username, fullname FROM users WHERE username = ?",
        (user_url_slug,)
    ).fetchone()

    if user is None:
        abort(404)

    follower_rows = connection.execute(
        "SELECT users.username, users.filename AS user_filename "
        "FROM following "
        "JOIN users ON following.follower = users.username "
        "WHERE following.followee = ?",
        (user_url_slug,)
    ).fetchall()

    followers = []
    for row in follower_rows:
        info = dict(row)
        # Determine relationship to logged-in user
        logname_follows_username = False
        if logname != row["username"]:
            follow = connection.execute(
                "SELECT 1 FROM following "
                "WHERE follower = ? AND followee = ?",
                (logname, row["username"])
            ).fetchone()
            if follow:
                logname_follows_username = True
        info["logname_follows_username"] = logname_follows_username
        followers.append(info)

    context = {"logname": logname, "followers": followers}
    return flask.render_template("followers.html", **context)


@insta485.app.route('/posts/<postid_url_slug>/')
def show_post(postid_url_slug):
    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = "awdeorio"

    post = connection.execute(
        "SELECT postid, filename AS post_filename, "
        "owner, created "
        "FROM posts WHERE postid = ?",
        (postid_url_slug,)
    ).fetchone()

    if post is None:
        abort(404)

    user = connection.execute(
        "SELECT filename AS user_filename "
        "FROM users WHERE username = ?",
        (post["owner"],)
    ).fetchone()

    post["user_filename"] = user["user_filename"]

    postid = post["postid"]
    post["humanized"] = arrow.get(post["created"]).humanize()
    # Likes count
    post["likes"] = connection.execute(
        "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
        (postid,)
    ).fetchone()["like_count"]
    # Comments
    post["comments"] = connection.execute(
        "SELECT owner, text FROM comments "
        "WHERE postid = ? ORDER BY commentid ASC",
        (postid,)
    ).fetchall()

    # Add database info to context
    context = {"logname": logname, "post": post}
    return flask.render_template("post.html", **context)


@insta485.app.route('/explore/')
def show_explore():
    pass
