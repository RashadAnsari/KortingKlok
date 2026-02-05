import multiprocessing


# https://docs.gunicorn.org/en/latest/design.html#async-workers
def post_fork(server, worker):
    from psycogreen.gevent import patch_psycopg

    patch_psycopg()


# https://docs.gunicorn.org/en/stable/settings.html#settings
bind = ":8000"
# threads = 2
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
wsgi_app = "baseapi.wsgi"
loglevel = "warning"
keepalive = 10
graceful_timeout = 10
