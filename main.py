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
connections_collection = db['connections']

# set defaut port to 9000
define("port", default=9000, help="run on this port",type=int)
define("static_path", os.path.join(os.path.dirname(__file__), "static"))

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
        self.conn_handler = ConnectionsHandler(socket=self)
        self.conn_handler.add_connection()


        clients[self.id] = {"id":self.id, "object" : self, "init_time": helpers.get_cur_srv_time_ms()}

        self.write_message("Hello friend")
        print "WebSocket %s opened" % (self.id)

    def on_message(self, message):
        self.conn_handler.increment_messages()
        message_handler = NewMessageHandler(message, socket=self)

        """
        When a message is received we should call a message handler
        :param message: message received
        :return: for now this will print to console
        """
        print "Client %s received a message : %s" % (self.id, message)

    def on_close(self):
        if self.id in clients:
            del clients[self.id]

        self.conn_handler.remove_connection()

class ConnectionsHandler(object):
    def __init__(self, socket):
        self.socket = socket
        self.connections = []

    def _add_connection_cb(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            message_handler = NewMessageHandler(message=None,socket = self.socket)
            message_handler.respond(msg_type="Connect", data=result)
            print repr(result)

    def _get_connections_done(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            for i in range(len(result)):
                time = result[i]["init_time"]
                f_time = helpers.format_ms_to_hmsf(
                    helpers.time_dif_from_val_to_now(time)
                )
                result[i]["uptime"] = f_time
                del result[i]["_id"]
                del result[i]["init_time"]

            message_handler = NewMessageHandler(message=None, socket = self.socket)
            message_handler.respond(msg_type="Connections", data=result)
            print repr(result)

    def _remove_connection_done(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            print "Connection deleted" + repr(result)


    def _connections_each(self, result, error):
        if error:
            raise error
        elif result:
            self.connections.append(result)
        else:
            print "Done"
            self._get_connections_done(result=self.connections,error=error)

    def _increment_messages_done(self, result, error):
        if error:
            raise error
        elif result:
            print repr(result)

    def add_connection(self):
        connection = {"id":self.socket.id, "init_time": helpers.get_cur_srv_time_ms(), "messages":0}
        connections_collection.insert(connection, callback=self._add_connection_cb)

    def get_connections(self):
        connections_collection.find().each(callback=self._connections_each)

    def remove_connection(self):
        connections_collection.remove({"id":self.socket.id},callback=self._remove_connection_done)

    def increment_messages(self):
        connections_collection.find_and_modify(
            query={"id": self.socket.id},
            update={"$inc": {"messages": 1}},
            new=True,
            callback=self._increment_messages_done
        )

class NewMessageHandler(object):
    def __init__(self, message, socket):
        self.response_message = ""
        self.message = {"message":message, "timestamp": helpers.get_cur_srv_time()}
        self.socket = socket
        if self.message["message"] is not None:
            self.interpret_msg()

    def interpret_msg(self):
        command = helpers.match_commands(self.message["message"])
        stripped_list = list()
        if len(command) > 0:
            for i in range(len(command[0])):
                if len(str(command[0][i])) != 0:
                    stripped_list.append(command[0][i])
            if stripped_list[0] == "send":
                if stripped_list[1] == "get":
                    if stripped_list[2]:
                         collection.find_one({stripped_list[2]: stripped_list[3]}, callback=self._find_one_cb)
                elif stripped_list[1] == "set":
                    if stripped_list[2]:
                        if stripped_list[3]:
                            doc = {stripped_list[2]:stripped_list[3]}
                            collection.insert(doc, callback=self._insert_cb)

            elif stripped_list[0] == "say":
                self.respond(msg_type="Sent")

            elif stripped_list[0] == "connections":
                ConnectionsHandler(socket=self.socket).get_connections()

            elif stripped_list[0] == "disconnect":
                self.socket.close()

            else:
                print "Invalid Command"

        else:
            print "Invalid Command"
            self.respond(msg_type="Invalid")

    def respond(self, msg_type="Sent", data=None):
        if msg_type == "Sent":
            self.response_msg = str(self.message["timestamp"]) + " Sent: " + self.message["message"]

        elif msg_type == "Invalid":
            self.response_msg = str(self.message["timestamp"]) + " " + "Invalid Command: " + ": " + self.message["message"]

        elif msg_type == "Received":
            if data is not None:
                self.response_msg = str(self.message["timestamp"]) + " Received: " + repr(data) + " OK"
            else:
                self.response_msg = str(self.message["timestamp"]) + " Received: null"

        elif msg_type == "Connections":
            if data is not None:
                self.response_msg = str(self.message["timestamp"]) + " Connections: " + repr(data) + " OK"

        elif msg_type == "Connect":
            if data is not None:
                self.response_msg = str(self.message["timestamp"]) + " Connected!: " + repr(data) + " OK"

        self.socket.write_message(self.response_msg)


    def _find_one_cb(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            self.respond(msg_type="Received",data=result)
            print repr(result)

    def _insert_cb(self, result, error):
        if error:
            raise tornado.web.HTTPError(500, error)
        else:
            self.respond(msg_type="Received",data=result)
            print repr(result)

    def get_current_connections(self):
        clients_data = {}
        # for each client we need uptime, messages, and id
        for key in clients:
            if key == "123456789":
                pass
        return repr(clients)

    def _return_uptime(self):
        pass

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
    (r'/ws', WebSocketHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": options.static_path})
], db=db)

print "Listening to the smooth sounds of port: " + str(options.port)

if __name__ == '__main__':
    # parse_command_line will take options from command line
    parse_command_line()
    # listen on port defined in define call
    app.listen(options.port)
    # start the ioLoop on server start
    IOLoop.current().start()