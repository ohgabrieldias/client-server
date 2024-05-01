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

intervalos_utilizados = set()

class ClientHandler:
    def __init__(self, client_socket, intervalo, log_callback, connection_log_callback):
        self.client_socket = client_socket
        self.intervalo = intervalo
        self.log_callback = log_callback
        self.connection_log_callback = connection_log_callback

    def decode_server_message(self,socket):
        return socket.recv(1024).decode().strip()
    
    def handle(self, client_address):
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

        # Imprime os resultados recebidos
        self.log_callback(f"\nResultados recebidos do cliente {client_address[0]}:{client_address[1]}:")
        for resultado in resultados:
            self.log_callback(resultado)
        self.log_callback("\n")

        # Fecha a conexão com o cliente
        self.client_socket.close()
        
class Server: # Classe que representa o servidor
    def __init__(self, host, port, max_connections, log_callback, connection_log_callback):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.log_callback = log_callback
        self.connection_log_callback = connection_log_callback
        self.server_socket = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        self.running = False
        self.connections_count = 0
        self.lock = threading.Lock()

    def accept_connections(self):
        while True:
            with self.lock:
                if self.connections_count >= self.max_connections:
                    self.log_callback("Número máximo de conexões atingido. Negando nova conexão.")
                    client_socket, _ = self.server_socket.accept()
                    client_socket.send("Conexão negada: número máximo de conexões atingido.\n".encode())
                    client_socket.close()  # Encerra a conexão com o cliente
                    continue

            client_socket, address = self.server_socket.accept()

            with self.lock:  # Bloqueia o acesso a variável connections_count
                self.connections_count += 1

            intervalo = self.gerar_intervalo_unico()
            client_socket.send(f"{intervalo[0]} {intervalo[1]}\n".encode())

            client_handler = ClientHandler(client_socket, intervalo, self.log_callback, self.connection_log_callback)
            self.executor.submit(client_handler.handle, address)
            self.connection_log_callback(address)  # Registra o endereço do cliente na GUI do servidor

    def start(self):
        while True: # Loop infinito para aceitar novas conexões
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilização do endereço
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen()

                self.log_callback(f"Servidor escutando em {self.host}:{self.port}. Aguardando conexões...")

                self.accept_connections()

            except Exception as e:
                if isinstance(e, RuntimeError) and "cannot schedule new futures after shutdown" in str(e):
                    self.log_callback("Erro no servidor: O servidor foi encerrado e não aceita mais conexões.")
                    break
                elif isinstance(e, OSError) and e.errno == 98:  # Endereço já em uso
                    self.log_callback("Endereço e porta já estão em uso. Tentando novamente em alguns segundos...")
                    time.sleep(5)  # Espera 5 segundos antes de tentar novamente
                    continue
                else:
                    self.log_callback(f"Erro no servidor: {e}")
                    break
            finally:
                if self.server_socket:
                    self.server_socket.close()  # Fecha o socket do servidor quando o servidor é encerrado

        self.log_callback("Servidor parou.")

    def stop(self):
        if self.server_socket:
            self.server_socket.close()
        self.executor.shutdown()
        self.log_callback("Servidor parando.....")

    def gerar_intervalo_unico(self):
        while True:
            segundo_valor = random.randint(1, 1000000)  # Valor aleatório entre 1 e 1000000
            intervalo = (0, segundo_valor)
            if intervalo not in intervalos_utilizados:
                intervalos_utilizados.add(intervalo)
                return intervalo

class ServerWindow(QMainWindow): # Classe que representa a janela do servidor
    def __init__(self):
        super(ServerWindow, self).__init__()
        loadUi("server.ui", self)  # Carrega o arquivo .ui

        self.startServer.clicked.connect(self.iniciar_servidor)
        self.stopServer.clicked.connect(self.parar_servidor)
        self.clearLogs.clicked.connect(self.limpar_logs)

        self.server = None

    def iniciar_servidor(self):
        if not self.server:
            HOST = '127.0.0.1'  # Endereço IP do servidor
            PORTA = 12345        # Porta que o servidor vai escutar
            max_connections = self.maxConnectionsSpinBox.value() # Número máximo de conexões defninido pelo usuário
            self.server = Server(HOST, PORTA, max_connections, self.update_log_info, self.update_connection_log_info)   # Instancia o servidor
            threading.Thread(target=self.server.start).start()  # Inicia o servidor em uma nova thread

    def parar_servidor(self):
        if self.server:
            self.server.stop()
            self.server = None

    def limpar_logs(self):
        self.logInfo.clear()
        self.clientConnect.clear()

    def update_log_info(self, message):
        QtCore.QMetaObject.invokeMethod(self.logInfo, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, message))

    def update_connection_log_info(self, address):
        QtCore.QMetaObject.invokeMethod(self.clientConnect, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Nova conexão de: {address[0]}:{address[1]}"))

    def closeEvent(self, event):
        self.parar_servidor()
        if self.server:
            self.server.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerWindow()
    window.show()
    sys.exit(app.exec_())