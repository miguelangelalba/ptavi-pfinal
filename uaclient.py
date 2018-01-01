#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa cliente que abre un socket a un servidor."""

import socket
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import XMLHandler
from proxy_registrar import answer_code
from proxy_registrar import Write_log


etiquetas = {
    "account": ["username", "passwd"],
    "uaserver": ["ip", "puerto"],
    "rtpaudio": ["puerto"],
    "regproxy": ["ip", "puerto"],
    "log": ["path"],
    "audio": ["path"]
}


def msg_constructor(metodo):
    u"""Función constructora de mensajes."""
    msg = ""
    if metodo == "REGISTER":
        msg = METHOD + " sip:" + CONF["account_username"] + ":" + \
            CONF["uaserver_puerto"] + " SIP/2.0" + "\r\n" + \
            "Expires: " + OPTION + " \r\n"
    elif metodo == "INVITE":
        head = METHOD + " sip:" + OPTION + " SIP/2.0" + "\r\n"
        content_type = "content_type: application/sdp" + "\r\n\r\n"
        v = "v=0" + " \r\n"
        o = "o=" + CONF["account_username"] + " " + CONF["uaserver_ip"] + \
            " \r\n"
        s = "s= misesion" + "\r\n"
        t = "t=0" + "\r\n"
        m = "m=audio " + CONF["rtpaudio_puerto"] + " RTP" + "\r\n"
        msg = head + content_type + v + o + s + t + m
    elif metodo == "ACK":
        #No utilizo el global ya que el ACK se lo tengo que pasar por ser auto
        msg = metodo + " sip:" + OPTION + " SIP/2.0" + "\r\n"
    elif metodo == "BYE":
        msg = METHOD + " sip:" + OPTION + " SIP/2.0" + "\r\n"
    else:
        #sys.exit(nswer_code["Method Not Allowed"]
        sys.exit("405 Method Not Allowed --> " + METHOD)

    return msg


def comunication():
    u"""Comunicación cliente/servidor.

    Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:

        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((CONF["regproxy_ip"], int(CONF["regproxy_puerto"])))
        msg_to_send = msg_constructor(METHOD)
        my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
        direccion = CONF["regproxy_ip"] + ":" + CONF["regproxy_puerto"]
        wr_log.log(CONF["log_path"], "sent", direccion, msg_to_send)

        try:
            data = my_socket.recv(1024)
            print("Enviando: " + msg_to_send)
        except ConnectionRefusedError:
            msg = "No server listening at " + CONF["regproxy_ip"] + \
                " port " + CONF["regproxy_puerto"]
            wr_log.log(CONF["log_path"], "err", " ", msg)
            sys.exit("Error: " + msg)
        print('Recibido -- ', data.decode('utf-8'))

        if data == answer_code["Unauthorized"]:
            ath = "Authorization: Digest response=123123212312321212123"
            msg = msg_constructor(METHOD) + ath
            wr_log.log(CONF["log_path"], "sent", direccion, msg)

            print("Enviando: " + msg)
            my_socket.send(bytes(msg, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )

            print('Recibido -- ', data.decode('utf-8'))
        elif data == answer_code["User Not Found"]:
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )
        elif data == answer_code["Method Not Allowed"]:
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )
        elif data == answer_code["Bad Request"]:
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )
        elif data == answer_code["Ok"]:
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )
        elif data == answer_code["Service Unavailable"]:
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )

        else:
            line = data.decode('utf-8').split(" ")
            wr_log.log(
                CONF["log_path"], "recv", direccion, data.decode('utf-8')
                )
            print ("Dir_ip_enviar " + line[7])
            print ("Puerto a enviar: " + line[10])
            ip = line[7]
            puerto = line[10]
            #direccion = ip + ":" + puerto
            #Mando RTP UA
            direccion1 = ip + ":" + puerto
            msg = "Mensaje RTP"
            wr_log.log(CONF["log_path"], "sent", direccion1, msg)
            aEjecutar = "./mp32rtp -i " + ip + " -p" + puerto + "< " + \
                CONF["audio_path"]

            #Mando ACK al server
            msg_to_send = msg_constructor("ACK")
            print("Enviando: " + msg_to_send)
            wr_log.log(CONF["log_path"], "sent", direccion, msg_to_send)
            my_socket.send(bytes(msg_to_send, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            print("Ejecutando:", aEjecutar)
            os.system(aEjecutar)
            print('Recibido -- ', data.decode('utf-8'))


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
        if CONF["uaserver_ip"] == "":
            CONF["uaserver_ip"] = "127.0.0.1"
        print(CONF)
        wr_log = Write_log()
        comunication()
    except socket.gaierror:
        sys.exit("Usage: python uaclient.py config method option")
