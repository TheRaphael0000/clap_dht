import argparse
import dotenv

from clap_dht.navidrome import Navidrome

from clap_dht.updater import Updater

def updater(args):
    print("updater")
    updater = Updater(drop_all=args.drop, batch_size=args.batch, force_process=args.force)
    updater.start()

def navidrome(args):
    navidrome = Navidrome()
    navidrome.update_ids()



def main():
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(prog='CLAP DHT CLI')

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="valid subcommands",
        required=True
    )

    subparser_updater = subparsers.add_parser(
        "updater", 
        help=""
    )

    subparser_updater.add_argument('--force', action='store_true')
    subparser_updater.add_argument('--drop', action='store_true')
    subparser_updater.add_argument('--batch', type=int, default=8)

    subparser_updater.set_defaults(func=updater)


    subparser_navidrome = subparsers.add_parser(
        "navidrome", 
        help=""
    )

    subparser_navidrome.set_defaults(func=navidrome)

    args = parser.parse_args()
    args.func(args)
