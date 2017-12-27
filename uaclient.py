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



def msg_constructor():
    u"""Función constructora de mensajes."""
    msg = ""
    if METHOD == "REGISTER":
        msg = METHOD + " sip:" + CONF["account_username"] + ":" \
        + CONF["uaserver_puerto"] + " SIP/2.0" + "\r\n" + \
        "Expires: " + OPTION + "\r\n"
    elif METHOD == "INVITE":
        head = METHOD +" sip:" + OPTION + ":" + CONF["uaserver_puerto"] + \
        " SIP/2.0" + "\r\n"
        content_type = "content_type: application/sdp" +"\r\n\r\n"
        v = "v=0"
        o = "o=" + CONF["account_username"] + CONF["uaserver_ip"] + "\r\n"
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
        my_socket.connect((CONF["regproxy_ip"],int(CONF["regproxy_puerto"])))
        msg_to_send = msg_constructor()
        my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
        try:
            data = my_socket.recv(1024)
            print("Enviando: " + msg_to_send)
        except ConnectionRefusedError:
            sys.exit ("Error: No server listening at " + CONF["regproxy_ip"] +
            " port " + CONF["regproxy_puerto"])

        print('Recibido -- ', data.decode('utf-8'))


class XMLHandler(ContentHandler):
    """Constructor XML"""
    def __init__(self,etique):
        self.XML = {}
        self.etiquetas = etique

    def get_tags(self):
        return self.XML

    def startElement(self, name, attrs):
        if name not in self.etiquetas.keys():
            return

        for atributo in self.etiquetas[name]:
            #Identifico la etiqueta y el argumento en la misma línea
            #Lo meto en un diccionario
            self.XML[name + "_" + atributo] = attrs.get(atributo, "")
            #Esta linea la dejo para un futuro
            #if self.XML["uaserver_ip"] == ""
            #    self.XML["uaserver_ip"] = "127.0.0.1"

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
        parser = make_parser()
        cHandler = XMLHandler(etiquetas)
        parser.setContentHandler(cHandler)
        parser.parse(open(CONFIG))
        CONF = cHandler.get_tags()
        print(CONF)
        comunication()
    except socket.gaierror:
        sys.exit("Usage: python uaclient.py config method option")
