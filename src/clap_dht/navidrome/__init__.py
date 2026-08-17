from __future__ import annotations
import argparse
from argparse import _SubParsersAction, ArgumentParser

import logging

logger = logging.getLogger("NAVIDROME")

def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    navidrome_parser = subparsers.add_parser(
        "navidrome", 
        help="Navidrome operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    navidrome_subparsers = navidrome_parser.add_subparsers(required=True)

    update_parser = navidrome_subparsers.add_parser(
        "update", 
        help="Update ids using navidrome",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    scan_group = update_parser.add_mutually_exclusive_group()
    scan_group.add_argument("--quick-scan", "-s", action="store_true", help="Quick-scan before updating")
    scan_group.add_argument("--full-scan", action="store_true", help="Full-scan before updating")
    update_parser.set_defaults(func=command_update)


def command_update(args):
    from .navidrome import Navidrome
    logger.debug("command navidrome")
    navidrome = Navidrome()
    navidrome.update_ids(args.quick_scan, args.full_scan)