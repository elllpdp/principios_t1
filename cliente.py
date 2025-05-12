# Cliente

# Preambulo: Importar librerias
import socket
from getpass import getpass
import os
import threading

def receive_chat_messages(conn):
    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
            print(f"\nEjecutivo: {message}\nCliente: ", end="", flush=True)
        except:
            break

# Crear socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectarse al servidor
client_socket.connect(('localhost', 12345))

# Identificarse como cliente
client_socket.recv(1024)  # Recibir pregunta
client_socket.send("cliente".encode())

# Recibir respuesta del servidor
data = client_socket.recv(1024).decode()
print(f"{data}")
data = client_socket.recv(1024).decode()
print(f"{data}")

# Enviar correo
valid_mail = False
while not valid_mail:
    mail = input("Correo electrónico: ")
    if mail.count("@") == 1 and mail.find(".") != -1 and len(mail) >= 5:
        client_socket.send(mail.encode())
        if client_socket.recv(1024).decode() == "1":
            valid_mail = True
        else:
            print("Correo electrónico no válido. Intente nuevamente.")
    else:
        print("Correo electrónico no válido. Intente nuevamente.")

# Enviar Contraseña
valid_pass = False
while not valid_pass:
    password = getpass("Contraseña: ")
    if len(password) >= 3:
        client_socket.send(password.encode())
        if client_socket.recv(1024).decode() == "1":
            valid_pass = True
        else:
            print("Contraseña no válida. Intente nuevamente.")
    else:
        print("Contraseña no válida. Intente nuevamente.")

