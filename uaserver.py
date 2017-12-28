#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Servidor de eco en UDP simple."""

import socketserver
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import XMLHandler
from uaclient import etiquetas
from proxy_registrar import answer_code

SIP_type = {
    "INVITE": answer_code["Trying"] + answer_code["Ringing"] +
    answer_code["Ok"],
    "BYE": answer_code["Ok"],
    "ACK": answer_code["Ok"]
    }


class SIPServer(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):
        u"""Handle method of the server class.

        (All requests will be handled by this method).
        Compruebo los métodos y mando las respuestas asociadas a cada método
        con los diccionarios definidos arriba.
        """
        RTP_receiver = ""
        line = self.rfile.read().decode('utf-8').split(" ")
        if not line[0] in SIP_type:
            self.wfile.write(answer_code["Method Not Allowed"])
        elif line[0] == "INVITE":
            RTP_receiver = int(line[6])

            v = "v=0" + "\r\n"
            o = " o=" + CONF["account_username"] + " " + CONF["uaserver_ip"] +\
            "\r\n"
            s = "s= misesion" + "\r\n"
            t = "t=0" + "\r\n"
            m = "m=audio " + CONF["rtpaudio_puerto"] + " RTP" + "\r\n"
            sdp = v + o + s + t + m
            msg = SIP_type["INVITE"] + sdp
            self.wfile.write(msg)

        elif line[0] == "ACK":
            aEjecutar = "./mp32rtp -i 127.0.0.1 -p" + RTP_receiver + "< " + \
            CONF["audio_path"]
            print("ACK recibido ejecutando:", aEjecutar)
            os.system(aEjecutar)

        else:
            self.wfile.write(SIP_type[line[0]])

        print("El cliente ha mandado " + str(line))


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit("Usage: python uaserver.py config")

    CONFIG = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler(etiquetas)
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    CONF = cHandler.get_tags()
    print (CONF)

    serv = socketserver.UDPServer(
        ('', int(CONF["uaserver_puerto"])), SIPServer
        )

    print("Listening...")

    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        print("Finalizado uaserver")
