import random
import ast
import socket
import threading
import time

class Peer:
    def __init__(self, nodeId, ip_address):
        self.nodeId = nodeId
        self.ipAddress = ip_address
        self.successor = ip_address # endereço do sucessor
        self.data = {}  # Dados armazenados no nó
        self.statusNetwork = False # status pra saber se o nó esta na rede
        self.statusNetworkCondition = threading.Condition() # serve para saber se a status network mudou
        self.sendSocketLock = threading.Lock()
        
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

        message = 'connection {}'.format(self.ipAddress)
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
                try: 
                    self.send_data(self.successor, mensage = 'verification p2p')          
                except socket.timeout:
                    print('\nO sucessor saiu da rede') # aqui colocar o tratamento da saida do sucessor
                except ConnectionRefusedError:
                    print('A conexão com o sucessor falhou') # aqui colocar o tratamento da saida do sucessor
                finally:
                    time.sleep(5) # manda mensagem de verificacao a cada 5 segundos
               
    # recebe o nome do contato e verifica se tem em seus dados
    # se tiver retorna o item 'nome: numero'            
    def search(self, name=''):
        if name.lower() in self.data:
            return self.data[name]
        else:
            return False
               
    def __listen(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_address = ("", 5000)  # Deixe o primeiro argumento vazio para receber conexões em qualquer endereço IP disponível
        listen_socket.bind(listen_address)
        listen_socket.listen(5)      
        return listen_socket.accept() 
    
    def send_data(self, address, mensage):
        with self.sendSocketLock:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            addressSocket = (address, 5000)
            peer_socket.connect(addressSocket)
            peer_socket.sendall(mensage.encode())
            peer_socket.close()        
    
    def search_next_peer(self, name, peer_address): 
        try:
            mensage = 'search {} {}'.format(name, peer_address)
            self.send_data(self.successor, mensage)
        except:
            return False
    
    def search_contact(self, name):
        if self.search(name):
            return self.search(name)
        else:
            print('Procurando contato na rede...')
            self.search_next_peer(name, self.ipAddress)
        
     
    def received_mensage(self): # recebe todas as mensagens do peer e trata de acordo com o cabeçalho
        while 1:
            connection_socket, address = self.__listen() # espera uma conexão para aceitar
            
            # Receber a mensagem enviada pelo nó conectando
            data = connection_socket.recv(1024)
            received_message = data.decode().split(' ')
            
            if received_message[0] == 'verification':
                continue
            if received_message[0] == 'NotFound':
                print('O contato não foi encontrado na rede')
            if received_message[0] == 'response':
                name = received_message[2]
                number = received_message[1]
                self.put(name, number)
                print('Contato {}:{} adicionado'.format(name, number))
            if received_message[0] == 'search': 
                connection_socket.close()
                nameContact = received_message[1]
                addressRequest = received_message[2]
                if self.search(nameContact):
                    mensage = 'response {} {}'.format(self.search(nameContact), nameContact)
                    self.send_data(addressRequest, mensage)                
                elif self.successor == addressRequest:
                    self.send_data(addressRequest, 'NotFound contact')
                else:
                    self.search_next_peer(nameContact, addressRequest)
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
            menu = input('1 - Exibir sucessor e anterior\n2 - Procurar contato\n3 - Adicionar contato\n4 - Sair da rede\ \nEscolha: ')
            if menu == '1':
                print('\nSucessor = {}\nStatus: {}'.format(peer.successor, peer.statusNetwork))
            elif menu == '2':
                name = input('Digite o nome do contato: ')
                if peer.search(name):
                    print('Voce já tem esse contato, o número é: {}'.format(peer.search(name)))
                else:
                    peer.search_contact(name)
            elif menu == '3':
                name = input('Nome: ')
                number = input('Número: ')
                peer.put(name, number)
            elif menu == '4': 
                peer.statusNetwork = False
                break
            
main()

# def testSearch():
#     peer = Peer(1, '192.168.100.31')
#     peer.put('Jacob', '988220526')   
    
# testSearch()
        
    
    
    
    
