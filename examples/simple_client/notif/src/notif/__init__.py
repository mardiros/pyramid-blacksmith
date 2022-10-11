import email as emaillib
import smtplib
from textwrap import dedent

from blacksmith import HTTPError, ResponseBox
from blacksmith.domain.error import AbstractErrorParser
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery
from notif.resources.user import User
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPException
from pyramid.response import Response

smtp_sd = SyncConsulDiscovery()


class ForwardPyramidHttpError(AbstractErrorParser[HTTPException]):
    def __call__(self, error: HTTPError) -> HTTPException:
        return HTTPException(error.json.get("detail", ""), code=error.status_code)


def send_email(user: User, message: str):
    email_content = dedent(
        f"""\
        Subject: notification
        From: notification@localhost
        To: "{user.firstname} {user.lastname}" <{user.email}>

        {message}
        """
    )
    msg = emaillib.message_from_string(email_content)

    srv = smtp_sd.resolve("smtp", None)
    # XXX Synchronous socket here, OK for the example
    # real code should use aiosmtplib
    s = smtplib.SMTP(srv.address, int(srv.port))
    s.send_message(msg)
    s.quit()


def post_notif(request):
    if request.method == "GET":
        return {"detail": "Use POST to test the consul driver"}

    body = request.json
    api_user = request.blacksmith.client("api_user")
    user: ResponseBox[User, HTTPException] = api_user.users.get(
        {"username": body["username"]}
    )
    if user.is_err():
        raise user.unwrap_err()

    send_email(user.unwrap(), body["message"])
    return {"detail": f"{user.email} accepted"}


def get_metrics(request):
    resp = Response(content_type=CONTENT_TYPE_LATEST, body=generate_latest(REGISTRY))
    return resp


def main(global_config, **settings):
    """Build the pyramid WSGI App."""
    with Configurator(settings=settings) as config:
        config.add_route("notify_v1", "/v1/notification")
        config.add_view(post_notif, route_name="notify_v1", renderer="json")

        config.add_route("prom_metrics", "/metrics")
        config.add_view(get_metrics, route_name="prom_metrics")

        app = config.make_wsgi_app()
        return app
