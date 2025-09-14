"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485
import arrow


@insta485.app.route('/')
def show_index():
    """Display / route."""

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    ## POSSIBLY REPLACE LATER!!!!
    logname = "awdeorio"
    cur = connection.execute(
    "SELECT posts.postid, posts.filename AS post_filename, "
    "posts.owner, posts.created, users.fullname, "
    "users.filename AS user_filename "
    "FROM posts "
    "JOIN users ON posts.owner = users.username "
    "WHERE posts.owner = ? "
    "OR posts.owner IN (SELECT followee FROM following WHERE follower = ?) "
    "ORDER BY posts.postid DESC",
    (logname, logname)
    )
    posts = cur.fetchall()

    for post in posts:
        postid = post["postid"]
        
        post["humanized"] = arrow.get(post["created"]).humanize()

        # Likes count
        cur = connection.execute(
            "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
            (postid,)
        )
        post["likes"] = cur.fetchone()["like_count"]

        # Comments
        cur = connection.execute(
            "SELECT owner, text FROM comments WHERE postid = ? ORDER BY created ASC",
            (postid,)
        )
        post["comments"] = cur.fetchall()

    # Add database info to context
    context = {"logname": logname, "posts": posts}
    return flask.render_template("index.html", **context)