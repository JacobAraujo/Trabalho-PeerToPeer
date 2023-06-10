import random
import ast
import socket
import threading

class Peer:
    def __init__(self, node_id, ip_address):
        self.node_id = node_id
        self.ip_address = ip_address
        self.successor = ip_address # endereço do sucessor
        self.previous = ip_address # endereço do anterior
        self.data = {}  # Dados armazenados no nó
        self.statusNetwork = False # indica se o nó está na rede ou não
        
        #self.lock = threading.Lock() # chamando self.lock.acquire(). Após concluir as operações nos dados protegidos, a thread deve liberar o bloqueio chamando self.lock.release(), permitindo que outras threads possam adquiri-lo.
    
    # connect -> se uma nó 4 pede pra se conectar na rede peo nó 3 que tem sucessor 1 e anterior 2 então
    #            ele vai ter como sucessor o 1 e anterior o 3, já o 3 agora tem como sucessor o 4 ao inves do 1
    #            então o connect vai ser responsavel por:
    #            mandar uma mensagem para o nó existente com o seu endereço e vai receber o endereço do nó
    #            (que agora vai ser o sucessor do nó existente)e vai receber o sucessor do nó existente
    #            (que vai ser seu sucessor) e o endereço do nó existente que vai ser seu anterior
    #            duvida: se ele vai se conectar a partir do ip do nó existente não precisa receber
    
    def connect(self, ip_existing):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        existing_peer_address = (ip_existing, 5000)
        
        peer_socket.connect(existing_peer_address)

        message = 'OK'
        peer_socket.sendall(message.encode())
        
        response = peer_socket.recv(1024)
        successor_address = response.decode()
        
        self.successor = successor_address
        self.previous = ip_existing
        
    def receive_connection(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_address = ("", 5000)  # Deixe o primeiro argumento vazio para receber conexões em qualquer endereço IP disponível
        listen_socket.bind(listen_address)
        listen_socket.listen(1)

        print("Aguardando conexões...")
        connection_socket, address = listen_socket.accept() # espera uma conexão para aceitar
        print("Conexão recebida de:", address)
        
        # Receber a mensagem enviada pelo nó conectando
        data = connection_socket.recv(1024)
        received_message = data.decode() 

        if received_message == 'OK':
            mensage = self.successor 
            connection_socket.sendall(mensage.encode())
            self.successor = address # o novo nó agora é sucessor do nó antigo

        # Fechar a conexão do socket de conexão
        connection_socket.close()

        # Fechar o socket de escuta
        listen_socket.close()

def main():
    id = random.randint(0, 10000)
    ip = input('Insira seu ip: ')
    
    peer = Peer(id, ip)
    
    while True:
        menu = input('1 - Conexão\n2 - Não conectar \nEscolha: ')
        if menu == '1':
            ipRede = input('Insira o endereço de um nó na rede: ')
            peer.connect(ipRede)
            peer.statusNetwork = True
        elif menu == '2':
            break
        
    peer.receive_connection()
    
    while True:
        menu = input('1 - Sair da rede \nEscolha: ')
        if menu == 1: 
            print('sair da rede')
            # sair da rede
            
main()
        
        
    
    
    
    
