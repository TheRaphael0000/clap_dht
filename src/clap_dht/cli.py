import argparse
import dotenv
import logging
import os


from clap_dht.navidrome import Navidrome

from clap_dht.query import Query
from clap_dht.updater import Updater

logger = logging.getLogger()

def command_update(args):
    logger.debug("command update")
    updater = Updater(drop_all=args.drop, batch_size=args.batch, max_workers=args.workers, force_process=args.force, prefetch_factor=args.prefetch)
    updater.start()

def command_navidrome(args):
    logger.debug("command navidrome")
    navidrome = Navidrome()
    navidrome.update_ids()

def command_query(args):
    logger.debug("command query")
    query = Query(proximity_function=args.proximity, limit=args.limit, path=args.path, json=args.json, external_id=args.external_id)
    print(query)


def main():
    dotenv.load_dotenv()

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

    subparser_update = subparsers.add_parser(
        "update", 
        help="Update operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparser_update.add_argument("--force", "-f", action="store_true", help="Process all files and override result in DB")
    subparser_update.add_argument("--drop", action="store_true", help="Drop the database before processing files")
    subparser_update.add_argument("--batch", "-b", type=int, default=8, help="Number of files process concurently, larger numbers take more memory but can be faster")
    subparser_update.add_argument("--prefetch", "-p", type=int, default=2, help="The number of prefetched batches in memory")
    subparser_update.add_argument("--workers", "-w", type=int, default=os.process_cpu_count(), help="The maximum number of workers used in a batch")

    subparser_update.set_defaults(func=command_update)

    subparser_navidrome = subparsers.add_parser(
        "navidrome", 
        help="Navidrome operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparser_navidrome.set_defaults(func=command_navidrome)

    subparser_query = subparsers.add_parser(
        "query", 
        help="DB Query operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparser_query.set_defaults(func=command_query)
    group = subparser_query.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", "-p", type=str, help="The relative path to a file in the DB")
    group.add_argument("--external_id", "-e", type=str, help="The external id of a file in the DB")
    subparser_query.add_argument("--limit", "-l", type=int, default=20, help="Number of results")
    subparser_query.add_argument("--json", "-j", action="store_true", help="Return a json formatted string")
    subparser_query.add_argument("--proximity", choices=Query.proximity_functions.keys(), default="cosine_distance", help="Proximity function used for the distance")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    args.func(args)