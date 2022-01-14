from pyramid.config import Configurator


def main(global_config, **settings):
    """Build the pyramid WSGI App."""
    with Configurator(settings=settings) as config:
        config.add_route("notify_v1", "/v1/notification")
        config.add_route("prom_metrics", "/metrics")
        config.scan(".views")

        app = config.make_wsgi_app()
        return app
