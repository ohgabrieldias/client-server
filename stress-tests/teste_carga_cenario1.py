import os
import random
import socket
import time
import matplotlib.pyplot as plt
import numpy as np
import threading
import netifaces

def conectar_ao_servidor(host, porta):
    """
    Estabelece uma conexão com o servidor.

    Parâmetros:
        host (str): O endereço IP do servidor.
        porta (int): A porta do servidor.

    Retorna:
        client_socket (socket): O socket cliente conectado ao servidor.
        connection_time (float): O tempo de conexão com o servidor em segundos.
    """
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
    """
    Extrai o intervalo recebido do servidor.

    Parâmetros:
        mensagem (str): A mensagem recebida do servidor.

    Retorna:
        intervalo (tuple): O intervalo (tupla de dois números inteiros).
        reception_time (float): O tempo de recepção da mensagem.
    """
    start_time = time.time()
    intervalo = mensagem.split()
    if len(intervalo) != 2:
        return None, 0  # Retorna None se a mensagem não contiver um intervalo válido

    a, b = int(intervalo[0]), int(intervalo[1])
    end_time = time.time()
    reception_time = end_time - start_time
    return (a, b), reception_time

def decode_server_message(socket):
    """
    Decodifica mensagens recebidas do servidor.

    Parâmetros:
        socket (socket): O socket do servidor.

    Retorna:
        A mensagem decodificada (str).
    """
    return socket.recv(1024).decode().strip()

def calcular_soma_pares(intervalo):
    """
    Calcula a soma dos números pares dentro do intervalo.

    Parâmetros:
        intervalo (tuple): O intervalo de números (tupla de dois números inteiros).

    Retorna:
        soma (int): A soma dos números pares dentro do intervalo.
        calculation_time (float): O tempo de duração do cálculo.
    """
    start_time = time.time()
    a, b = intervalo
    soma = sum(x for x in range(a, b+1) if x % 2 == 0)
    end_time = time.time()
    calculation_time = end_time - start_time
    return soma, calculation_time

def calcular_soma_impares(intervalo):
    """
    Calcula a soma dos números ímpares dentro do intervalo.

    Parâmetros:
        intervalo (tuple): O intervalo de números (tupla de dois números inteiros).

    Retorna:
        soma (int): A soma dos números ímpares dentro do intervalo.
        calculation_time (float): O tempo de duração do cálculo.
    """
    start_time = time.time()
    a, b = intervalo
    soma = sum(x for x in range(a, b+1) if x % 2 != 0)
    end_time = time.time()
    calculation_time = end_time - start_time
    return soma, calculation_time

def calcular_pi(intervalo):
    """
    Calcula o valor de PI utilizando a fórmula de Leibniz.

    Parâmetros:
        intervalo (tuple): O intervalo de números (tupla de dois números inteiros).

    Retorna:
        pi (float): O valor de PI calculado.
        calculation_time (float): O tempo de duração do cálculo.
    """
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
    """
    Envia os resultados dos cálculos para o servidor.

    Parâmetros:
        socket (socket): O socket do cliente conectado ao servidor.
        soma_pares (int): A soma dos números pares.
        soma_impares (int): A soma dos números ímpares.
        pi (float): O valor de PI calculado.

    Retorna:
        sending_time (float): O tempo de duração do envio.
    """
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
    """
    Calcula os resultados dos cálculos.

    Parâmetros:
        intervalo (tuple): O intervalo de números (tupla de dois números inteiros).

    Retorna:
        soma_pares (int): A soma dos números pares.
        soma_impares (int): A soma dos números ímpares.
        pi (float): O valor de PI calculado.
        calculation_time_sum_even (float): O tempo de duração do cálculo da soma dos números pares.
        calculation_time_sum_odd (float): O tempo de duração do cálculo da soma dos números ímpares.
        calculation_time_pi (float): O tempo de duração do cálculo de PI.
    """
    soma_pares, calculation_time_sum_even = calcular_soma_pares(intervalo)
    soma_impares, calculation_time_sum_odd = calcular_soma_impares(intervalo)
    pi, calculation_time_pi = calcular_pi(intervalo)
    
    return soma_pares, soma_impares, pi, calculation_time_sum_even, calculation_time_sum_odd, calculation_time_pi

