#!/usr/bin/env python2

import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='Run the fedocal app')
parser.add_argument(
    '--config', '-c', dest='config',
    help='Configuration file to use for fedocal.')
parser.add_argument(
    '--debug', dest='debug', action='store_true',
    default=False,
    help='Expand the level of data returned.')
parser.add_argument(
    '--profile', dest='profile', action='store_true',
    default=False,
    help='Profile fedocal.')
parser.add_argument(
    '--port', '-p', default=5000,
    help='Port for the fedocal to run on.')
parser.add_argument(
    "--cert", "-s", default=None, help="Filename of SSL cert for the flask application."
)
parser.add_argument(
    "--key",
    "-k",
    default=None,
    help="Filename of the SSL key for the flask application.",
)
parser.add_argument(
    '--host', default="127.0.0.1",
    help='Hostname to listen on. When set to 0.0.0.0 the server is available '
    'externally. Defaults to 127.0.0.1 making it only visible on localhost')

args = parser.parse_args()

if args.config:
    config = args.config
    if not config.startswith('/'):
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        config = os.path.join(here, config)
    os.environ['FEDOCAL_CONFIG'] = config

from fedocal import APP

if args.profile:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

APP.debug = True
if args.cert and args.key:
    APP.run(host=args.host, port=int(args.port), ssl_context=(args.cert, args.key))
else:
    APP.run(host=args.host, port=int(args.port))
