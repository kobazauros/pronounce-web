# pyright: strict


# Binding to a unix socket is more performant than TCP
bind = "unix:pronounce-web.sock"
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 3
threads = 2
worker_class = "gthread"
timeout = 120  # Extended timeout for audio processing
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
