"""Views, one for each Insta485 page."""
from insta485.views.index import (
    show_index,
    show_users,
    show_followers,
    show_following,
    show_explore,
    show_post
)

from insta485.views.accounts import (
    show_login,
    show_create,
    show_delete,
    show_edit,
    show_password,
    create_file,
    accounts
    
    
)

from insta485.views.buttons import (
    update_likes,
    update_comments,
    update_post,
    update_following
)