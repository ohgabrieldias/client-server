import random
import socket
import time
import matplotlib.pyplot as plt
import numpy as np
import threading

def conectar_ao_servidor(host, porta):
    start_time = time.time()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, porta))
    except ConnectionRefusedError as e:
        print(str(e))  
        return None, 0  
    end_time = time.time()
    connection_time = end_time - start_time
    return client_socket, connection_time

def receber_intervalo(mensagem):
    start_time = time.time()
    intervalo = mensagem.split()
    if len(intervalo) != 2:
        return None, 0  # Retorna None se a mensagem não contiver um intervalo válido

    a, b = int(intervalo[0]), int(intervalo[1])
    end_time = time.time()
    reception_time = end_time - start_time
    return (a, b), reception_time

def decode_server_message(socket):
    return socket.recv(1024).decode().strip()

def calcular_soma_pares(intervalo):
    start_time = time.time()
    a, b = intervalo
    soma = sum(x for x in range(a, b+1) if x % 2 == 0)
    end_time = time.time()
    calculation_time = end_time - start_time
    return soma, calculation_time

def calcular_soma_impares(intervalo):
    start_time = time.time()
    a, b = intervalo
    soma = sum(x for x in range(a, b+1) if x % 2 != 0)
    end_time = time.time()
    calculation_time = end_time - start_time
    return soma, calculation_time

def calcular_pi(intervalo):
    start_time = time.time()
    a, b = intervalo
    pi = 0
    for i in range(a, b+1):
        sinal = pow(-1, i)
        termo = sinal / (2 * i + 1)
        pi += termo
    end_time = time.time()
    calculation_time = end_time - start_time
    return pi*4, calculation_time

def enviar_resultados(socket, soma_pares, soma_impares, pi):
    mensagem = f"Soma dos números pares: {soma_pares}\n"
    mensagem += f"Soma dos números ímpares: {soma_impares}\n"
    mensagem += f"Cálculo de PI com o intervalo: {pi}\n"

    start_time = time.time()

    socket.send(mensagem.encode())
    mensagem = decode_server_message(socket)
    end_time = time.time()
    print(mensagem)

    sending_time = end_time - start_time
    return sending_time

def calcular_dados(intervalo):
    soma_pares, calculation_time_sum_even = calcular_soma_pares(intervalo)
    soma_impares, calculation_time_sum_odd = calcular_soma_impares(intervalo)
    pi, calculation_time_pi = calcular_pi(intervalo)
    
    return soma_pares, soma_impares, pi, calculation_time_sum_even, calculation_time_sum_odd, calculation_time_pi

def gerar_dados_falsos():
    # Gerando dados falsos para envio ao servidor
    intervalo = (1, 1000000)
    soma_pares = random.randint(1, 1000000)
    soma_impares = random.randint(1, 1000000)
    pi = random.randint(13,14)

    return soma_pares, soma_impares, pi


def client_thread(host, porta, connection_times, response_times, success_count, failure_count):
    client_socket, connection_time = conectar_ao_servidor(host, porta)
    if client_socket is None:
        print("Falha ao conectar ao servidor.")
        failure_count.append(1)
        return
    
    mensagem = decode_server_message(client_socket)
    
    if mensagem.startswith("Conexão negada:"):
        print("Conexão negada: número máximo de conexões atingido.")
        client_socket.close()
        failure_count.append(1)
        return
    
    intervalo, reception_time = receber_intervalo(mensagem)
    if intervalo is None:
        print("Intervalo inválido.")
        client_socket.close()
        return
    
    #soma_pares, soma_impares, pi, calculation_time_sum_even, calculation_time_sum_odd, calculation_time_pi = calcular_dados(intervalo)
    soma_pares, soma_impares, pi = gerar_dados_falsos()

    sending_time = enviar_resultados(client_socket,soma_pares,soma_impares,pi)
    
    response_time = sending_time
    connection_times.append(connection_time)
    response_times.append(response_time)
    client_socket.close()
    success_count.append(1)

def main(num_clientes):
    HOST = '127.0.0.1'  # Endereço IP do servidor
    PORTA = 12345        # Porta que o servidor está escutando

    connection_times = []
    response_times = []
    success_count = []
    failure_count = []

    threads = []

    for _ in range(num_clientes):
        thread = threading.Thread(target=client_thread, args=(HOST, PORTA, connection_times, response_times, success_count, failure_count))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Calculando métricas
    success_count = sum(success_count)
    failure_count = sum(failure_count)
    total_connections = success_count + failure_count
    queue_size = total_connections - success_count  # Aproximação do tamanho da fila
    network_latency = np.array(connection_times)

    # Plotting the graphs
    fig, ax = plt.subplots(2, 1, figsize=(10, 5))

    # Gráfico de pizza para taxa de sucesso/falha
    ax[0].pie([success_count, failure_count], labels=['Sucesso', 'Falha'], autopct='%1.1f%%', startangle=140)
    ax[0].set_title('Taxa de Sucesso/Falha')

    # Histograma para latência da rede
    ax[1].hist(network_latency, bins=20, color='skyblue', edgecolor='black')
    ax[1].set_xlabel('Latência da Rede (s)')
    ax[1].set_ylabel('Frequência')
    ax[1].set_title('Distribuição da Latência da Rede')

    plt.tight_layout()
    plt.show()

    # Plotting the response and connection times
    fig, ax = plt.subplots(2, 1, figsize=(10, 5))

    # Gráfico de barras para tempo médio de resposta do servidor
    ax[0].hist(response_times, bins=20, color='skyblue', edgecolor='black')
    ax[0].set_xlabel('Tempo de Resposta (s)')
    ax[0].set_ylabel('Frequência')
    ax[0].set_title('Distribuição do Tempo de Resposta do Servidor')

    # Gráfico de barras para tempo de conexão
    ax[1].hist(connection_times, bins=20, color='lightgreen', edgecolor='black')
    ax[1].set_xlabel('Tempo de Conexão (s)')
    ax[1].set_ylabel('Frequência')
    ax[1].set_title('Distribuição do Tempo de Conexão')

    plt.tight_layout()
    plt.show()

    fig, ax = plt.subplots(2, 1, figsize=(10, 5))
    #plotar grafico tempo de resposta x numero de conexoes e gra
    ax[0].plot(response_times)
    ax[0].set_xlabel('Número de conexões')
    ax[0].set_ylabel('Tempo de resposta (s)')
    ax[0].set_title('Tempo de resposta x Número de conexões')

    ax[1].plot(connection_times)
    ax[1].set_xlabel('Número de conexões')
    ax[1].set_ylabel('Tempo de conexão (s)')
    ax[1].set_title('Tempo de conexão x Número de conexões')

    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    # Testando com diferentes números de clientes: 100, 1000, 10000
    main(100) # Testando com 100 clientes
    main(1000) # Testando com 1000 clientes
    main(10000) # Testando com 10000 clientes
