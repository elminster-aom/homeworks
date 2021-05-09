#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests (Code not cleaned up)
See: mdonkers/server.py on https://gist.github.com/mdonkers
Usage:
    ./server.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import random
import time


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        myResponse = random.choice([200, 302, 404, 500])

        self.send_response(myResponse)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        random_delay = random.uniform(0, 15)
        time.sleep(random_delay)
        logging.info(f"GET_request - Path:{self.path}, Response_time:{random_delay}")

        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode("utf-8"))

    def do_POST(self):
        random_delay = random.uniform(0, 15)
        time.sleep(random_delay)
        content_length = int(
            self.headers["Content-Length"]
        )  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        logging.info(
            f"POST_request - Path:{self.path}, Response_time:{random_delay}, Body:\n{post_data.decode('utf-8')}\n"
        )

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        print(f"Usage:\n./server.py [<port>]")
