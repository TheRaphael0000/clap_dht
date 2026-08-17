from __future__ import annotations
import logging
import argparse
from argparse import _SubParsersAction, ArgumentParser
import sys

from .query import Query

logger = logging.getLogger("CLI")


def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    subparser = subparsers.add_parser(
        "query", 
        help="DB Query operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.set_defaults(func=command)
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", "-p", type=str, help="The relative path to a file in the DB")
    group.add_argument("--songId", "-e", type=str, help="Query by songId")
    group.add_argument("--albumId", "-b", type=str, help="Query by albumId")
    group.add_argument("--artistId", "-r", type=str, help="Query by artistId")
    subparser.add_argument("--limit", "-l", type=int, default=20, help="Number of results")
    subparser.add_argument("--json", "-j", action="store_true", help="Return a json formatted string")
    subparser.add_argument("--proximity", choices=Query.proximity_functions.keys(), default="cosine_distance", help="Proximity function used for the distance")


def command(args):
    logger.debug("command query")
    query = Query(proximity_function=args.proximity, limit=args.limit, path=args.path, json=args.json, songId=args.songId, albumId=args.albumId, artistId=args.artistId)
    print(query, file=sys.stdout)
