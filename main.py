from tornado.ioloop import IOLoop
from tornado import gen
import tornado.web
import tornado.websocket
import motor
import os
import helpers

from tornado.options import define, options, parse_command_line

DBUSER = os.environ.get('DBUSER')
DBKEY = os.environ.get('DBKEY')
DBURI = "mongodb://%s:%s@ds061345.mongolab.com:61345/sloan_testdb" % (DBUSER, DBKEY)

db = motor.motor_tornado.MotorClient(DBURI)['sloan_testdb']
collection = db['test_collection']

# set defaut port to 9000
define("port", default=9000, help="run on this port",type=int)

# store connected clients in dict
# TODO store in mongodb
clients = dict()

# Main index view
class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("static/index.html")
        # self.write("This is your response")
        # finsh() closes request loop and we no longer need it because self.finish()
        # is called inside tornado during render
        # self.finish()

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self,*args):
        self.id = self.get_argument("Id")
        self.stream.set_nodelay(True)
        clients[self.id] = {"id":self.id, "object" : self}
        self.write_message("Hello friend")
        print "WebSocket %s opened" % (self.id)

    def on_message(self, message):
        message_handler = NewMessageHandler(message,socket=self)
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

class NewMessageHandler(object):
    def __init__(self, message, socket):
        self.message = message
        self.socket = socket
        print self.interpret_msg()

    def interpret_msg(self):
        command = helpers.match_commands(self.message)
        stripped_list = list()
        if len(command) > 0:
            for i in range(len(command[0])):
                if len(str(command[0][i])) != 0:
                    stripped_list.append(command[0][i])
            if stripped_list[0] == "send":
                if stripped_list[1] == "get":
                    if stripped_list[2]:
                         collection.find_one({"tim":"babycakes"},callback=self._find_one_cb)
                elif stripped_list[1] == "set":
                    if stripped_list[2]:
                        if stripped_list[3]:
                            doc = {stripped_list[2]:stripped_list[3]}
                            IOLoop.current().stop()
                            IOLoop.current().run_sync(do_insert(doc))

            elif stripped_list[0] == "connect":
                pass
            else:
                print "Invalid Command"
        else:
            print "Invalid Command"

    def respond(self):
        self.socket.write_message("this is a response message");

    def _find_one_cb(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            print repr(result)

@gen.coroutine
def do_insert(doc):
    future = collection.insert(doc)
    result = yield future
    print 'result %s' % repr(result)

@gen.coroutine
def do_find_one():
    future = collection.find_one({"tim":"babycakes"})
    result = yield future
    print 'result %s' % repr(result)




# This defines url routing and which class(view) to call per url
# WebSocket connections happen on ws:// not http://, tornado
# Knows how to differeniate and handle these request,
# So route appears the same but is different protocol

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/ws', WebSocketHandler)
], db=db)

print "Listening to the smooth sounds of port: " + str(options.port)

if __name__ == '__main__':
    # parse_command_line will take options from command line
    parse_command_line()
    # listen on port defined in define call
    app.listen(options.port)
    # start the ioLoop on server start
    IOLoop.current().start()