# Gunicorn configuration
wsgi_app = "main:app"

# サーバーのホストとポートの設定
bind = "0.0.0.0:8000"

# ワーカーの設定
workers = 4
timeout = 30

# ログの設定
accesslog = "-"
errorlog = "-"
loglevel = "debug"

# リクエスト上限
max_requests = 1000
max_requests_jitter = 100

daemon = False