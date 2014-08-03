# Docker bootstrapper for python projects

Helps setting up logging and rsyslogd.


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
