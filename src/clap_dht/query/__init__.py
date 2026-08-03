from __future__ import annotations
import logging
import argparse
from argparse import _SubParsersAction, ArgumentParser

from clap_dht.db import Embedding

from .query import Query

logger = logging.getLogger()


def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    subparser = subparsers.add_parser(
        "query", 
        help="DB Query operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.set_defaults(func=command)
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", "-p", type=str, help="The relative path to a file in the DB")
    group.add_argument("--external_id", "-e", type=str, help="The external id of a file in the DB")
    subparser.add_argument("--limit", "-l", type=int, default=20, help="Number of results")
    subparser.add_argument("--json", "-j", action="store_true", help="Return a json formatted string")
    subparser.add_argument("--proximity", choices=Query.proximity_functions.keys(), default="cosine_distance", help="Proximity function used for the distance")


def command(args):
    logger.debug("command query")
    query = Query(proximity_function=args.proximity, limit=args.limit, path=args.path, json=args.json, external_id=args.external_id)
    print(query)
