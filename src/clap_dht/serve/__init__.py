from __future__ import annotations
import os
import argparse
from argparse import _SubParsersAction, ArgumentParser
import logging


logger = logging.getLogger("CLI")

def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    subparser = subparsers.add_parser(
        "serve", 
        help="Start a rest server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.add_argument("--host", default="127.0.0.1", help="Socket host")
    subparser.add_argument("--port", default=80, type=int, help="Socket port")
    subparser.add_argument("--reload", action="store_true", help="Auto reload (for dev)")
    subparser.add_argument("--no-dht", action="store_true", help="Start the service without DHT support")

    subparser.set_defaults(func=command)


def command(args):
    logger.debug("command serve")
    from .rest.api import API
    api = API(host=args.host, port=args.port, reload=args.reload, no_dht=args.no_dht)
    api.start()