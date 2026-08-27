"""To'lov qatlami: Click protokoli va uni qabul qiladigan HTTP server."""
from . import click
from .webapp import run_server

__all__ = ["click", "run_server"]
