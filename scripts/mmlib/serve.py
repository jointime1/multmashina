"""Локальный сервер для предпросмотра и рендера: без кеша, чтобы правки сцен были видны сразу."""
import functools
import http.server
import threading


class БезКеша(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *a):   # тишина в консоли
        pass


def запустить(папка, порт=0):
    """Поднять сервер в фоне; вернуть (сервер, порт)."""
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', порт), functools.partial(БезКеша, directory=str(папка)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]
