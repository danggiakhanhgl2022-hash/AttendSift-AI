"""WSGI entrypoint for cloud hosting (not the Windows desktop launcher)."""
from cloud.app import create_app

app = create_app()
