#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import XMLHandler

etiquetas = {
    "server":["name", "ip", "puerto"],
    "database":["path", "passwdpath"],
    "log":["path"]
}

answer_code = {
    "Trying": b"SIP/2.0 100 Trying\r\n\r\n",
    "Ringing": b"SIP/2.0 180 Ringing\r\n\r\n",
    "Ok": b"SIP/2.0 200 OK\r\n\r\n",
    "Bad Request": b"SIP/2.0 400 Bad Request\r\n\r\n",
    "Unauthorized": b"SIP/2.0 401 Unauthorized\r\n\r\n",
    "User Not Found": b"SIP/2.0 404 User Not Found\r\n\r\n",
    "Method Not Allowed": b"SIP/2.0 405 Method Not Allowed\r\n\r\n"
    }

SIP_type = {
    "INVITE": answer_code["Trying"] + answer_code["Ringing"] +
    answer_code["Ok"],
    "BYE": answer_code["Ok"],
    "ACK": answer_code["Ok"]
    }

SIP_metodo = ["INVITE", "BYE", "ACK", "REGISTER"]



class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""
    def handle(self):
        u"""Handle method of the server class.

        (All requests will be handled by this method).
        Compruebo los métodos y mando las respuestas asociadas a cada método
        con los diccionarios definidos arriba.
        """
        line = self.rfile.read().decode('utf-8').split(" ")
        if not line[0] in SIP_metodo:
            self.wfile.write(answer_code["Method Not Allowed"])
        elif line[0] == "REGISTER":
            self.wfile.write(answer_code["Unauthorized"])

        print("El cliente ha mandado " + line[0])




if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit("Usage: python proxy_registrar.py config")

    CONFIG = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler(etiquetas)
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    CONF = cHandler.get_tags()
    print (CONF)

    #SIPRegisterHandler.json2registered()
    serv = socketserver.UDPServer(('', int(CONF["server_puerto"])), \
    SIPRegisterHandler)

    print("Server " + CONF["server_name"] + " listening at port " +
    CONF["server_puerto"])

    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        print("Finalizado servidor")
