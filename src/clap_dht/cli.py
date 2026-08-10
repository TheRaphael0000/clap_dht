import logging
from clap_dht.utils.config import config
from clap_dht.utils.argument_parser import parse


def main():
    args = parse()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config.initialize(args.config)
    args.func(args)