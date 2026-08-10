import os
import signal
import logging
from clap_dht.utils.config import config
from clap_dht.utils.argument_parser import parse


def exit_all(sig, frame):
    os._exit(0)


def main():
    args = parse()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config.init(args.config)

    signal.signal(signal.SIGINT, exit_all)
    args.func(args)