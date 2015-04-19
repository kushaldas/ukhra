from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from ukhra import APP

http_server = HTTPServer(WSGIContainer(APP))
http_server.listen(5000)
IOLoop.instance().start()