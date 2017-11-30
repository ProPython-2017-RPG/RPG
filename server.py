import socket

HOST = '127.0.0.1'
PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((HOST, PORT))

A = None
B = None

print('Start Serve')

while True:

    try:
        data, addr = sock.recvfrom(1024)
    except:
        break

    if A is None:
        A = addr
    elif addr != A and B is None:
        B = addr

    if addr == A and B is not None:
        sock.sendto(data, B)
    elif addr == B and A is not None:
        sock.sendto(data, A)

print('Close Serve')