import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
import socket
import netifaces

class ClientWindow(QMainWindow):
    def __init__(self):
        super(ClientWindow, self).__init__()
        loadUi("client.ui", self)  # Carrega o arquivo .ui

        self.startButton.clicked.connect(self.iniciar_calculos)
        self.client_socket = None  # Inicializa o atributo do socket do cliente

    def get_local_ip(self):
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for address_info in addresses[netifaces.AF_INET]:
                    ip_address = address_info.get('addr')
                    if ip_address and ip_address != '127.0.0.1':
                        return ip_address
        return None
    
    def iniciar_calculos(self):
        HOST = self.get_local_ip()
        if HOST:
            print("Endereço IP da máquina na rede local:", HOST)
        PORTA = 12345        # Porta que o servidor está escutando

        # Conecta-se ao servidor
        self.operationLogTextEdit.append("Conectando ao servidor...")
        self.client_socket = self.conectar_ao_servidor(HOST, PORTA)
        if self.client_socket is None:
            self.operationLogTextEdit.append("Falha ao conectar ao servidor.")
            return  # Encerra a função se a conexão falhou
        
        mensagem = self.decode_server_message(self.client_socket)
        
        if mensagem.startswith("Conexão negada:"):
            self.operationLogTextEdit.append("Conexão negada: número máximo de conexões atingido.")
            self.client_socket.close()
            return
        self.operationLogTextEdit.append("\nConexão estabelecida com sucesso.")

        # Recebe o intervalo do servidor
        self.operationLogTextEdit.append("Recebendo intervalo do servidor...")
        intervalo = self.receber_intervalo(mensagem)

        if intervalo is None:
            # Handle case where server rejected connection due to max connections reached
            self.operationLogTextEdit.append("Servidor atingiu o máximo de conexões permitidas. Tente novamente mais tarde.")
            self.client_socket.close()
            return

        self.operationLogTextEdit.append(f"Intervalo recebido: {intervalo}")

        # Calcula os resultados
        self.operationLogTextEdit.append("Calculando resultados...")
        soma_pares = self.calcular_soma_pares(intervalo)
        soma_impares = self.calcular_soma_impares(intervalo)
        pi = self.calcular_pi(intervalo)
        self.operationLogTextEdit.append(f"Soma dos números pares: {soma_pares}")
        self.operationLogTextEdit.append(f"Soma dos números ímpares: {soma_impares}")
        self.operationLogTextEdit.append(f"Cálculo de PI com o intervalo: {pi}")
        # Envia os resultados para o servidor
        self.operationLogTextEdit.append("Enviando resultados para o servidor...")
        self.enviar_resultados(self.client_socket, soma_pares, soma_impares, pi)
        self.operationLogTextEdit.append(self.decode_server_message(self.client_socket))
        self.client_socket.close()

    def decode_server_message(self, socket):
        return socket.recv(1024).decode().strip()
    
    def conectar_ao_servidor(self, host, porta):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((host, porta))
        except ConnectionRefusedError as e:
            print(str(e))  # Imprime a mensagem de erro
            return None  # Retorna None se a conexão falhou
        return client_socket

    def receber_intervalo(self, mensagem):
        if not mensagem:
            return None  # Retorna None se a mensagem estiver vazia

        intervalo = mensagem.split()
        if len(intervalo) != 2:
            return None  # Retorna None se a mensagem não contiver um intervalo válido

        a, b = int(intervalo[0]), int(intervalo[1])
        return a, b


    def calcular_soma_pares(self, intervalo):
        a, b = intervalo
        soma = sum(x for x in range(a, b+1) if x % 2 == 0)
        
        return soma

    def calcular_soma_impares(self, intervalo):
        a, b = intervalo
        soma = sum(x for x in range(a, b+1) if x % 2 != 0)
        return soma
    
    def calcular_pi(self, intervalo):
        a, b = intervalo
        pi = 0
        for i in range(a, b+1):
            sinal = pow(-1, i)
            termo = sinal / (2 * i + 1)
            pi += termo
        return pi*4
    
    def enviar_resultados(self, client_socket, soma_pares, soma_impares, pi):
        try:
            mensagem = f"Soma dos números pares: {soma_pares}\n"
            mensagem += f"Soma dos números ímpares: {soma_impares}\n"
            mensagem += f"Cálculo de PI com o intervalo: {pi}\n"
            client_socket.send(mensagem.encode())
        except BrokenPipeError as e:
            print("Erro ao enviar dados para o servidor. A conexão foi fechada pelo servidor antes do término do envio.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec_())
