import socket

HOST = '127.0.0.1'
PORT = 17070

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((HOST, PORT))

dict = {}

print('Start Serve')

while True:
    data, addr = sock.recvfrom(1024)

    d = int(data[0])
    loggin = data[1:d + 1]

    dict.setdefault(loggin, addr)

    for key, value in dict.items():
        if key != loggin:
            sock.sendto(data, value)