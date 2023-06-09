import random
import ast
import socket
import threading

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.conected_peers = []
        self.clients_lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

    def start(self):
        print('Aguardando conexões dos clientes...')
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        print('henddle - 2\n')
        print('Conexão estabelecida com o cliente:', client_address)

        with self.clients_lock:
            self.clients.append(client_socket)
            self.conected_peers.append(client_address)
            clientList = []
            for addr in self.clients:
                if client_address[0] != addr.getpeername()[0]:
                    clientList.append(addr.getpeername()) 
            print('Clientes conectados:', clientList)
        
        message = f'{clientList}'
        print('\nenviando - 3' + str(message))
        client_socket.send(message.encode())

    def send_client_list(self, client_socket):
        with self.clients_lock:
            client_list = [addr.getpeername() for addr in self.clients]

        if client_socket is not None:
            message = f'Clientes conectados: {client_list}'
            client_socket.send(message.encode())
        else:
            print('Clientes conectados:', client_list)


    def send_message_to_client(self, client_socket, message):
        parts = message.split()
        if len(parts) >= 3:
            client_name = parts[1]
            message = ' '.join(parts[2:])
            with self.clients_lock:
                for client in self.clients:
                    if client.getpeername() == client_name:
                        client.send(message.encode())
                        break

    def connect_to_peer(self, peer_host):
        peer_port = 8080  # Porta padrão para a conexão com o peer
        print('conectando - 1\n')
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((peer_host, peer_port))
            
            # Chamar o método handle_client diretamente
            self.handle_client(client_socket, client_socket.getpeername())
            
            # Receber a lista de clientes conectados do peer existente
            print('\nrecebendo - 4')
            data = client_socket.recv(2048)
            client_list_str = data.decode()
            client_list = ast.literal_eval(client_list_str)
            print('\nRecebido - 5', client_list)
            
            # Estabelecer conexões com os peers já conectados
            for client in client_list:
                client_host, _ = client[0], client[1]
                print('Conectando - 6', client[0], ' com ', client[1])
                self.connect_to_peer(client_host)
        except ConnectionRefusedError:
            print('Não foi possível conectar ao peer:', peer_host)
            client_socket.close()


# Função para lidar com a entrada do usuário e enviar mensagens
def handle_user_input(client):
    while True:
        command = input('Comando: ')
        if command.lower() == 'sair':
            break
        elif command.lower() == 'clientes':
            client.send_client_list(None)
        elif command.startswith('mensagem '):
            parts = command.split()
            if len(parts) >= 3:
                client_name = parts[1]
                message = ' '.join(parts[2:])
                client.send_message_to_client(None, f'mensagem {client_name} {message}')
        else:
            print('Comando inválido!')

# Configuração e inicialização do cliente
client_host = input('Digite IP: ')
client_port = 8080
client = Client(client_host, client_port)
client.start()
print('Port: ', client_port)

# Lidar com a entrada do usuário em uma thread separada
threading.Thread(target=handle_user_input, args=(client,)).start()

# Conectar-se a outros peers (clientes)
peer_host = input('Informe o IP do peer: ')
client.connect_to_peer(peer_host)
