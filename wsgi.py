"""WSGI entrypoint for compatible hosting environments."""

from casino_calendar.dash_app import create_dash_app

app, server = create_dash_app()
application = server