# Ingreso Existoso
if valid_mail and valid_pass:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(client_socket.recv(1024).decode())
    exit_flag = False
    chat_socket = None
    chat_thread = None
    
    while not exit_flag:
        print("\n¿Cómo podemos ayudarte?")
        print("[1]: Cambio de Contraseña.")
        print("[2]: Historial de Operaciones.")
        print("[3]: Catálogo de Productos/Comprar Productos.")
        print("[4]: Solicitar Devolución de Productos.")
        print("[5]: Confirmar Recibo.")
        print("[6]: Contactarse con un Ejecutivo.")
        print("[7]: Consultar Saldo en Cuenta/Cargar Saldo.")
        print("[8]: Mis Cartas.")
        print("[9]: Salir.")
        
        ans = input("Escoja una opción: ")
        
        # Opción 1: Cambio de contraseña
        if ans == "1":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Cambio de Contraseña")
            newpass = getpass("Ingrese su nueva contraseña: ")
            if len(newpass) >= 3:
                msg = f"{ans}|{newpass}"
                client_socket.send(msg.encode())
                os.system('cls' if os.name == 'nt' else 'clear')
                print(client_socket.recv(1024).decode())
            else: 
                print("INTENTO FALLIDO. LA CONTRASEÑA DEBE TENER, AL MENOS, TRES CARACTERES.")
        
        # Opción 2: Historial de operaciones
        elif ans == "2":
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Historial de Operaciones")
            print("")
            hola = client_socket.recv(1024).decode().split("|")
            for operation in hola:
                print(operation)
            input("Presione Enter para volver al menú anterior.")
            os.system('cls' if os.name == 'nt' else 'clear')
        
        # Opción 3: Catálogo y Compra de Productos
        elif ans == "3":
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Catálogo de Productos")
            print("")
            hola = client_socket.recv(1024).decode().split("|")
            for product in hola:
                print(product)
            print("")
            print("¿Desea adquirir alguno de estos productos?")
            buy = input("De ser así, ingresar su número de catálogo. Sino, presionar otra tecla: ")
            if buy.isdigit():
                n = len(hola)
                if 1 <= int(buy) < n:
                    confirm_buy = input("¿Está seguro que desea comprar este producto? (S/N): ")
                    if confirm_buy.lower() in ["s", "si", "sí"]:
                        client_socket.send(buy.encode())
                        buy_ans = client_socket.recv(1024).decode()
                        if buy_ans == "1":
                            print("Compra realizada exitosamente.")
                        else: 
                            print("Compra no realizada.")
                    else:
                        client_socket.send("0".encode()) 
                        print("Compra no realizada.")
                else: 
                    client_socket.send("0".encode())
                    print("Compra no realizada.")
            else: 
                client_socket.send("0".encode())
                print("Compra no realizada.")
        
        # Opción 4: Devolución
        elif ans == "4":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Por favor contactarse con un ejecutivo.")
            input("Presionar Enter para volver al menú anterior.")
        
        # Opción 5: Confirmar recibo
        elif ans == "5":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Confirmar Recibo")
            print("")
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            confirm_cards = client_socket.recv(1024).decode().split("|")
            hola = ""
            send = True
            if confirm_cards[0] == "0": 
                client_socket.send("0".encode())
                print("No hay envíos que confirmar.")
                input("Presione Enter para volver al menú principal.")
            else: 
                confirm_cards = [c for c in confirm_cards if c]
                for card in confirm_cards:
                    hola1 = input("¿Desea confirmar el recibo de " + card + "? (S/N): ")
                    if hola1.isalpha(): 
                        hola = f"{hola1}|{hola}"
                    else: 
                        print("Acción Inválida. Cancelando Proceso de Confirmación.")
                        client_socket.send("0".encode())
                        send = False
                        break
                if send: 
                    client_socket.send(hola.encode())
        
        # Opción 6: Contactar ejecutivo
        elif ans == "6":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Contactarse con un Ejecutivo")
            print("")
            sure = input("¿Está seguro que desea contactarse con un ejecutivo? (S/N): ")
            if sure.lower() in ["s", "si", "sí"]:
                var = "null"
                msg = f"{ans}|{var}"
                client_socket.send(msg.encode())
                response = client_socket.recv(1024).decode()
                
                if response.startswith("CONNECT:"):
                    port = int(response.split(":")[1])
                    client_socket.send("ready".encode())
                    
                    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    chat_socket.connect(('localhost', port))
                    
                    chat_thread = threading.Thread(target=receive_chat_messages, args=(chat_socket,))
                    chat_thread.daemon = True
                    chat_thread.start()
                    
                    print("\nConectado con ejecutivo. Escribe tu mensaje (escribe 'chao' para terminar):")
                    while True:
                        message = input("Cliente: ")
                        if message.lower() == "chao":
                            chat_socket.close()
                            break
                        chat_socket.send(message.encode())
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                else:
                    print(response)
        
        # Opción 7: Consultar y cargar saldo
        elif ans == "7":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Consultar Saldo o Cargar Saldo")
            print("")
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            balance = client_socket.recv(1024).decode()
            print("Su saldo actual es de $" + balance + ".")
            load = input("¿Desea cargar saldo (S/N)?: ")
            if load.lower() in ["s", "si", "sí"]:
                amount = input("Ingrese la cantidad a cargar: ")
                if amount.isdigit():
                    client_socket.send(amount.encode())
                    carga_valida = client_socket.recv(1024).decode()
                    if carga_valida == "1": 
                        print("Saldo cargado exitosamente (cargo realizado en tarjeta de débito/credito).")
                    else: 
                        print("Carga no realizada.")
                else:
                    print("Operación Inválida.")
                    client_socket.send("0".encode())
            else: 
                print("Carga no realizada.")
                client_socket.send("0".encode())
        
        # Opción 8: Mis cartas
        elif ans == "8":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Mis Cartas:")
            print("")
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            cartas = client_socket.recv(1024).decode().split("|")
            if len(cartas) == 1 and cartas[0] == " ": 
                print("No hay cartas que mostrar.")
            else: 
                for carta in cartas: 
                    print(carta)
            input("Presione Enter para volver al menú principal. ")
        
        # Opción 9: Salir
        elif ans == "9":
            var = "null"
            msg = f"{ans}|{var}"
            client_socket.send(msg.encode())
            print("¡Gracias por su visita!")
            exit_flag = True
            client_socket.close() 
        
        # Opción no reconocida
        else: 
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Operación Invalida. Intente nuevamente.")

# Cerrar conexión
client_socket.close()