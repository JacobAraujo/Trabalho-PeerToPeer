import hashlib
import threading
import socket

class DHTNode:
    def __init__(self, node_id, ip_address):
        self.node_id = node_id
        self.ip_address = ip_address
        self.successor = None
        self.predecessor = None
        self.data = {}  # Dados armazenados no nó
        self.lock = threading.Lock()

    def join(self, existing_node):
        if existing_node is None:
            self.successor = self
            self.predecessor = self
        else:
            self.successor = existing_node
            self.predecessor = existing_node.predecessor
            existing_node.predecessor.successor = self
            existing_node.predecessor = self

    def put(self, key, value):
        hashed_key = hashlib.sha1(key.encode()).hexdigest()
        if self.node_id == hashed_key or self._belongs_to_successor(hashed_key):
            self.data[key] = value
        else:
            self.successor.put(key, value)

    def get(self, key):
        hashed_key = hashlib.sha1(key.encode()).hexdigest()
        if self.node_id == hashed_key or self._belongs_to_successor(hashed_key):
            return self.data.get(key)
        else:
            return self.successor.get(key)

    def _belongs_to_successor(self, key):
        if self.node_id < self.successor.node_id:
            return self.node_id < key <= self.successor.node_id
        else:
            return self.node_id < key or key <= self.successor.node_id

    def print_data(self):
        print(f"Node {self.node_id}: {self.data}")

    def print_ring(self):
        current_node = self
        ring = [current_node.node_id]
        while current_node.successor != self:
            current_node = current_node.successor
            ring.append(current_node.node_id)
        print("Ring: ", "->".join(ring))

    def join_peer(self, existing_ip):
        existing_node = None
        try:
            existing_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            existing_node_socket.connect((existing_ip, 5000))
            existing_node_socket.sendall(f"JOIN {self.node_id} {self.ip_address}".encode())
            response = existing_node_socket.recv(1024).decode()
            if response == "OK":
                existing_node_id, existing_node_ip = existing_node_socket.recv(1024).decode().split()
                existing_node = DHTNode(existing_node_id, existing_node_ip)
        except Exception as e:
            print(f"Error connecting to existing peer: {e}")
        finally:
            existing_node_socket.close()

        self.join(existing_node)

    def find_contact(self, key):
        hashed_key = hashlib.sha1(key.encode()).hexdigest()
        if self.node_id == hashed_key or self._belongs_to_successor(hashed_key):
            return self.ip_address
        else:
            return self.successor.find_contact(key)

    def download_contact(self, key):
        hashed_key = hashlib.sha1(key.encode()).hexdigest()
        if self.node_id == hashed_key or self._belongs_to_successor(hashed_key):
            return self.data.get(key)
        else:
            return self.successor.download_contact(key)

# Exemplo de uso
# node1 = DHTNode('1', '192.168.0.1')
# node2 = DHTNode('2', '192.168.0.2')
# node3 = DHTNode('3', '192.168.0.3')

# node1.join(None)
# node2.join(node1)
# node3.join(node2)

# node1.put('key1', 'value1')
# node2.put('key2', 'value2')
# node3.put('key3', 'value3')

# node1.print_data()  # Node 1: {'key1': 'value1'}
# node2.print_data()  # Node 2: {'key2': 'value2'}
# node3.print_data()  # Node 3: {'key3': 'value3'}

# node1.print_ring()  # Ring: 1->3->2
# node2.print_ring()  # Ring: 2->1->3
# node3.print_ring()  # Ring: 3->2->1

# contact_key = 'key2'
# contact_ip = node1.find_contact(contact_key)
# print(f"Contact IP for '{contact_key}': {contact_ip}")  # Contact IP for 'key2': 192.168.0.2

# contact_key = 'key3'
# contact_value = node1.download_contact(contact_key)
# print(f"Contact value for '{contact_key}': {contact_value}")  # Contact value for 'key3': value3

#Exemplo de uso 2

# Criando os nós da rede
node1 = DHTNode('1', '192.168.0.1')
node2 = DHTNode('2', '192.168.0.2')
node3 = DHTNode('3', '192.168.0.3')
node4 = DHTNode('4', '192.168.0.4')
node5 = DHTNode('5', '192.168.0.5')

# Realizando a junção dos nós na rede
node1.join(None)
node2.join(node1)
node3.join(node2)
node4.join(node3)
node5.join(node4)

# Adicionando dados aos nós
node1.put('key1', 'value1')
node2.put('key2', 'value2')
node3.put('key3', 'value3')
node4.put('key4', 'value4')
node5.put('key5', 'value5')

# Exibindo os dados e a configuração do anel para cada nó
node1.print_data()
node2.print_data()
node3.print_data()
node4.print_data()
node5.print_data()

node1.print_ring()
node2.print_ring()
node3.print_ring()
node4.print_ring()
node5.print_ring()

# Realizando uma busca de contato e download em um dos nós
contact_ip = node1.find_contact('key4')
contact_value = node1.download_contact('key5')

print(f"Contact IP for 'key4': {contact_ip}")
print(f"Contact value for 'key5': {contact_value}")
