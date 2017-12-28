#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
import time
import json
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

etiquetas = {
    "server": ["name", "ip", "puerto"],
    "database": ["path", "passwdpath"],
    "log": ["path"]
}

answer_code = {
    "Trying": b"SIP/2.0 100 Trying\r\n\r\n",
    "Ringing": b"SIP/2.0 180 Ringing\r\n\r\n",
    "Ok": b"SIP/2.0 200 OK\r\n\r\n",
    "Bad Request": b"SIP/2.0 400 Bad Request\r\n\r\n",
    "Unauthorized": b"SIP/2.0 401 Unauthorized\r\n" +
    b"www Authenticate: Digest nonce=8989898989898989898989898989 \r\n\r\n",
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
    users = {}

    def find_user(self, cliente):

        if not cliente in self.users.keys():
            return False
        else:
            return True

    def deluser(self, cliente, line, time_now):

        del_users = []
        #cliente = line[1][line[1].find(":") + 1:line[1].rfind(":")]
        if int(line[3]) == 0:
            del self.users[cliente]
        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        for user in self.users:
            if self.users[user]["expires"] < time_now:
                del_users.append(user)
        for user in del_users:
            del self.users[user]

    def registrarse(self, cliente, line):
        #cliente = line[1][line[1].find(":") + 1:line[1].rfind(":")]
        puerto = line[1][line[1].rfind(":") + 1:]
        expires_time = time.gmtime(int(time.time()) + int(line[3]))
        usuario = {
            "ip": self.client_address[0],
            "puerto": puerto,
            "expires": time.strftime("%Y-%m-%d %H:%M:%S", expires_time)
            }
        self.users[cliente] = usuario

        print (self.users)

    def comunication(self, msg_to_send, ip, port):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:

            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, int(port)))
            my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
            return my_socket.recv(1024)

    def handle(self):
        u"""Handle method of the server class.

        (All requests will be handled by this method).
        Compruebo los métodos y mando las respuestas asociadas a cada método
        con los diccionarios definidos arriba.
        """
        line_to_send = self.rfile
        line = self.rfile.read().decode('utf-8').split(" ")
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
        cliente = line[1][line[1].find(":") + 1:line[1].rfind(":")]

        if not line[0] in SIP_metodo:
            msg = answer_code["Method Not Allowed"]
        elif line[0] == "REGISTER":
            if len(line) == 5:
                msg = answer_code["Unauthorized"]
            else:
                #falta el SDP
                if int(line[3]) == 0:
                    self.registrarse(cliente, line)
                    self.deluser(cliente, line, time_now)
                    msg = answer_code["Ok"]
                else:
                    self.registrarse(cliente, line)
                    self.deluser(cliente, line, time_now)
                    msg = answer_code["Ok"]
                self.register2json()
        elif line[0] == "INVITE":
            o = line[4][line[4].find("=") + 1:]
            print(o)
            if self.find_user(o) is False:
                print("no lo encuentro en la primera")
                msg = answer_code["Unauthorized"]
            else:
                cliente = line[1][line[1].find(":") + 1:]
                if self.find_user(cliente) is False:
                    msg = answer_code["User Not Found"]
                else:
                    msg_to_send = " ".join(line)
                    msg = self.comunication(
                    msg_to_send, self.users[cliente]["ip"],
                    self.users[cliente]["puerto"]
                    )

        self.wfile.write(msg)
        print("El cliente ha mandado " + line[0])

    def register2json(self):
        """Crea un archivo .json del dicionario de usuarios."""
        with open("registered.json", "w") as fich_json:
            json.dump(
                self.users,
                fich_json,
                sort_keys=True,
                indent=4, separators=(',', ': '))


class XMLHandler(ContentHandler):
    """Constructor XML"""
    def __init__(self, etique):
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

if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit("Usage: python proxy_registrar.py config")

    CONFIG = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler(etiquetas)
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    CONF = cHandler.get_tags()
    if CONF["server_ip"] == "":
        CONF["server_ip"] = "127.0.0.1"
    #print (CONF)

    #SIPRegisterHandler.json2registered()
    serv = socketserver.UDPServer(('', int(CONF["server_puerto"])),
    SIPRegisterHandler)

    print("Server " + CONF["server_name"] + " listening at port " +
    CONF["server_puerto"])

    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        print("Finalizado proxy_registrar")
