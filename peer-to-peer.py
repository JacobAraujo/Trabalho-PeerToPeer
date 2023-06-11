import random
import ast
import socket
import threading
import time

class Peer:
    def __init__(self, node_id, ip_address):
        self.node_id = node_id
        self.ip_address = ip_address
        self.successor = ip_address # endereço do sucessor
        self.data = {}  # Dados armazenados no nó
        self.statusNetwork = False # status pra saber se o nó esta na rede
        self.statusNetworkCondition = threading.Condition() # serve para saber se a status network mudou
        
        #self.lock = threading.Lock() # chamando self.lock.acquire(). Após concluir as operações nos dados protegidos, a thread deve liberar o bloqueio chamando self.lock.release(), permitindo que outras threads possam adquiri-lo.
    
    # connect -> se uma nó 4 pede pra se conectar na rede peo nó 3 que tem sucessor 1 e anterior 2 então
    #            ele vai ter como sucessor o 1 e anterior o 3, já o 3 agora tem como sucessor o 4 ao inves do 1
    #            então o connect vai ser responsavel por:
    #            mandar uma mensagem para o nó existente com o seu endereço e vai receber o endereço do nó
    #            (que agora vai ser o sucessor do nó existente)e vai receber o sucessor do nó existente
    #            (que vai ser seu sucessor) e o endereço do nó existente que vai ser seu anterior
    #            duvida: se ele vai se conectar a partir do ip do nó existente não precisa receber
    
    # quando um novo nó se conectar ele tem que avisar ao sucessor dele para atualizar o previous. O previous serve pra alguma coisa?
    
    def connect_peer(self, ip_existing):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        existing_peer_address = (ip_existing, 5000)
        
        peer_socket.connect(existing_peer_address) # se conecta com o nó que já está na rede

        message = 'connection {}'.format(self.ip_address)
        peer_socket.sendall(message.encode()) # manda uma mensagem para se conectar
         
        response = peer_socket.recv(1024)
        successor_address = response.decode()
        
        self.successor = successor_address # sucessor é o sucessor nó que ja estava na rede
        self.statusNetwork = True 
         
    def put(self, name, number):
        self.data[name] = number


    # funcao que vai tentar se conectar com o seu sucessor para saber se ele ainda está ativo
    def verification(self):
        with self.statusNetworkCondition:
            while not self.statusNetwork:
                self.statusNetworkCondition.wait()  # Aguarda a alteração de self.statusNetwork
            while self.statusNetwork: 
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
                successor_address = (self.successor, 5000)

                try:
                    peer_socket.settimeout(1)  # Define um tempo limite de 10 segundos para a conexão
                    peer_socket.connect(successor_address)   
                    message = 'verification p2p'
                    peer_socket.sendall(message.encode()) # manda uma mensagem de veirficacao
                              
                except socket.timeout:
                    print('\nO sucessor saiu da rede') # aqui colocar o tratamento da saida do sucessor
                except ConnectionRefusedError:
                    print('A conexão com o sucessor falhou') # aqui colocar o tratamento da saida do sucessor
                finally:
                    peer_socket.close()
                time.sleep(5) # manda mensagem de verificacao a cada 5 segundos
                
    def received_mensage(self): # recebe todas as mensagens do peer e trata de acordo com o cabeçalho
        while 1:
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_address = ("", 5000)  # Deixe o primeiro argumento vazio para receber conexões em qualquer endereço IP disponível
            listen_socket.bind(listen_address)
            listen_socket.listen(5)

            connection_socket, address = listen_socket.accept() # espera uma conexão para aceitar
            
            # Receber a mensagem enviada pelo nó conectando
            data = connection_socket.recv(1024)
            received_message = data.decode().split(' ')
            
            if received_message[0] == 'verification':
                continue
            if received_message[0] == 'search': # falta fazer
                print('procura contato')     
            if received_message[0] == 'connection': # algum peer quer se conectar com esse peer
                mensage = self.successor  
                connection_socket.sendall(mensage.encode()) # manda o sucessor 
                self.successor = received_message[1] # o novo nó agora é sucessor do nó antigo  
                self.statusNetwork = True
                with self.statusNetworkCondition:
                    self.statusNetworkCondition.notify_all() # notifica as threads que mudou a variavel network condition -> resolve o problema de verification nao inciar no primeiro nó da rede
                print("Conexão recebida de:", address)
             # Fechar a conexão do socket de conexão
            connection_socket.close()

            # Fechar o socket de escuta
            listen_socket.close()      
            
            if not self.statusNetwork:
                break         

def main():
    id = random.randint(0, 10000) # talvez mude depois para adequar ao formato dht
    ip = input('Insira seu ip: ')
    
    peer = Peer(id, ip)
    
    menu = input('1 - Conexão\n2 - Não conectar \nEscolha: ')
    if menu == '1':
        ipRede = input('Insira o endereço de um nó na rede: ')
        peer.connect_peer(ipRede)
        
    receive_thread = threading.Thread(target=peer.received_mensage) # therad independente do fluxo principal para ficar mandando a verificacao
    receive_thread.daemon = True # serve para encerrar a thread junto com o programa principal
    receive_thread.start()      
    
    verify_thread = threading.Thread(target=peer.verification) # thread independente do fluxo principal para ficar tratando as mensagens
    verify_thread.daemon = True
    verify_thread.start()
 
    while True:
        # criar uma thred para responder uma verificacao para saber se o peer ainda esta na rede
        if peer.statusNetwork:
            menu = input('1 - Exibir sucessor e anterior\n2 - Sair da rede \nEscolha: ')
            if menu == '1':
                print('\nSucessor = {}\nStatus: {}'.format(peer.successor, peer.statusNetwork))
            elif menu == '2': 
                peer.statusNetwork = False
                break
            
main()
        
        
    
    
    
    
