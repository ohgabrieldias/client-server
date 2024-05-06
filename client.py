import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
import socket
import netifaces

class ClientWindow(QMainWindow):
    """
    Classe que representa a janela do cliente.

    Métodos:
        get_local_ip(): Obtém o endereço IP da máquina na rede local.
        iniciar_calculos(): Inicia o processo de cálculos e comunicação com o servidor.
        decode_server_message(socket): Decodifica mensagens recebidas do servidor.
        conectar_ao_servidor(host, porta): Conecta-se ao servidor.
        receber_intervalo(mensagem): Extrai o intervalo recebido do servidor.
        calcular_soma_pares(intervalo): Calcula a soma dos números pares dentro do intervalo.
        calcular_soma_impares(intervalo): Calcula a soma dos números ímpares dentro do intervalo.
        calcular_pi(intervalo): Calcula o valor de PI utilizando a fórmula de Leibniz.
        enviar_resultados(client_socket, soma_pares, soma_impares, pi): Envia os resultados dos cálculos para o servidor.
    """
    def __init__(self):
        super(ClientWindow, self).__init__()
        loadUi("client.ui", self)

        self.startButton.clicked.connect(self.iniciar_calculos)
        self.client_socket = None

    def get_local_ip(self):
        """
        Obtém o endereço IP da máquina na rede local.

        Retorna:
            Endereço IP da máquina na rede local.
        """
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
        """
        Inicia o processo de cálculos e comunicação com o servidor.
        """
        HOST = self.get_local_ip()
        if HOST:
            print("Endereço IP da máquina na rede local:", HOST)
        PORTA = 12345

        self.operationLogTextEdit.append("Conectando ao servidor...")
        self.client_socket = self.conectar_ao_servidor(HOST, PORTA)
        if self.client_socket is None:
            self.operationLogTextEdit.append("Falha ao conectar ao servidor.")
            return
        
        mensagem = self.decode_server_message(self.client_socket)
        
        if mensagem.startswith("Conexão negada:"):
            self.operationLogTextEdit.append("Conexão negada: número máximo de conexões atingido.")
            self.client_socket.close()
            return
        self.operationLogTextEdit.append("\nConexão estabelecida com sucesso.")

        self.operationLogTextEdit.append("Recebendo intervalo do servidor...")
        intervalo = self.receber_intervalo(mensagem)

        if intervalo is None:
            self.operationLogTextEdit.append("Servidor atingiu o máximo de conexões permitidas. Tente novamente mais tarde.")
            self.client_socket.close()
            return

        self.operationLogTextEdit.append(f"Intervalo recebido: {intervalo}")

        self.operationLogTextEdit.append("Calculando resultados...")
        soma_pares = self.calcular_soma_pares(intervalo)
        soma_impares = self.calcular_soma_impares(intervalo)
        pi = self.calcular_pi(intervalo)
        self.operationLogTextEdit.append(f"Soma dos números pares: {soma_pares}")
        self.operationLogTextEdit.append(f"Soma dos números ímpares: {soma_impares}")
        self.operationLogTextEdit.append(f"Cálculo de PI com o intervalo: {pi}")

        self.operationLogTextEdit.append("Enviando resultados para o servidor...")
        self.enviar_resultados(self.client_socket, soma_pares, soma_impares, pi)
        self.operationLogTextEdit.append(self.decode_server_message(self.client_socket))
        self.client_socket.close()

    def decode_server_message(self, socket):
        """
        Decodifica mensagens recebidas do servidor.

        Parâmetros:
            socket: socket do servidor.

        Retorna:
            Mensagem decodificada.
        """
        return socket.recv(1024).decode().strip()
    
    def conectar_ao_servidor(self, host, porta):
        """
        Conecta-se ao servidor.

        Parâmetros:
            host: endereço IP do servidor.
            porta: porta do servidor.

        Retorna:
            Socket do cliente conectado ao servidor.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((host, porta))
        except ConnectionRefusedError as e:
            print(str(e))
            return None
        return client_socket

    def receber_intervalo(self, mensagem):
        """
        Extrai o intervalo recebido do servidor.

        Parâmetros:
            mensagem: mensagem recebida do servidor.

        Retorna:
            Intervalo (tupla de dois números inteiros) ou None se a mensagem for inválida.
        """
        if not mensagem:
            return None

        intervalo = mensagem.split()
        if len(intervalo) != 2:
            return None

        a, b = int(intervalo[0]), int(intervalo[1])
        return a, b


    def calcular_soma_pares(self, intervalo):
        """
        Calcula a soma dos números pares dentro do intervalo.

        Parâmetros:
            intervalo: tupla contendo os limites do intervalo.

        Retorna:
            Soma dos números pares dentro do intervalo.
        """
        a, b = intervalo
        soma = sum(x for x in range(a, b+1) if x % 2 == 0)
        
        return soma

    def calcular_soma_impares(self, intervalo):
        """
        Calcula a soma dos números ímpares dentro do intervalo.

        Parâmetros:
            intervalo: tupla contendo os limites do intervalo.

        Retorna:
            Soma dos números ímpares dentro do intervalo.
        """
        a, b = intervalo
        soma = sum(x for x in range(a, b+1) if x % 2 != 0)
        return soma
    
    def calcular_pi(self, intervalo):
        """
        Calcula o valor de PI utilizando a fórmula de Leibniz.

        Parâmetros:
            intervalo: tupla contendo os limites do intervalo.

        Retorna:
            Valor de PI calculado.
        """
        a, b = intervalo
        pi = 0
        for i in range(a, b+1):
            sinal = pow(-1, i)
            termo = sinal / (2 * i + 1)
            pi += termo
        return pi*4
    
    def enviar_resultados(self, client_socket, soma_pares, soma_impares, pi):
        """
        Envia os resultados dos cálculos para o servidor.

        Parâmetros:
            client_socket: socket do cliente conectado ao servidor.
            soma_pares: soma dos números pares.
            soma_impares: soma dos números ímpares.
            pi: valor de PI calculado.
        """
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