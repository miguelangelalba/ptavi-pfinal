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
from proxy_registrar import Write_log

SIP_type = {
    "INVITE": answer_code["Trying"] + answer_code["Ringing"] +
    answer_code["Ok"],
    "BYE": answer_code["Ok"],
    "ACK": answer_code["Ok"]
    }
ip_to_send = [""]
RTP_to_send = [""]

class SIPServer(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):
        u"""Handle method of the server class.

        (All requests will be handled by this method).
        Compruebo los métodos y mando las respuestas asociadas a cada método
        con los diccionarios definidos arriba.
        """
        line = self.rfile.read().decode('utf-8').split(" ")
        direccion = self.client_address[0] + ":" + str(self.client_address[1])
        wr_log.log(CONF["log_path"], "recv", direccion,  " ".join(line))

        if not line[0] in SIP_type:
            print ("Metodo no encontrado")
            msg = answer_code["Method Not Allowed"]
            self.wfile.write(msg)
            wr_log.log(CONF["log_path"], "sent", direccion, msg.decode('utf-8'))

        elif line[0] == "INVITE":
            print ("Imprimiendo esto: " + line[5])
            ip_to_send.insert(0,line[5])
            RTP_to_send.insert(0,line[8])
            print ("Puerto RTP:" + str(RTP_to_send[0]))

            v = "v=0" + "\r\n"
            o = "o=" + CONF["account_username"] + " " + CONF["uaserver_ip"] +\
            " \r\n"
            s = "s= misesion" + "\r\n"
            t = "t=0" + "\r\n"
            m = "m=audio " + CONF["rtpaudio_puerto"] + " RTP" + "\r\n"
            sdp = v + o + s + t + m
            msg = SIP_type["INVITE"] + bytes(sdp, 'utf-8')
            self.wfile.write(msg)
            wr_log.log(CONF["log_path"], "sent", direccion, msg.decode('utf-8'))

        elif line[0] == "ACK":
            print ("Puerto ACK RTP:" + str(RTP_to_send[0]))
            aEjecutar = "./mp32rtp -i " + ip_to_send[0] +  " -p" + \
            RTP_to_send[0] + "< " + \
            CONF["audio_path"]
            print("ACK recibido ejecutando:", aEjecutar)
            os.system(aEjecutar)
            #self.wfile.write(msg)
        elif line[0] == "BYE":
            msg = SIP_type["BYE"]
            self.wfile.write(msg)
            wr_log.log(CONF["log_path"], "sent", direccion, msg.decode('utf-8'))


        #else:
        #    msg = SIP_type[line[0]]
            #self.wfile.write(SIP_type[line[0]])
        #self.wfile.write(msg)
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
    if CONF["uaserver_ip"] == "":
        CONF["uaserver_ip"] = "127.0.0.1"
    print (CONF)
    wr_log = Write_log()

    serv = socketserver.UDPServer(
        ('', int(CONF["uaserver_puerto"])), SIPServer
        )

    print("Listening...")
    wr_log.log(CONF["log_path"],"star","","")


    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        wr_log.log(CONF["log_path"],"finish","","")
        print("Finalizado uaserver")