def gerar_dados_falsos():
    """
    Gera dados falsos para envio ao servidor.

    Retorna:
        soma_pares (int): A soma dos números pares falsos.
        soma_impares (int): A soma dos números ímpares falsos.
        pi (float): O valor de PI falso.
    """
    intervalo = (1, 1000000)
    soma_pares = random.randint(1, 1000000)
    soma_impares = random.randint(1, 1000000)
    pi = random.randint(13,14)

    return soma_pares, soma_impares, pi


def client_thread(host, porta, connection_times, response_times, success_count, failure_count):
    """
    Função a ser executada em cada thread do cliente.

    Parâmetros:
        host (str): O endereço IP do servidor.
        porta (int): O número da porta do servidor.
        connection_times (list): Lista para armazenar os tempos de conexão.
        response_times (list): Lista para armazenar os tempos de resposta.
        success_count (list): Lista para armazenar os sucessos de conexão.
        failure_count (list): Lista para armazenar as falhas de conexão.
    """
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

def save_graphs(N, success_count, failure_count, network_latency, response_times, connection_times):
    """
    Salva os gráficos gerados.

    Parâmetros:
        N (int): O número de clientes.
        success_count (int): O número de conexões bem-sucedidas.
        failure_count (int): O número de conexões falhadas.
        network_latency (numpy.array): Array com os tempos de latência da rede.
        response_times (list): Lista com os tempos de resposta.
        connection_times (list): Lista com os tempos de conexão.
    """
    # Obter o diretório atual do script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Criar o diretório para salvar os gráficos
    folder_name = os.path.join(current_dir, str(N))
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Gráfico de pizza para taxa de sucesso/falha
    fig, ax = plt.subplots(2, 1, figsize=(10, 5))
    ax[0].pie([success_count, failure_count], labels=['Sucesso', 'Falha'], autopct='%1.1f%%', startangle=140)
    ax[0].set_title('Taxa de Sucesso/Falha')

    # Histograma para latência da rede
    ax[1].hist(network_latency, bins=20, color='skyblue', edgecolor='black')
    ax[1].set_xlabel('Latência da Rede (s)')
    ax[1].set_ylabel('Frequência')
    ax[1].set_title('Distribuição da Latência da Rede')

    plt.tight_layout()
    plt.savefig(os.path.join(folder_name, 'taxa_sucesso_falha_e_latencia.png'))
    plt.close()

    # Gráfico de barras para tempo médio de resposta do servidor
    fig, ax = plt.subplots(2, 1, figsize=(10, 5))
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
    plt.savefig(os.path.join(folder_name, 'distribuicao_tempo_resposta_e_conexao.png'))
    plt.close()

    # Gráfico de linhas para tempo de resposta x número de conexões e tempo de conexão x número de conexões
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
    plt.savefig(os.path.join(folder_name, 'tempo_resposta_e_conexao_x_num_conexoes.png'))
    plt.close()


def get_local_ip():
    """
    Obtém o endereço IP local da máquina.

    Retorna:
        ip_address (str): O endereço IP local da máquina.
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

def main(num_clientes):
    """
    Função principal para testar o desempenho do servidor com um número específico de clientes.

    Parâmetros:
        num_clientes (int): O número de clientes a serem simulados.
    """
    HOST = get_local_ip()
    if HOST:
        print("Endereço IP da máquina na rede local:", HOST)
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

    save_graphs(num_clientes, success_count, failure_count, network_latency, response_times, connection_times)

if __name__ == "__main__":
    # Testando com diferentes números de clientes: 100, 1000, 10000
    main(100) # Testando com 100 clientes
    main(1000) # Testando com 1000 clientes
    main(10000) # Testando com 10000 clientes