# Docker bootstrapper for python projects

Helps setting up logging and rsyslogd.

Rsyslog will be listening on the standard `/dev/log` socket and forwarding
everything to logentries.

The `bootstrap()` turns the caller process into circusd and thus the function
never returns.

## Usage:

1. add `docker_bootstrap` to your requirements
2. drop your `circus.ini` file in the current dir
3. Write a `bootstrap.py` module with the following contents:

    ```
    from docker_bootstrap import bootstrap

    bootstrap(log_level='WARNING', logentries_token='adsf', rsyslog_debug=False)
    ```

4. in your Dockerfile add a `ENTRYPOINT python bootstrap.py`
5. in your python code call: `docker_bootstrap.setup_logging()` and subsequently configure logging with `disable_existing_loggers=False`

The bootstrapper will spawn rsyslogd and circus for you.


## Sample circusd config

```
[watcher:web]
cmd = uwsgi
args = uwsgi.ini
copy_env = True
use_sockets = True
send_hup = True
stop_signal = QUIT

stderr_stream.class = FileStream
stderr_stream.filename = /err.log
stderr_stream.max_bytes = 1000000
stderr_stream.backup_count = 4

stdout_stream.class = FileStream
stdout_stream.filename = /out.log
stdout_stream.max_bytes = 1000000
stdout_stream.backup_count = 4

[circus]
logoutput = syslog:///dev/log?local7
```

## Sample uwsgi config

```
[uwsgi]
http-socket = :8080
master = true
processes = 4
module = my_proj.wsgi:application
logger = syslog
```

## Testing locally

To log to the console instead of rsyslog, call
`bootstrap(rsyslog=False, console=True, circus=False)`; it will also prevent spawning of rsyslogd and circus.

Usually `bootstrap()` should be called by the testcase setup logic.
