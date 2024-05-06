import multiprocessing
import socket
import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from PyQt5.uic import loadUi
import random
import concurrent.futures
import netifaces

intervalos_utilizados = set()

class ClientHandler:
    """
    Classe para lidar com clientes conectados ao servidor.

    Parâmetros:
        client_socket: socket do cliente conectado.
        intervalo: intervalo atribuído ao cliente para cálculos.
        log_callback: função de callback para registrar mensagens de log.
        connection_log_callback: função de callback para registrar conexões.

    Métodos:
        decode_server_message(socket): Decodifica mensagens recebidas do cliente.
        handle(client_address): Manipula a conexão com o cliente.
    """
    def __init__(self, client_socket, intervalo, log_callback, connection_log_callback):
        self.client_socket = client_socket
        self.intervalo = intervalo
        self.log_callback = log_callback
        self.connection_log_callback = connection_log_callback

    def decode_server_message(self, socket):
        """
        Decodifica mensagens recebidas do cliente.

        Parâmetros:
            socket: socket do cliente.

        Retorna:
            Mensagem decodificada.
        """
        return socket.recv(1024).decode().strip()
    
    def handle(self, client_address):
        """
        Manipula a conexão com o cliente.

        Parâmetros:
            client_address: tupla contendo o endereço IP e a porta do cliente.
        """
        a, b = self.intervalo

        # Registra o endereço do cliente na GUI do servidor
        self.log_callback(f"Nova conexão de: {client_address[0]}:{client_address[1]}")

        # Recebe os resultados dos cálculos do cliente
        resultados = []
        while True:
            resultado = self.decode_server_message(self.client_socket)
            if not resultado:
                break
            resultados.append(resultado)
            # Envia uma confirmação de volta para o cliente
            self.client_socket.sendall(b"200 - Sever received the data\n")
        # Imprime os resultados recebidos
        self.log_callback(f"\nResultados recebidos do cliente {client_address[0]}:{client_address[1]}:")
        for resultado in resultados:
            self.log_callback(resultado)
        self.log_callback("\n")

        # Fecha a conexão com o cliente
        self.client_socket.close()

class Server:
    """
    Classe que representa o servidor.

    Parâmetros:
        host: endereço IP do servidor.
        port: porta do servidor.
        max_connections: número máximo de conexões permitidas.
        log_callback: função de callback para registrar mensagens de log.
        connection_log_callback: função de callback para registrar conexões.

    Métodos:
        accept_connections(): Aceita conexões de clientes.
        start(): Inicia o servidor.
        stop(): Para o servidor.
        gerar_intervalo_unico(): Gera um intervalo único para um cliente.
    """
    def __init__(self, host, port, max_connections, log_callback, connection_log_callback):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.log_callback = log_callback
        self.connection_log_callback = connection_log_callback
        self.server_socket = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        self.running = True
        self.connections_count = 0
        self.lock = threading.Lock()

    def accept_connections(self):
        """
        Aceita conexões de clientes.
        """
        while self.running:
            with self.lock:
                if self.connections_count >= self.max_connections:
                    self.log_callback("Número máximo de conexões atingido. Negando nova conexão.")
                    client_socket, _ = self.server_socket.accept()
                    client_socket.send("Conexão negada: número máximo de conexões atingido.\n".encode())
                    client_socket.close()
                    continue

            client_socket, address = self.server_socket.accept()
    
            with self.lock:
                self.connections_count += 1
            print(self.connections_count)
            intervalo = self.gerar_intervalo_unico()
            client_socket.send(f"{intervalo[0]} {intervalo[1]}\n".encode())

            client_handler = ClientHandler(client_socket, intervalo, self.log_callback, self.connection_log_callback)
            self.executor.submit(client_handler.handle, address)
            self.connection_log_callback(address)

    def start(self):
        """
        Inicia o servidor.
        """
        while self.running:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen()

                self.log_callback(f"Servidor escutando em {self.host}:{self.port}. Aguardando conexões...")

                self.accept_connections()

            except Exception as e:
                if isinstance(e, RuntimeError) and "cannot schedule new futures after shutdown" in str(e):
                    self.log_callback("Erro no servidor: O servidor foi encerrado e não aceita mais conexões.")
                    break
                elif isinstance(e, OSError) and e.errno == 98:
                    self.log_callback("Endereço e porta já estão em uso. Tentando novamente em alguns segundos...")
                    time.sleep(5)
                    continue
                else:
                    self.log_callback(f"Erro no servidor: {e}")
                    break
            finally:
                if self.server_socket:
                    self.server_socket.close()

        self.log_callback("Servidor parou.")

    def stop(self):
        """
        Para o servidor.
        """
        if self.server_socket:
            self.server_socket.close()
        for conn in self.executor._threads:
            try:
                conn.client_socket.close()
            except Exception as e:
                print(f"Erro ao fechar a conexão: {e}")
        self.executor.shutdown()
        self.running = False
        self.log_callback("Servidor parando.....")

    def gerar_intervalo_unico(self):
        """
        Gera um intervalo único para um cliente.

        Retorna:
            Intervalo único.
        """
        while True:
            segundo_valor = random.randint(1, 1000000)
            intervalo = (0, segundo_valor)
            if intervalo not in intervalos_utilizados:
                intervalos_utilizados.add(intervalo)
                return intervalo

class ServerWindow(QMainWindow):
    """
    Classe que representa a janela do servidor.
    """
    def __init__(self):
        super(ServerWindow, self).__init__()
        loadUi("server.ui", self)

        self.startServer.clicked.connect(self.iniciar_servidor)
        self.clearLogs.clicked.connect(self.limpar_logs)
        self.stopServer.clicked.connect(self.parar_servidor)
        self.server = None

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

    def iniciar_servidor(self):
        """
        Inicia o servidor.
        """
        if not self.server:
            HOST = self.get_local_ip()
            if HOST:
                print("Endereço IP da máquina na rede local:", HOST)
            PORTA = 12345
            max_connections = self.maxConnectionsSpinBox.value()
            self.server = Server(HOST, PORTA, max_connections, self.update_log_info, self.update_connection_log_info)
            threading.Thread(target=self.server.start).start()

    def parar_servidor(self):
        """
        Para o servidor.
        """
        if self.server:
            self.server.stop()
            self.server = None

    def limpar_logs(self):
        """
        Limpa os logs na interface gráfica.
        """
        self.logInfo.clear()
        self.clientConnect.clear()

    def update_log_info(self, message):
        """
        Atualiza a interface gráfica com mensagens de log.

        Parâmetros:
            message: mensagem de log a ser exibida.
        """
        QtCore.QMetaObject.invokeMethod(self.logInfo, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, message))

    def update_connection_log_info(self, address):
        """
        Atualiza a interface gráfica com informações de conexão.

        Parâmetros:
            address: tupla contendo o endereço IP e a porta do cliente.
        """
        QtCore.QMetaObject.invokeMethod(self.clientConnect, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Nova conexão de: {address[0]}:{address[1]}"))

    def closeEvent(self, event):
        """
        Manipula o evento de fechamento da janela.

        Parâmetros:
            event: evento de fechamento.
        """
        self.parar_servidor()
        if self.server:
            self.server.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerWindow()
    window.show()
    sys.exit(app.exec_())