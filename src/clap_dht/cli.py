import argparse
import logging

from clap_dht.updater import add_subparser as add_subparser_updater
from clap_dht.navidrome import add_subparser as add_subparser_navidrome
from clap_dht.query import add_subparser as add_subparser_query
from clap_dht.serve import add_subparser as add_subparser_serve

def main():
    parser = argparse.ArgumentParser(
        prog="CLAP DHT CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true")

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="valid subcommands",
        required=True,
    )

    add_subparser_updater(subparsers)
    add_subparser_navidrome(subparsers)
    add_subparser_query(subparsers)
    add_subparser_serve(subparsers)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    args.func(args)