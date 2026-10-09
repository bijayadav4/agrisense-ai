# Gunicorn Production WSGI Configuration for AgriSense AI

bind = "0.0.0.0:5000"
workers = 2
threads = 2
worker_class = "gthread"
timeout = 60
keepalive = 5

# Memory Optimization: Load ML models once in parent master process before worker fork
preload_app = True

accesslog = "-"
errorlog = "-"
loglevel = "info"
