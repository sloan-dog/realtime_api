import tornado.ioloop
import tornado.web
import tornado.websocket
import motor
import os

from tornado.options import define, options, parse_command_line

DBUSER = os.environ.get('DBUSER')
DBKEY = os.environ.get('DBKEY')
DBURI = "mongodb://%s:%s@ds061345.mongolab.com:61345/sloan_testdb" % (DBUSER, DBKEY)

db = motor.motor_tornado.MotorClient(DBURI)['sloan_testdb']

# set defaut port to 9000
define("port", default=9000, help="run on this port",type=int)

# store connected clients in dict
# TODO store in mongodb
clients = dict()

# This defines url routing and which class(view) to call per url
# WebSocket connections happen on ws:// not http://, tornado
# Knows how to differeniate and handle these request,
# So route appears the same but is different protocol
app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/ws', WebSocketHandler)
], db=db)

if __name__ == '__main__':
    # parse_command_line will take options from command line
    parse_command_line()
    # listen on port defined in define call
    app.listen(options.port)
    # start the ioLoop on server start
    tornado.ioloop.IOLoop.instance().start()

# Main index view
class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("static/index.html")
        # self.write("This is your response")
        # finsh() closes request loop and we no longer need it because self.finish()
        # is called inside tornado during render
        # self.finish()

class MessageHandler(object):
    def __init__(self, message, socket):
        self.message = message
        self.socket = socket
        print str(self.message + "MessageHandler Initialized")

    def respond(self):
        self.socket.write_message("this is a response message");

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self,*args):
        self.id = self.get_argument("Id")
        self.stream.set_nodelay(True)
        clients[self.id] = {"id":self.id, "object" : self}
        self.write_message("Hello friend")
        print "WebSocket %s opened" % (self.id)

    def on_message(self, message):
        message_handler = MessageHandler(message,socket=self)
        message_handler.respond()

        """
        When a message is received we should call a message handler
        :param message: message received
        :return: for now this will print to console
        """
        print "Client %s received a message : %s" % (self.id, message)

    def on_close(self):
        if self.id in clients:
            del clients[self.id]

