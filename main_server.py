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
    user_id = CharField()
    info = TextField()
    class Meta:
        database = db  # модель будет использовать базу данных 'admin_test'

# User.create_table()

# user = User(author="me", text='bad work!', birthday=date(3000, 12, 9))
# user.save()

# for book in Book.filter(author="me"):
#     print(book.text, ' ', book.birthday)

HOST = "127.0.0.1"
PORT = 9999
send_queues = {}
lock = threading.Lock()


def handle_client_recv(sock, addr):
    """
    Receive messages from client and broadcast them to
    other clients until client disconnects
    """
    while True:
        data = sock.recv(4096)
        logger.info("Got data from {}; {}".format(sock.getpeername(), data.decode("utf-8")))
        print("Got data from", sock.getpeername(), data.decode("utf-8"))
        if not data:
            handle_disconnect(sock)
            break

        broadcast(data, addr, sock.fileno())


def handle_client_send(sock, addr, q):
    """ Monitor queue for new messages, send them to client as
        they arrive """
    while True:
        msg = q.get()
        if msg is None:
            break
        try:
            logger.info("Send data from {} to {}; data: {}".format(msg[0], addr, msg[1].decode('utf-8')))
            res = "{}: {}".format(msg[0], msg[1].decode('utf-8'))
            sock.send(res.encode("utf-8"))
        except (IOError, ):
            handle_disconnect(sock)
            break


def broadcast(data, addr, info):
    """
    Add message to each connected client's send queue
    """
    print("Broadcast:", data.decode('utf-8'))

    with lock:
        for q in send_queues.keys():
            if q != info:
                send_queues[q].put([addr, data])


def handle_disconnect(sock):
    """
    Ensure queue is cleaned up and socket closed when a client
    disconnects
    """
    fd = sock.fileno()
    with lock:
        # Get send queue for this client
        q = send_queues.get(fd, None)

    # If we find a queue then this disconnect has not yet
    # been handled
    if q:
        q.put(None)
        del send_queues[fd]
        addr = sock.getpeername()
        logger.info('Client {} disconnected'.format(addr))
        print('Client {} disconnected'.format(addr))
        sock.close()


def main():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((HOST, PORT))
    listen_sock.listen(100)

    while True:
        client_sock, addr = listen_sock.accept()
        user = User
        try:
            tupl = user.select().where(user.user_id == addr).get()
        except:
            tupl = 0

        if tupl == 0:
            user = User.create(user_id=addr, info="yours info!")
        else:
            # tupl = user.select().where(user.user_id == addr).first()
            info = tupl[1]
            client_sock.sendto(info, addr)

        # user.save()

        q = queue.Queue()

        with lock:
            send_queues[client_sock.fileno()] = q

        threading.Thread(
            target=handle_client_recv,
            args=[client_sock, addr], daemon=True
        ).start()
        threading.Thread(
            target=handle_client_send,
            args=[client_sock, addr, q], daemon=True
        ).start()
        logger.info('Connection from {}'.format(addr))
        print('Connection from {}'.format(addr))


if __name__ == '__main__':
    main()