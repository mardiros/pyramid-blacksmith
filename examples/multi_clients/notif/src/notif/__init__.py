import email as emaillib
import smtplib
from textwrap import dedent

from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery
from notif.resources.user import User
from pyramid.config import Configurator

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


def post_notif_using_static(request):
    if request.method == "GET":
        return {"detail": "Use POST to test the static driver"}

    body = request.json
    api_user = request.blacksmith.client_static("api_user")
    user: User = (api_user.users.get({"username": body["username"]})).response
    send_email(user, body["message"])
    return {"detail": f"{user.email} accepted"}


def post_notif_using_consul(request):
    if request.method == "GET":
        return {"detail": "Use POST to test the consul driver"}

    body = request.json
    api_user = request.blacksmith.client_consul("api_user")
    user: User = (api_user.users.get({"username": body["username"]})).response
    send_email(user, body["message"])
    return {"detail": f"{user.email} accepted"}


def post_notif_using_router(request):
    if request.method == "GET":
        return {"detail": "Use POST to test the router driver"}

    body = request.json
    api_user = request.blacksmith.client_router("api_user")
    user: User = (api_user.users.get({"username": body["username"]})).response
    send_email(user, body["message"])
    return {"detail": f"{user.email} accepted"}


def main(global_config, **settings):
    """Build the pyramid WSGI App."""
    with Configurator(settings=settings) as config:

        config.add_route("notify_v1", "/v1/notification")
        config.add_view(
            post_notif_using_consul, route_name="notify_v1", renderer="json"
        )

        config.add_route("notify_v2", "/v2/notification")
        config.add_view(
            post_notif_using_consul, route_name="notify_v2", renderer="json"
        )

        config.add_route("notify_v3", "/v3/notification")
        config.add_view(
            post_notif_using_router, route_name="notify_v3", renderer="json"
        )

        app = config.make_wsgi_app()
        return app
