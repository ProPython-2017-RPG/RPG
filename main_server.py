"""
Низкоуровневая реализация TCP-сервера, работающего с множеством клиентов, используя потоки.
"""
import threading
import queue
import socket
import peewee
from peewee import *
import logging
from datetime import date

db = MySQLDatabase("admin_test", host="188.226.185.13", port=3306, user="admin_test", passwd="111111")

logger = logging.getLogger("client")
logger.setLevel(logging.INFO)
# create the logging file handler
fh = logging.FileHandler("activity.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
fh.setFormatter(formatter)
# add handler to logger object
logger.addHandler(fh)

class User(Model):
    user_login = CharField()
    info = TextField()
    class Meta:
        database = db  # модель будет использовать базу данных 'admin_test'

# User.create_table()

# user = User(author="me", text='bad work!', birthday=date(3000, 12, 9))
# user.save()

# for book in Book.filter(author="me"):
#     print(book.text, ' ', book.birthday)

HOST = "0.0.0.0"
PORT = 9999
send_queues = {}
lock = threading.Lock()
players = []

def handle_client_recv(sock):
    """
    Receive messages from client and broadcast them to
    other clients until client disconnects
    """
    d = 0
    login = ''
    while True:
        try:
            data = sock.recv(1024)
        except:
            if login != '':
                data = d.to_bytes(1, 'big') + login + (2).to_bytes(1, 'big')
                for p in players:
                    if sock != p:
                        p.send(data)
            sock.close()
            break

        d = int(data[0])
        login = data[1:d + 1]
        label = int(data[d + 1])
        if label == 3:
            user = User
            try:
                tupl = user.select().where(user.user_login == login).get()
            except:
                tupl = 0

            if tupl == 0:
                user = User.create(user_login=login)
                logger.info("user created {}".format(login.decode("utf-8")))
                sock.sendto((1).to_bytes(1, 'big')) # в базе нет, логин создали
            else:
                sock.sendto((0).to_bytes(1, 'big'))  # в базе есть, ошибка
        elif label == 2:
            for p in players:
                if sock != p:
                    p.send(data)
            # handle_disconnect(sock)
            sock.close()
            break
        else:
            for p in players:
                if sock != p:
                    p.send(data)


        # else:
        # print("Got data from", sock.getpeername(), data.decode("utf-8"))
        # if not data:
        #     handle_disconnect(sock)
        #     break


# def handle_disconnect(sock):
#     """
#     Ensure queue is cleaned up and socket closed when a client
#     disconnects
#     """
#     fd = sock.fileno()
#     with lock:
#         # Get send queue for this client
#         q = send_queues.get(fd, None)
#
#     # If we find a queue then this disconnect has not yet
#     # been handled
#     if q:
#         q.put(None)
#         del send_queues[fd]
#         addr = sock.getpeername()
#         logger.info('Client {} disconnected'.format(addr))
#         print('Client {} disconnected'.format(addr))
#         sock.close()


def main():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((HOST, PORT))
    listen_sock.listen(10)

    while True:
        client_sock, addr = listen_sock.accept()
        logger.info('Connection from {}'.format(addr))
        players.append(client_sock)
        # user = User
        # try:
        #     tupl = user.select().where(user.user_id == addr).get()
        # except:
        #     tupl = 0
        #
        # if tupl == 0:
        #     user = User.create(user_id=addr, info="yours info!")
        # else:
        #     # tupl = user.select().where(user.user_id == addr).first()
        #     info = tupl[1]
        #     client_sock.sendto(info, addr)

        # user.save()

        q = queue.Queue()

        with lock:
            send_queues[client_sock.fileno()] = q

        threading.Thread(
            target=handle_client_recv,
            args=[client_sock], daemon=True
        ).start()
        print('Connection from {}'.format(addr))


if __name__ == '__main__':
    main()