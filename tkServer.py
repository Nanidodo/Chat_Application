import socket
import threading
from datetime import datetime

# Server configuration
HOST = '127.0.0.1'
PORT = 12340

#'192.168.43.219'
#'192.168.43.245'


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}
nicknames = []

def broadcast(message, client=None):
    for c in clients.values():
        if c != client:
            c.send(message.encode('utf-8'))

def send_user_list():
    user_list = "USERLIST " + " ".join(nicknames)
    for client in clients.values():
        client.send(user_list.encode('utf-8'))

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith('BROADCAST'):
                broadcast(message, client)
            elif message.startswith('PRIVATE'):
                _, sender, recipient, private_message = message.split(' ', 3)
                # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                formatted_message = f"PRIVATE {sender} {recipient} {private_message}"
                if recipient in clients:
                    clients[recipient].send(formatted_message.encode('utf-8'))
                # clients[sender].send(formatted_message.encode('utf-8'))  # Send the message back to the sender as well
        except:
            nickname = [nick for nick, c in clients.items() if c == client][0]
            nicknames.remove(nickname)
            del clients[nickname]
            client.close()
            broadcast(f"BROADCAST {nickname} left the chat.", None)
            send_user_list()
            break

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send("NICK".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients[nickname] = client

        print(f"Nickname of the client is {nickname}")
        broadcast(f"BROADCAST {nickname} joined the chat!", None)
        send_user_list()

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server is listening...")
receive()
