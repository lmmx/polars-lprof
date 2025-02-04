import argh

from .parse import parse_lprof


def cli():
    argh.dispatch_command(parse_lprof)
