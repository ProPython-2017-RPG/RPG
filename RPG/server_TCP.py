import socket
import threading

HOST = '127.0.0.1'
PORT = 17071
RUN = True

players = []

def listen(sock: socket.socket):
    global RUN
    while RUN:
        data = sock.recv(1024)
        for p in players:
            if sock != p:
                p.send(data)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(2)
    print('Start Serve')
    while True:
        client_sock, addr = sock.accept()
        print('New client', addr)
        players.append(client_sock)
        threading.Thread(target=listen, args=(client_sock,)).start()

if __name__ == '__main__':
    main()