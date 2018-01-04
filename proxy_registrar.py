#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
import time
import json
import csv
import hashlib
import random
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
    b"www Authenticate: Digest nonce=",
    "User Not Found": b"SIP/2.0 404 User Not Found\r\n\r\n",
    "Method Not Allowed": b"SIP/2.0 405 Method Not Allowed\r\n\r\n",
    "Service Unavailable": b"SIP/2.0 503 Service Unavailable\r\n\r\n"
    }

SIP_type = {
    "INVITE": answer_code["Trying"] + answer_code["Ringing"] +
    answer_code["Ok"],
    "BYE": answer_code["Ok"],
    "ACK": answer_code["Ok"]
    }

SIP_metodo = ["INVITE", "BYE", "ACK", "REGISTER"]

Log_type = {
    "sent": " Sent to ",
    "recv": " Received from ",
    "err": " Error: ",
    "star": " Starting... ",
    "finish": " Finishing. ",
    "other": " Other "
    }


class Write_log(ContentHandler):

    def time_now(self):

        return time.strftime("%Y%m%d%H%M%S", time.gmtime())

    def log(self, fichero, tipo, direccion, msg):

        time = self.time_now()
        msg = msg.replace("\r\n", " ")
        if tipo == "star":
            pass
        elif tipo == "finish":
            pass
        elif tipo == "err":
            pass
        else:
            direccion = direccion + ": "

        with open(fichero, "a") as fichero_log:
            fichero_log.write(time + Log_type[tipo] + direccion + msg + "\r\n")


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""
    users = {}
    passwd = []
    NONCE = random.getrandbits(100)

    #hash_generated = ""
    def generate_hash(self, passwd):
        h = hashlib.sha1()
        h.update(bytes(str(self.NONCE), 'utf-8'))
        h.update(bytes(passwd, 'utf-8'))

        print (h.hexdigest())
        return(h.hexdigest())

    @classmethod
    def read_passwd(self):
        text = ""

        with open("passwords.txt", "r") as fichero:
            lines = fichero.readlines()

        for line in lines:
            text += line
        text = text.replace("\n", " ")
        self.passwd = text.split(" ")

        print (self.passwd)

    def find_user(self, cliente):

        if not cliente in self.users.keys():
            return False
        else:
            return True

    def find_pass_user(self, user):
        if not user in self.passwd:
            sys.exit("Falta usuario en el ficheror passwords.txt")
        return self.passwd[self.passwd.index(user) + 1]

    def deluser(self, cliente, line, time_now):

        del_users = []
        if int(line[3]) == 0:
            del self.users[cliente]
        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        for user in self.users:
            if self.users[user]["expires"] < time_now:
                del_users.append(user)
        for user in del_users:
            del self.users[user]

    def registrarse(self, cliente, line):
        puerto = line[1][line[1].rfind(":") + 1:]
        expires_time = time.gmtime(int(time.time()) + int(line[3]))
        usuario = {
            "ip": self.client_address[0],
            "puerto": puerto,
            "expires": time.strftime("%Y-%m-%d %H:%M:%S", expires_time)
            }
        self.users[cliente] = usuario

        print (self.users)

    def comunication_ack(self, msg_to_send, ip, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            print("Mandando ACK")
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, int(port)))
            my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
            direccion = ip + ":" + port
            wr_log.log(CONF["log_path"], "sent", direccion, msg_to_send)

    def comunication(self, msg_to_send, ip, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, int(port)))
            my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
            direccion = ip + ":" + port + " "
            wr_log.log(CONF["log_path"], "sent", direccion, msg_to_send)
            try:
                msg_rcv = my_socket.recv(1024)
                wr_log.log(
                    CONF["log_path"], "recv", direccion,
                    msg_rcv.decode('utf-8')
                )
                return msg_rcv

            except ConnectionRefusedError:
                wr_log.log(
                    CONF["log_path"], "err", direccion,
                    answer_code["Service Unavailable"].decode('utf-8')
                )
                return answer_code["Service Unavailable"]

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
        direccion = self.client_address[0] + ":" + str(self.client_address[1])
        wr_log.log(CONF["log_path"], "recv", direccion, " ".join(line))

        print("El cliente ha mandado " + line[0])

        if not line[0] in SIP_metodo:
            msg = answer_code["Method Not Allowed"]
            wr_log.log(
                CONF["log_path"], "sent", direccion, msg.decode('utf-8')
            )

        elif line[0] == "REGISTER":
            if len(line) == 5:
                digest_nonce = b"'" + bytes(str(self.NONCE), 'utf-8') + b"'"
                msg = answer_code["Unauthorized"] + digest_nonce + b"\r\n\r\n"
                print ("Contraseña: ")
            else:
                response = line[6][line[6].find("'") + 1:line[6].rfind("'")]
                passwd = self.find_pass_user(cliente)
                hash_generated = self.generate_hash(passwd)

                print("Este es el response:" + response)
                print ("ESte es el Hash generado:" + hash_generated)
                if response == hash_generated:
                    if int(line[3]) == 0:
                        self.registrarse(cliente, line)
                        self.deluser(cliente, line, time_now)
                        msg = answer_code["Ok"]

                    else:
                        self.registrarse(cliente, line)
                        self.deluser(cliente, line, time_now)
                        msg = answer_code["Ok"]
                    self.register2json()
                else:
                    msg = answer_code["Bad Request"]

        elif line[0] == "INVITE":
            o = line[4][line[4].find("=") + 1:]
            if self.find_user(o) is False:
                msg = answer_code["Unauthorized"]
            else:
                cliente = line[1][line[1].find(":") + 1:]
                if self.find_user(cliente) is False:
                    msg = answer_code["User Not Found"]
                else:
                    msg_to_send = " ".join(line)
                    msg = self.comunication(
                        msg_to_send, self.users[cliente]["ip"],
                        self.users[cliente]["puerto"],
                    )
        elif line[0] == "BYE":
            cliente = line[1][line[1].find(":") + 1:]
            print (cliente)
            if self.find_user(cliente) is False:
                msg = answer_code["User Not Found"]
            else:
                msg_to_send = " ".join(line)
                msg = self.comunication(
                    msg_to_send, self.users[cliente]["ip"],
                    self.users[cliente]["puerto"],
                )

        elif line[0] == "ACK":
            cliente = line[1][line[1].find(":") + 1:]
            msg_to_send = " ".join(line)
            self.comunication_ack(
                msg_to_send, self.users[cliente]["ip"],
                self.users[cliente]["puerto"],
            )
        if line[0] == "ACK":
            pass
        else:
            self.wfile.write(msg)
            #Al tener una lista de mensajes en bytes tengo que decodificarlos
            #para que quede constancia en el log
            wr_log.log(
                CONF["log_path"], "sent", direccion, msg.decode('utf-8')
            )

    def register2json(self):
        """Crea un archivo .json del dicionario de usuarios."""
        with open("registered.json", "w") as fich_json:
            json.dump(
                self.users,
                fich_json,
                sort_keys=True,
                indent=4, separators=(',', ': '))
    # Gracias a esto puedo acceder al método desde el programa principal
    @classmethod
    def json2registered(self):
        """Existencia archivo .json.

        Comprueba la exstencia de un archivo .json para crear un diccionario
        de usuarios a partir de este.
        """
        try:
            fich_json = open("registered.json", "r")
            self.users = json.load(fich_json)
            # print("lo he pillado")
            # print(self.users)
        except:
            self.users = {}


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


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit("Usage: python proxy_registrar.py config")

    CONFIG = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler(etiquetas)
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    CONF = cHandler.get_tags()
    wr_log = Write_log()
    if CONF["server_ip"] == "":
        CONF["server_ip"] = "127.0.0.1"
    #print (CONF)

    SIPRegisterHandler.json2registered()
    SIPRegisterHandler.read_passwd()
    serv = socketserver.UDPServer(
        ('', int(CONF["server_puerto"])), SIPRegisterHandler
        )

    msg = "Server " + CONF["server_name"] + " listening at port " + \
        CONF["server_puerto"]
    print (msg)
    wr_log.log(CONF["log_path"], "star", " ", msg)

    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        print("Finalizado proxy_registrar")
        wr_log.log(CONF["log_path"], "finish", " ", "")
