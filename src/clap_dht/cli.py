import argparse
import dotenv
import logging

from clap_dht.navidrome import Navidrome

from clap_dht.updater import Updater

logger = logging.getLogger()

def command_update(args):
    logger.debug("command update")
    updater = Updater(drop_all=args.drop, batch_size=args.batch, force_process=args.force)
    updater.start()

def command_navidrome(args):
    logger.debug("command navidrome")
    navidrome = Navidrome()
    navidrome.update_ids()



def main():
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(prog='CLAP DHT CLI')
    parser.add_argument("--debug", action="store_true")

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="valid subcommands",
        required=True
    )

    subparser_update = subparsers.add_parser(
        "update", 
        help=""
    )

    subparser_update.add_argument('--force', action='store_true')
    subparser_update.add_argument('--drop', action='store_true')
    subparser_update.add_argument('--batch', type=int, default=8)

    subparser_update.set_defaults(func=command_update)

    subparser_navidrome = subparsers.add_parser(
        "navidrome", 
        help=""
    )

    subparser_navidrome.set_defaults(func=command_navidrome)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    args.func(args)
