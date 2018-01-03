"""
This module is used for all mailing related tasks.

:license: AGPLv3, see LICENSE for details.
"""
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


def _send_mail(
    html_body: str,
    subject: str,
    recipients: t.Sequence[str],
    mailer: t.Optional[Mail] = None,
) -> None:
    if mailer is None:
        mailer = mail

    text_maker = html2text.HTML2Text(bodywidth=78)
    text_maker.inline_links = False
    text_maker.wrap_links = False

    message = Message(
        subject=subject,
        body=text_maker.handle(html_body),
        html=html_body,
        recipients=recipients,
    )
    mailer.send(message)


def send_grade_reminder_email(
    assig: models.Assignment,
    user: models.User,
    mailer: Mail,
) -> None:
    html_body = current_app.config['REMINDER_TEMPLATE'].replace(
        '\n\n', '<br><br>'
    ).format(
        site_url=current_app.config['EXTERNAL_URL'],
        assig_id=assig.id,
        user_name=html.escape(user.name),
        user_email=html.escape(user.email),
        assig_name=html.escape(assig.name),
        course_id=assig.course_id,
    )
    _send_mail(
        html_body,
        (
            f'Grade reminder for {assig.name} on '
            f'{current_app.config["EXTERNAL_URL"]}'
        ),
        [user.email],
        mailer,
    )


def send_reset_password_email(user: models.User) -> None:
    token = user.get_reset_token()
    html_body = current_app.config['EMAIL_TEMPLATE'].replace(
        '\n\n', '<br><br>'
    ).format(
        site_url=current_app.config["EXTERNAL_URL"],
        url=(
            f'{current_app.config["EXTERNAL_URL"]}/reset_'
            f'password/?user={user.id}&token={token}'
        ),
        user_id=user.id,
        token=token,
        user_name=html.escape(user.name),
        user_email=html.escape(user.email),
    )
    try:
        _send_mail(
            html_body, f'Reset password on {psef.app.config["EXTERNAL_URL"]}',
            [user.email]
        )
    except Exception:
        raise APIException(
            'Something went wrong sending the email, '
            'please contact your site admin',
            f'Sending email to {user.id} went wrong.',
            APICodes.UNKOWN_ERROR,
            500,
        )


def init_app(app: t.Any) -> None:
    mail.init_app(app)
