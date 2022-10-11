import email as emaillib
import json
import smtplib
from textwrap import dedent

from blacksmith import HTTPError
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery
from notif.resources.user import User
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from pyramid.response import Response
from pyramid.view import view_config

smtp_sd = SyncConsulDiscovery()


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


@view_config(route_name="notify_v1", renderer="json")
def post_notif(request):
    if request.method == "GET":
        return {"detail": "Use POST to test the consul driver"}

    body = request.json
    api_user = request.blacksmith.client("api_user")
    user: User = (api_user.users.get({"username": body["username"]})).unwrap()
    send_email(user, body["message"])
    return {"detail": f"{user.email} accepted"}


@view_config(route_name="prom_metrics")
def get_metrics(request):
    resp = Response(content_type=CONTENT_TYPE_LATEST, body=generate_latest(REGISTRY))
    return resp


@view_config(context=HTTPError)
def failed_validation(exc: HTTPError, request):
    # If the view has two formal arguments, the first is the context.
    # The context is always available as ``request.context`` too.
    response = Response(json.dumps(exc.response.json))
    response.status_int = exc.status_code
    return response
