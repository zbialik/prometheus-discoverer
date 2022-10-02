import os
import sys
import time
import logging
import argparse
from functools import partial
from threading import Thread

from . import kube

fmt, datefmt = "[%(asctime)s.%(msecs)03d] - %(message)s", "%Y%m%dT%H:%M:%S"
handlers = [logging.StreamHandler()]

def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--timeout",
        default=60,
        help="Kubernetes Watch API timeout in seconds",
    )
    parser.add_argument(
        "-l", "--loglevel", default="INFO", help="logging level"
    )
    parser.add_argument(
        "-i",
        "--reconcile-interval",
        default=300,
        help="Interval in seconds for periodic reconciliation, 0 disables it",
        type=int
    )
    return parser.parse_args()

def set_up_logging(loglevel):
    loglevel = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(loglevel)

    logging.basicConfig(
        level=loglevel, format=fmt, datefmt=datefmt, handlers=handlers
    )

def main(server, timeout):
    kube_client = kube.KubeClient()

    while True:
        store_api_endpoints = kube_client.list_prometheus_operated_services()

        kube_client.reconcile(store_api_endpoints)

        time.sleep(5)


def run():
    args = vars(init_args())

    set_up_logging(args.pop("loglevel"))

    main(**args)


if __name__ == "__main__":
    run()
