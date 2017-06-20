from flask_login import logout_user

from . import api


@api.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return ('', 204)

