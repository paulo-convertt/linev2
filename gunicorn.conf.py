# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", 4))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 5

# Restart workers after this many requests, with up to 50 requests variation
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'line-chatbot'

# Worker timeout for debuging purposes
timeout = 120

# The maximum number of simultaneous clients per worker
worker_connections = 1000

# Application
# Set PYTHONPATH to include src directory
pythonpath = "/app/src"

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Called before forking a worker."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives a SIGINT or SIGQUIT signal."""
    worker.log.info("worker received INT or QUIT signal")

def on_exit(server):
    """Called when the server is exiting."""
    server.log.info("Shutting down: Master")
