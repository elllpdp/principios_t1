# Servidor

# Preambulo: Importar librerias
import socket
import json
from datetime import datetime
import threading
import time
import atexit
import random

# Cargar Archivo de Usuarios
with open("users.json", "r", encoding="utf-8") as file:
    data = json.load(file)
    file.close()

# Cargar Mails
user_mails = [user['mail'] for user in data['users']]
exec_mails = [executive['mail'] for executive in data['executives']]

# Registra la hora y fecha actual
now = datetime.now() 
year = now.strftime('%Y')

# Recurso compartido simulado
mutex = threading.Lock()

# Lista para almacenar los mensajes
logs = []

# Cola de clientes esperando ejecutivos
executive_queue = []
executive_connections = {}
client_connections = {}

# Función para encontrar puerto disponible
def find_available_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# Función para imprimir y guardar
def log(mensaje):
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    entrada = {
        "timestamp": timestamp,
        "mensaje": str(mensaje)
    }
    logs.append(entrada)
    print(mensaje)
    with open("movimientos.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

# Función para manejar chat directo
def handle_chat(conn1, conn2):
    try:
        while True:
            data = conn1.recv(1024)
            if not data:
                break
            conn2.send(data)
    except:
        pass
    finally:
        conn1.close()
        conn2.close()

# Función para manejar ejecutivos
def manejar_ejecutivo(conn, addr):
    log(f"[SERVER] Ejecutivo conectando desde {addr}")
    mail = None
    try:
        # Autenticación
        conn.send("Bienvenido Ejecutivo a LomavioStore!".encode())
        conn.send("Para ingresar introducir correo electrónico y contraseña.".encode())
        
        # Recibir correo
        valid_mail = False
        while not valid_mail:
            mail = conn.recv(1024).decode()
            is_exec = any(email == mail for email in exec_mails)
            if is_exec:
                conn.send("1".encode())
                valid_mail = True
            else:
                conn.send("0".encode())

        # Verificar contraseña
        password = [e['password'] for e in data['executives'] if e['mail'] == mail][0]
        valid_pass = False
        while not valid_pass:
            recv_password = conn.recv(1024).decode()
            if recv_password == password:
                conn.send("1".encode())
                valid_pass = True
                log(f"[SERVER] Ejecutivo {mail} conectado.")
                executive_connections[mail] = conn
                conn.send(f"Hola {mail}, en este momento hay {threading.active_count()-2} clientes conectados.".encode())
            else:
                conn.send("0".encode())

        # Manejo de comandos del ejecutivo
        while True:
            command = conn.recv(1024).decode()
            
            if command == "status":
                response = f"Clientes conectados: {len(client_connections)}\n"
                response += f"Clientes en espera: {len(executive_queue)}"
                conn.send(response.encode())
                
            elif command == "details":
                response = "Clientes conectados:\n"
                for mail, info in client_connections.items():
                    response += f"{mail} - {info['last_action']}\n"
                conn.send(response.encode())
                
            elif command == "connect":
                if executive_queue:
                    client_conn, client_addr, client_mail = executive_queue.pop(0)
                    direct_port = find_available_port()
                    
                    conn.send(f"CLIENT:{client_mail}".encode())
                    
                    if conn.recv(1024).decode() == "ready":
                        conn.send(str(direct_port).encode())
                        
                        direct_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        direct_socket.bind(('localhost', direct_port))
                        direct_socket.listen(1)
                        
                        exec_conn, exec_addr = direct_socket.accept()
                        client_conn.send(f"CONNECT:{direct_port}".encode())
                        client_conn.recv(1024)
                        
                        client_conn2, client_addr2 = direct_socket.accept()
                        
                        threading.Thread(target=handle_chat, args=(exec_conn, client_conn2)).start()
                        threading.Thread(target=handle_chat, args=(client_conn2, exec_conn)).start()
                        
                        direct_socket.close()
                else:
                    conn.send("No hay clientes en espera.".encode())
                    
            elif command.startswith("buy:"):
                _, client_mail, card_name, price = command.split(":")
                try:
                    price = float(price)
                    user_data = [u for u in data['users'] if u['mail'] == client_mail][0]
                    user_data['balance'] += price
                    user_data['operations'].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Venta de {card_name} por ${price}")
                    with open("users.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    conn.send(f"Compra de {card_name} por ${price} registrada.".encode())
                except Exception as e:
                    conn.send(f"Error: {str(e)}".encode())
                    
            elif command.startswith("publish:"):
                _, card_name, price = command.split(":")
                try:
                    with open("cards.json", "r", encoding="utf-8") as f:
                        cards = json.load(f)
                    
                    new_card = {
                        "name": card_name,
                        "price": float(price),
                        "state": 0
                    }
                    cards['cards'].append(new_card)
                    
                    with open("cards.json", "w", encoding="utf-8") as f:
                        json.dump(cards, f, indent=4)
                    conn.send(f"Carta {card_name} publicada por ${price}.".encode())
                except Exception as e:
                    conn.send(f"Error: {str(e)}".encode())
                    
            elif command.startswith("history:"):
                _, client_mail = command.split(":")
                user_data = [u for u in data['users'] if u['mail'] == client_mail][0]
                response = "\n".join(user_data['operations'][-10:])
                conn.send(response.encode())
                
            elif command.startswith("operations:"):
                _, client_mail = command.split(":")
                user_data = [u for u in data['users'] if u['mail'] == client_mail][0]
                response = "\n".join(user_data['operations'])
                conn.send(response.encode())
                
            elif command == "catalogue":
                with open("cards.json", "r", encoding="utf-8") as f:
                    cards = json.load(f)
                response = "\n".join([f"{c['name']}: ${c['price']}" for c in cards['cards']])
                conn.send(response.encode())
                
            elif command == "exit":
                break
                
    except Exception as e:
        log(f"[SERVER] Error con ejecutivo {addr}: {e}")
    finally:
        if mail in executive_connections:
            del executive_connections[mail]
        conn.close()
        log(f"[SERVER] Ejecutivo {mail} desconectado.")

# Función que maneja cada cliente
def manejar_cliente(conn, addr):
    log(f"[SERVER] Conectando a {addr}")
    client_mail = None
    try:
        conn.send("Bienvenido a LomavioStore!".encode())
        conn.send("Para ingresar introducir correo electrónico y contraseña.".encode())
        
        # Recibir correo
        valid_mail = False
        while not valid_mail:
            mail = conn.recv(1024).decode()
            is_user = any(email == mail for email in user_mails)
            if is_user:
                conn.send("1".encode())
                valid_mail = True
                client_mail = mail
            else:
                conn.send("0".encode())

        # Verificar contraseña
        password = [u['password'] for u in data['users'] if u['mail'] == mail][0]
        valid_pass = False
        while not valid_pass:
            recv_password = conn.recv(1024).decode()
            if recv_password == password:
                conn.send("1".encode())
                valid_pass = True
                log(f"[SERVER] Cliente {mail} conectado.")
                client_connections[mail] = {
                    'conn': conn,
                    'last_action': 'Recién conectado'
                }
                user_data = [u for u in data['users'] if u['mail'] == mail][0]
                conn.send(f"¡Bienvenido/a de vuelta, {user_data['user']}!".encode())
            else:
                conn.send("0".encode())

        # Manejo de opciones del cliente
        while True:
            recived = conn.recv(1024).decode()
            if not recived:
                break
                
            if "|" in recived:
                select, info = recived.split("|")
            else:
                select = recived
                info = ""
                
            client_connections[mail]['last_action'] = f"Opción {select} - {datetime.now().strftime('%H:%M:%S')}"
            
            # Opción 6: Contactar ejecutivo
            if select == "6":
                log(f"[SERVER] {mail} solicita ejecutivo")
                executive_queue.append((conn, addr, mail))
                conn.send("Esperando ejecutivo...".encode())
                continue
                
            # Opción 1: Cambio de contraseña
            elif select == "1":
                if len(info) >= 3:
                    user_data = [u for u in data['users'] if u['mail'] == mail][0]
                    user_data['password'] = info
                    user_data['operations'].append(now.strftime("%Y-%m-%d %H:%M:%S") + " Cambio de contraseña")
                    with open("users.json", "w", encoding="utf-8") as file:
                        json.dump(data, file, indent=4)
                        file.close()
                    conn.send("Contraseña cambiada exitosamente.".encode())
                    log("[SERVER] Cambio de contraseña de usuario " + user_data['user'] + " exitoso.")
                else:
                    conn.send("INTENTO FALLIDO.".encode())
                    log("[SERVER] Cambio de contraseña de " + user_data['user'] + "fallido.") 

            # Opción 2: Historial de operaciones
            elif select == "2": 
                user_data = [u for u in data['users'] if u['mail'] == mail][0]
                hola = ""
                for operation in user_data['operations']:
                    sep_operation = operation.split('-')
                    if sep_operation[0] == year:
                        hola = f"{operation}|{hola}"
                conn.send(hola.encode())

            # Opción 3: Catálogo y Compra de Productos
            elif select == "3":
                try: 
                    with open("cards.json", "r", encoding="utf-8") as catalogo:
                        productos = json.load(catalogo)
                        catalogo.close()
                    
                    all_cards = productos['cards']
                    available_cards = [card for card in all_cards if card['state'] == 0]
                    
                    log("[SERVER] " + user_data['user'] + " está revisando el catálogo.")
                    i = 0
                    hola = ""
                    for card in available_cards:
                        i += 1
                        hola1 = str(i) + ": " + card["name"] + " $" + str(card["price"])
                        hola = f"{hola}|{hola1}"
                    conn.send(hola.encode())
                    
                    buy = conn.recv(1024).decode()
                    if buy == "0": 
                        log("[SERVER] Compra de carta cancelada por " + user_data['user'])
                    elif 1 <= int(buy) <= i:
                        user_data = [u for u in data['users'] if u['mail'] == mail][0]
                        if user_data['balance'] >= available_cards[int(buy) - 1]['price']:
                            user_data['balance'] -= available_cards[int(buy) - 1]['price']
                            user_data['operations'].append(now.strftime("%Y-%m-%d %H:%M:%S") + " Compra de " + available_cards[int(buy) - 1]['name'])
                            log("[SERVER] Compra de " + available_cards[int(buy) - 1]['name'] + " por parte de " + user_data['user'])
                            id = all_cards.index(available_cards[int(buy) - 1])
                            user_data['cards'].append(id)
                            available_cards[int(buy) - 1]['state'] = 1
                            with open("users.json", "w", encoding="utf-8") as file:
                                json.dump(data, file, indent=4)
                                file.close()
                            with open("cards.json", "w", encoding="utf-8") as file:
                                json.dump(productos, file, indent=4)
                                file.close()
                            conn.send("1".encode())
                        else: 
                            conn.send("0".encode())
                    else: 
                        conn.send("0".encode())
                except Exception as e:
                    log(f"[SERVER] Error en compra: {str(e)}")
                    conn.send("0".encode())

            # Opción 5: Confirmar recibo
            elif select == "5":
                user_data = [u for u in data['users'] if u['mail'] == mail][0]
                with open("cards.json", "r", encoding="utf-8") as catalogo:
                    productos = json.load(catalogo)
                    catalogo.close()
                all_cards = productos['cards']
                need_confirm = ""
                for card in user_data['cards']:
                    if all_cards[card]["state"] == 1:
                        card_name = all_cards[card]["name"]
                        need_confirm = f"{card_name}|{need_confirm}"
                if len(need_confirm) == 0:
                    need_confirm = "0"
                conn.send(need_confirm.encode())
                
                cards_confirmed = conn.recv(1024).decode().split("|")
                if cards_confirmed != "0" and need_confirm != "0":
                    need_confirm = need_confirm.split("|")
                    need_confirm.remove("")
                    cards_confirmed.remove("")
                    i = 0
                    for confirmation in cards_confirmed:
                        if confirmation.lower() in ["s", "si", "sí"]:
                            all_cards[user_data['cards'][i]]["state"] = 2
                            user_data['operations'].append(now.strftime("%Y-%m-%d %H:%M:%S") + " Recibo de " + all_cards[user_data['cards'][i]]["name"])
                            with open("users.json", "w", encoding="utf-8") as file:
                                json.dump(data, file, indent=4)
                                file.close()
                            with open("cards.json", "w", encoding="utf-8") as file:
                                json.dump(productos, file, indent=4)
                                file.close()
                            log("[SERVER] Recibo Confirmado de " +  all_cards[user_data['cards'][i]]["name"] + " por parte de " + user_data['user'] + ".")
                        i += 1

            # Opción 7: Consultar y cargar saldo
            elif select == "7":
                user_data = [u for u in data['users'] if u['mail'] == mail][0]
                conn.send(str(user_data['balance']).encode())
                amount = conn.recv(1024).decode()
                if amount != "0" and amount.isalpha() == False: 
                    user_data['balance'] += float(amount)
                    user_data['operations'].append(now.strftime("%Y-%m-%d %H:%M:%S") + " Carga de $" + amount)
                    with open("users.json", "w", encoding="utf-8") as file:
                        json.dump(data, file, indent=4)
                        file.close()
                    conn.send("1".encode())
                    log("[SERVER] Carga de $" + amount + " para " + user_data['user'])

            # Opción 8: Mostrar mis cartas
            elif select == "8":
                user_data = [u for u in data['users'] if u['mail'] == mail][0]
                with open("cards.json", "r", encoding="utf-8") as catalogo:
                    productos = json.load(catalogo)
                    catalogo.close()
                all_cards = productos['cards']
                hola = " "
                for card in user_data['cards']:
                    if all_cards[card]["state"] == 1: 
                        msg = "En Envío."
                    elif all_cards[card]["state"] == 2: 
                        msg = "Enviado y Recibo Confirmado."
                    else: 
                        msg = ""
                    hola1 = all_cards[card]["name"] + ": " + msg
                    hola = f"{hola1}|{hola}"
                conn.send(hola.encode())

            # Opción 9: Salir
            elif select == "9":
                log("[SERVER] " + user_data['user'] + " desconectado.")
                break

            # Opción no reconocida
            else:
                conn.send("Opción no reconocida".encode())
                
    except Exception as e:
        log(f"[SERVER] Error con {addr}: {e}")
    finally:
        if client_mail and client_mail in client_connections:
            del client_connections[client_mail]
        conn.close()
        log(f"[SERVER] Conexión cerrada con {addr}")

# Configurar el servidor
HOST = 'localhost'
PORT = 12345
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(12)
log("[*] Servidor escuchando...")

# Bucle principal
while True:
    conn, addr = server_socket.accept()
    # Primer mensaje para identificar si es cliente o ejecutivo
    conn.send("¿Eres cliente o ejecutivo? (cliente/ejecutivo)".encode())
    user_type = conn.recv(1024).decode().lower()
    
    if user_type == "ejecutivo":
        hilo = threading.Thread(target=manejar_ejecutivo, args=(conn, addr))
    else:
        hilo = threading.Thread(target=manejar_cliente, args=(conn, addr))
    hilo.start()
    log(f"[>] Conexiones activas: {threading.active_count() - 1}")