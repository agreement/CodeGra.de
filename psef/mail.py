import html
import typing as t

import html2text
from flask import current_app
from flask_mail import Mail, Message

import psef
import psef.models as models
from psef.errors import APICodes, APIException
from psef.models import db

mail = Mail()


def send_reset_password_email(user: models.User) -> None:
    token = user.get_reset_token()
    html_body = current_app.config['EMAIL_TEMPLATE'].replace(
        '\n\n', '<br><br>'
    ).format(
        site_url=current_app.config["EXTERNAL_URL"],
        url=f'{psef.app.config["EXTERNAL_URL"]}/reset_'
        f'password/?user={user.id}&token={token}',
        user_id=user.id,
        token=token,
        user_name=html.escape(user.name),
        user_email=html.escape(user.email),
    )
    text_maker = html2text.HTML2Text(bodywidth=78)
    text_maker.inline_links = False
    text_maker.wrap_links = False

    message = Message(
        subject=f'Reset password on {psef.app.config["EXTERNAL_URL"]}',
        body=text_maker.handle(html_body),
        html=html_body,
        recipients=[user.email],
    )
    try:
        mail.send(message)
    except:
        raise APIException(
            'Something went wrong sending the email, '
            'please contact your site admin',
            f'Sending email to {user.id} went wrong.',
            APICodes.UNKOWN_ERROR,
            500,
        )


def init_app(app: t.Any) -> None:
    mail.init_app(app)
