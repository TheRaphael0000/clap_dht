from __future__ import annotations
import argparse
from argparse import _SubParsersAction, ArgumentParser

import logging

logger = logging.getLogger("NAVIDROME")

def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    subparser = subparsers.add_parser(
        "navidrome", 
        help="Navidrome operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.set_defaults(func=command)


def command(args):
    from .navidrome import Navidrome
    logger.debug("command navidrome")
    navidrome = Navidrome()
    navidrome.update_ids()