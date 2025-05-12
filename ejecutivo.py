# Ejecutivo

import socket
from getpass import getpass
import os
import threading
import sys

# Crear socket
executive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectarse al servidor
executive_socket.connect(('localhost', 12345))

# Variables globales
current_client = None
chat_socket = None
chat_thread = None
in_chat = False

def receive_chat_messages():
    global in_chat
    while True:
        try:
            message = chat_socket.recv(1024).decode()
            if not message:
                break
            print(f"\nCliente: {message}")
            if in_chat:
                print("Ejecutivo: ", end="", flush=True)
        except:
            break

def authenticate():
    try:
        # Paso 1: Recibir pregunta de identificación
        pregunta = executive_socket.recv(1024).decode()
        if not pregunta:
            print("Error: No se recibió pregunta de identificación del servidor")
            return False

        # Paso 2: Responder que somos ejecutivo
        executive_socket.send("ejecutivo".encode())

        # Paso 3: Recibir mensaje de bienvenida
        welcome1 = executive_socket.recv(1024).decode()
        welcome2 = executive_socket.recv(1024).decode()
        print(f"{welcome1}\n{welcome2}")

        # Verificación de correo
        valid_mail = False
        while not valid_mail:
            mail = input("Correo electrónico: ").strip()
            if mail.count("@") == 1 and mail.find(".") != -1 and len(mail) >= 5:
                executive_socket.send(mail.encode())
                response = executive_socket.recv(1024).decode()
                if response == "1":
                    valid_mail = True
                else:
                    print("Correo no válido o no es de ejecutivo. Intente nuevamente.")
            else:
                print("Formato de correo no válido. Intente nuevamente.")

        # Verificación de contraseña
        valid_pass = False
        while not valid_pass:
            password = getpass("Contraseña: ").strip()
            if len(password) >= 3:
                executive_socket.send(password.encode())
                response = executive_socket.recv(1024).decode()
                if response == "1":
                    valid_pass = True
                    welcome = executive_socket.recv(1024).decode()
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(welcome)
                    return True
                else:
                    print("Contraseña incorrecta. Intente nuevamente.")
            else:
                print("La contraseña debe tener al menos 3 caracteres.")
                
    except Exception as e:
        print(f"Error durante autenticación: {str(e)}")
    
    return False

def show_menu():
    print("\nComandos disponibles:")
    print(":status - Muestra clientes conectados y solicitudes")
    print(":details - Muestra detalles de clientes conectados")
    print(":connect - Conectarse con un cliente en espera")
    print(":history - Historial del cliente actual")
    print(":operations - Historial completo del cliente actual")
    print(":catalogue - Mostrar catálogo de cartas")
    print(":buy [carta] [precio] - Comprar carta al cliente")
    print(":publish [carta] [precio] - Publicar carta en venta")
    print(":disconnect - Desconectar del cliente actual")
    print(":exit - Salir del sistema\n")

def handle_chat_session():
    global in_chat, current_client, chat_socket
    
    print("\nChat iniciado. Escribe tus mensajes (escribe ':disconnect' para terminar).")
    print("Ejecutivo: ", end="", flush=True)
    in_chat = True
    
    while in_chat:
        try:
            message = input()
            if message.lower() == ":disconnect":
                executive_socket.send(f"disconnect:{current_client}".encode())
                chat_socket.close()
                current_client = None
                in_chat = False
                print("\nChat finalizado.")
                break
            else:
                chat_socket.send(message.encode())
                print("Ejecutivo: ", end="", flush=True)
        except Exception as e:
            print(f"\nError en el chat: {str(e)}")
            in_chat = False
            break

def main():
    global current_client, chat_socket, chat_thread, in_chat
    
    if not authenticate():
        print("Error de autenticación. Saliendo...")
        executive_socket.close()
        return
    
    exit_flag = False
    while not exit_flag:
        if not in_chat:
            show_menu()
        
        try:
            if in_chat:
                handle_chat_session()
                continue
                
            command = input("Ejecutivo: " if not in_chat else "").strip()
            
            if command == ":status":
                executive_socket.send("status".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\n{response}")
                
            elif command == ":details":
                executive_socket.send("details".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\n{response}")
                
            elif command == ":connect":
                if current_client:
                    print("\nYa estás conectado con un cliente. Usa :disconnect primero.\n")
                    continue
                    
                executive_socket.send("connect".encode())
                response = executive_socket.recv(1024).decode()
                
                if response.startswith("CLIENT:"):
                    current_client = response.split(":")[1]
                    print(f"\nConectado con cliente: {current_client}")
                    
                    executive_socket.send("ready".encode())
                    port = int(executive_socket.recv(1024).decode())
                    
                    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    chat_socket.connect(('localhost', port))
                    
                    chat_thread = threading.Thread(target=receive_chat_messages)
                    chat_thread.daemon = True
                    chat_thread.start()
                    
                    handle_chat_session()
                    
                else:
                    print(f"\n{response}")
                    
            elif command.startswith(":buy"):
                if not current_client:
                    print("\nNo estás conectado con ningún cliente.\n")
                    continue
                    
                parts = command.split()
                if len(parts) != 3:
                    print("\nFormato incorrecto. Usa: :buy [carta] [precio]\n")
                    continue
                    
                card_name = parts[1]
                price = parts[2]
                executive_socket.send(f"buy:{current_client}:{card_name}:{price}".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\n{response}")
                
            elif command.startswith(":publish"):
                parts = command.split()
                if len(parts) < 2:
                    print("\nFormato incorrecto. Usa: :publish [carta] [precio]\n")
                    continue
                    
                card_name = parts[1]
                price = parts[2] if len(parts) > 2 else "0"
                executive_socket.send(f"publish:{card_name}:{price}".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\n{response}")
                
            elif command == ":history":
                if not current_client:
                    print("\nNo estás conectado con ningún cliente.\n")
                    continue
                    
                executive_socket.send(f"history:{current_client}".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\nHistorial reciente del cliente:\n{response}")
                
            elif command == ":operations":
                if not current_client:
                    print("\nNo estás conectado con ningún cliente.\n")
                    continue
                    
                executive_socket.send(f"operations:{current_client}".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\nTodas las operaciones del cliente:\n{response}")
                
            elif command == ":catalogue":
                executive_socket.send("catalogue".encode())
                response = executive_socket.recv(1024).decode()
                print(f"\nCatálogo de productos:\n{response}")
                
            elif command == ":disconnect":
                if not current_client:
                    print("\nNo estás conectado con ningún cliente.\n")
                    continue
                    
                executive_socket.send(f"disconnect:{current_client}".encode())
                if chat_socket:
                    chat_socket.close()
                current_client = None
                in_chat = False
                print("\nDesconectado del cliente.")
                
            elif command == ":exit":
                if current_client:
                    executive_socket.send(f"disconnect:{current_client}".encode())
                    if chat_socket:
                        chat_socket.close()
                executive_socket.send("exit".encode())
                exit_flag = True
                print("\nSaliendo del sistema...")
                
            else:
                if not command.startswith(":"):
                    print("\nComando no reconocido. Usa ':' para comandos especiales.")
                    
        except Exception as e:
            print(f"\nError al procesar comando: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo...")
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
    finally:
        executive_socket.close()