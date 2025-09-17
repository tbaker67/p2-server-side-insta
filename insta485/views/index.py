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
    #if "logname" not in session:
        #abort(403)

    folder = str(insta485.app.config["UPLOAD_FOLDER"])
    path = os.path.join(folder, filename)

    if not os.path.isfile(path):
        abort(404)  # File not found

    return send_from_directory(folder, filename)


@insta485.app.route('/')
def show_index():
    """Display / route."""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']
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

    liked_posts = connection.execute(
        "SELECT postid FROM likes WHERE owner = ?",
        (logname,)
    ).fetchall()
    liked_postids = {row["postid"] for row in liked_posts}

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
            "SELECT owner, text, commentid "
            "FROM comments "
            "WHERE postid = ? ORDER BY commentid ASC",
            (postid,)
        ).fetchall()
        post["liked"] = post["postid"] in liked_postids

    # Add database info to context
    context = {"logname": logname, "posts": posts}
    return flask.render_template("index.html", **context)


@insta485.app.route('/users/<user_url_slug>/')


def show_users(user_url_slug):
    """Show user page"""

    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))
    
    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']

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
    """Show following page"""

    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']

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
    """show followers page"""

    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']

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
    """show post page"""

    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))
    
    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']

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

    liked = False

    like_query = connection.execute(
        "SELECT 1 FROM likes "
        "WHERE owner = ? AND "
        "postid = ?",
        (logname, postid)
    ).fetchone()

    if like_query:
        liked=True

    post["liked"] = liked

    # Add database info to context
    context = {"logname": logname, "post": post}
    return flask.render_template("post.html", **context)


@insta485.app.route('/explore/')
def show_explore():
    """Show explore page"""

    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    connection = insta485.model.get_db()
    # TODO: REPLACE WITH LOGNAME LATER!!!!
    logname = session['logname']

    not_following_rows = connection.execute(
        "SELECT users.username " 
        "FROM users "
        "WHERE users.username != ? "
        "AND username NOT IN "
        "(SELECT following.followee " 
        "FROM following " 
        "WHERE following.follower = ?)",
        (logname,logname)
    ).fetchall()

    not_following = []
    for row in not_following_rows:
        username = row["username"]
        user = connection.execute(
            "SELECT filename AS user_filename "
            "FROM users "
            "WHERE username = ?",
            (username,)
        ).fetchone()
        user_filename = user["user_filename"]
        not_following.append({'username': username, 'user_filename': user_filename})


    context = {'logname': logname, 'not_following': not_following}
    return flask.render_template('explore.html', **context)

@insta485.app.route('/accounts/login/')
def show_login():
    """Show accounts/ login page"""
    if 'logname' in session:
        return flask.redirect(flask.url_for('show_index'))
    else:
        return flask.render_template('login.html')


@insta485.app.route('/accounts/create/')
def show_create():
    """show accounts/create page"""
    if 'logname' in session:
        return flask.redirect(flask.url_for('show_edit'))
    else:
        return flask.render_template('create.html')

@insta485.app.route('/accounts/delete/')
def show_delete():
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))
    else:
        return flask.render_template('delete.html', logname=session['logname'])


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Show accounts/edit page"""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))

    else:
        logname = session['logname']
        connection = insta485.model.get_db()

        user_info = connection.execute(
            "SELECT username, fullname, "
            "email, filename AS user_filename "
            "FROM users "
            "Where username = ?",
            (logname,)
        ).fetchone()

        context = {'logname': logname, 'user_info': user_info}
        return flask.render_template('edit.html', **context)
    
@insta485.app.route('/accounts/password/')
def show_password():
    """Show accounts/delete page"""
    if 'logname' not in session:
        return flask.redirect(flask.url_for('show_login'))
    else:
        return flask.render_template('password.html', logname=session['logname'])

@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """Log out user and redirect to login page."""

    session.clear()
    return flask.redirect(flask.url_for('show_login'))
        
import hashlib


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """Perform account operations and redirect."""

    operation = flask.request.form.get('operation')
    target = flask.request.args.get('target', flask.url_for('show_index'))

    if operation == "login":
        # TODO: handle login (check username/password, set session)

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
        else:
            session['logname'] = username

        

    elif operation == "create":
        # TODO: handle account creation
        pass

    elif operation == "delete":
        # TODO: handle account deletion
        pass

    elif operation == "edit_account":
        # TODO: handle account editing
        pass

    elif operation == "update_password":
        # TODO: handle password update
        pass

    elif operation == "logout":
        # TODO: handle logout
        pass

    else:
        # Invalid operation
        abort(400)

    # Finally redirect to target
    return flask.redirect(target)