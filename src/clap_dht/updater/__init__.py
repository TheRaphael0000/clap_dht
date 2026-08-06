from __future__ import annotations
import os
import argparse
from argparse import _SubParsersAction, ArgumentParser
import logging


logger = logging.getLogger("CLI")

def add_subparser(subparsers: _SubParsersAction[ArgumentParser]):
    subparser = subparsers.add_parser(
        "update", 
        help="Update operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.add_argument("--force", "-f", action="store_true", help="Process all files and override result in DB")
    subparser.add_argument("--drop", action="store_true", help="Drop the database before processing files")
    subparser.add_argument("--no-dht", "-n", action="store_true", help="Don't rely on DHT")
    subparser.add_argument("--ignore-existing-fingerprint", action="store_true", help="To ignore fingerprint stored in the file tags")
    subparser.add_argument("--batch", "-b", type=int, default=8, help="Number of files processed at the same time, larger numbers take more memory but can be faster")
    subparser.add_argument("--prefetch", "-p", type=int, default=2, help="The number of prefetched batches in memory")
    subparser.add_argument("--workers", "-w", type=int, default=os.process_cpu_count(), help="The maximum number of workers used in a batch")

    subparser.set_defaults(func=command)


def command(args):
    from .updater import Updater # dynamically load the updater to avoid loading all the torch libs on other commands
    logger.debug("command update")
    updater = Updater(drop_all=args.drop, batch_size=args.batch, max_workers=args.workers, force_process=args.force, prefetch_factor=args.prefetch, ignore_existing_fingerprint=args.ignore_existing_fingerprint, use_dht=not args.no_dht)
    updater.start()