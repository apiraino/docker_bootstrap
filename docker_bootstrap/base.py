# -*- coding: utf-8 -*-
'''
Prepare the config files for the other docker inhabitants starting from
the environment variables.
'''

import os
import time
import sys
import subprocess
import socket

from jinja2 import Environment, FileSystemLoader

SYSLOG_SOCKET = '/log.sock'

TEMPLATE_DIR = os.path.join(os.path.os.path.dirname(__file__), 'templates')

__all__ = ['setup_logging', 'bootstrap']


def prepare_python_logging_config(log_level='INFO'):
    # create and write logging config file
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('logging.conf.jinja2')
    contents = template.render(log_level=log_level, syslog_socket=SYSLOG_SOCKET)

    with open('logging.conf', 'w') as f:
        f.write(contents)


def setup_logging():
    import logging.config
    import yaml
    with open('logging.conf', 'r') as f:
        logging_config = yaml.load(f)
    logging.config.dictConfig(logging_config)


def setup_rsyslog_logging(log_level, logentries_token=None,
                          rsyslog_debug=False):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('rsyslog.conf.jinja2')
    contents = template.render(logentries_token=logentries_token,
                               syslog_socket=SYSLOG_SOCKET,
                               rsyslog_debug=rsyslog_debug)

    with open('/rsyslog.conf', 'w') as f:
        f.write(contents)

    # spawn rsyslog
    rsyslog = subprocess.Popen(['rsyslogd', '-i', '/rsyslog.pid',
                                '-f', '/rsyslog.conf'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    def print_rsyslog_streams():
        stderr = rsyslog.stderr.read()
        print('Rsyslogd stderr: {}'.format(stderr)) if stderr else None
        stdout = rsyslog.stdout.read()
        print('Rsyslogd stdout: {}'.format(stdout)) if stdout else None

    for i in range(10):
        if os.path.exists('/log.sock'):
            break
        time.sleep(.2)
    else:
        print('Error spawning rsyslogd')
        print_rsyslog_streams()
        sys.exit(1)
    print_rsyslog_streams()


def become_circusd():
    print('Bootstrapping done, spawning circusd')
    os.execlp('circusd', 'circusd', 'circus.ini')


def bootstrap(log_level='INFO', logentries_token=None, rsyslog_debug=False):
    '''Setup python logging, rsyslog and spawn circusd.

    Args:
      log_level (default to `INFO`)
      logentries_token: token for logentries logging
      rsyslog_debug: debug rsyslog loggin logally
    '''
    prepare_python_logging_config(log_level=log_level)
    setup_rsyslog_logging(log_level=log_level, rsyslog_debug=rsyslog_debug,
                          logentries_token=logentries_token)
    setup_logging()
    become_circusd()
