#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


etiquetas = {
    "account": ["username", "passwd"],
    "uaserver": ["ip", "puerto"],
    "rtpaudio": ["puerto"],
    "regproxy": ["ip", "puerto"],
    "log": ["path"],
    "audio": ["path"]
}


answer_code = {
    "Trying": b"SIP/2.0 100 Trying\r\n\r\n",
    "Ringing": b"SIP/2.0 180 Ringing\r\n\r\n",
    "Ok": b"SIP/2.0 200 OK\r\n\r\n",
    "Bad Request": b"SIP/2.0 400 Bad Request\r\n\r\n",
    "Method Not Allowed": b"SIP/2.0 405 Method Not Allowed\r\n\r\n"
    }

SIP_type = {
    "BYE": answer_code["Ok"],
    "ACK": answer_code["Ok"]
    }


def msg_constructor():
    u"""Función constructora de mensajes."""
    if METHOD == "REGSITER":
        msg = METHOD + " sip:" + login + ":" port + " SIP/2.0" + "\r\n" +
        "Expires: " + OPTION + "\r\n")
    elif METHOD == "INVITE":
        head = METHOD +" sip:" + OPTION + ":" port + " SIP/2.0" + "\r\n"
        content_type = "content_type: application/sdp" +"\r\n\r\n"
        v = "v=0"
        o = "o=" CONF["account_username"] + CONF["userserver_ip"] + "\r\n"
        s = "s= misesion" + "\r\n"
        t = "t=0" + "\r\n"
        m = "m=audio" + CONF["rtpaudio_puerto"] + "RTP" + "\r\n"
        msg = head + content_type + v + o + s + t + m
    elif METHOD == "BYE":
        msg = METHOD + " sip:" + OPTION + "SIP/2.0" + "\r\n"

    return msg


def comunication():
    u"""Comunicación cliente/servidor.

    Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:

        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((CONF[regproxy_ip], CONF[regproxy_port]))
        msg_to_send = msg_constructor()
        my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
        print("Enviando: " + msg_to_send)
        data = my_socket.recv(1025)
        print('Recibido -- ', data.decode('utf-8'))


class XMLHandler(ContentHandler):
    """Constructor XML"""
    def __init__(self):
        self.XML = {}


    def get_tags(self):
        return self.XML

    def startElement(self, name, attrs):
        if name not in etiquetas.keys():
            return

        for atributo in etiquetas[name]:
            #Identifico la etiqueta y el argumento en la misma línea
            #Lo meto en un diccionario
            self.XML[name + "_" + atributo] = attrs.get(atributo, "")

if __name__ == '__main__':

    if len(sys.argv) != 4:
        sys.exit("Usage: python uaclient.py config method option")
    try:
        CONFIG = sys.argv[1]
        METHOD = sys.argv[2].upper()
        OPTION = sys.argv[3]
    except Exception:
        sys.exit("Usage: python uaclient.py config method option")

    try:
        pass
        #comunication(server, port, sip_type, login)
    except socket.gaierror:
        sys.exit("Usage: python uaclient.py config method option")

    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    CONF = cHandler.get_tags()
