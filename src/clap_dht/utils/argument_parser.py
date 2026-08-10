import argparse

from clap_dht.updater import add_subparser as add_subparser_updater
from clap_dht.navidrome import add_subparser as add_subparser_navidrome
from clap_dht.db import add_subparser as add_subparser_db
from clap_dht.query import add_subparser as add_subparser_query
from clap_dht.serve import add_subparser as add_subparser_serve
from clap_dht.utils.config import config


def parse():
    parser = argparse.ArgumentParser(
        prog="CLAP DHT CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Show debug logs")
    parser.add_argument("--config", type=str, help="Path to the config file", default=config.default_config_path())

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="valid subcommands",
        required=True,
    )

    add_subparser_db(subparsers)
    add_subparser_navidrome(subparsers)
    add_subparser_query(subparsers)
    add_subparser_serve(subparsers)
    add_subparser_updater(subparsers)

    args = parser.parse_args()

    return args