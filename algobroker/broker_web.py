#!/usr/bin/env python3
# http://flask.pocoo.org/snippets/116/

from flask import Flask, send_from_directory, Response
import flask
import algobroker
from io import StringIO
from queue import Queue
import sys
import time

app = Flask(__name__, static_url_path='')
subscriptions = []
# SSE "protocol" is described here: http://mzl.la/UPFyxY
class ServerSentEvent(object):
    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
            }
    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.items() if k]
        return "%s\n\n" % "\n".join(lines)

@app.route("/")
def hello():
    return app.send_static_file('broker_web.html')

@app.route("/test-data")
def testdata():
    return flask.jsonify({"records" : [{"Name" : "foo",
                           "Country" : "bar"},
                          {"Name" : "foo1",
                           "Country" : "bar1"}]})

@app.route("/desk-alert")
def deskalert():
    algobroker.send("data",
                    [{"dest" : "broker_desk_alert",
                     "cmd" : "alert",
                     "type" : "desk",
                     "alert" : "high"}])
    return "alert"

@app.route("/debug")
def debug():
    return "Currently %d subscriptions" % len(subscriptions)

@app.route("/publish")
def publish():
    msg = str(time.time())
    for sub in subscriptions[:]:
        sub.put(msg)
    return "OK"

@app.route("/subscribe")
def subscribe():
    def gen():
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit: # Or maybe use flask signals
            subscriptions.remove(q)
    return Response(gen(), mimetype="text/event-stream",
                    headers={"cache-control":"True",
                             "keep-alive":"True"})

if __name__ == "__main__":
    app.debug = True
    app.run(threaded=True)
    # Then visit http://localhost:5000 to subscribe
    # and send messages by visiting http://localhost:5000/publish