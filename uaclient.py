#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

etiquetas = {"account":["username","passwd"],
    "uaserver":["ip","puerto"],
    "rtpaudio":["puerto"],
    "regproxy":["ip","puerto"],
    "log":["path"],
    "audio":["path"]
}

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
            #Con identifico la etiqueta y el argumento en la misma línea
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
    lista = cHandler.get_tags()
    print(lista)
