import cv2
import numpy as np
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import signal
import threading
from queue import Queue
import asyncio
import websockets
import os

result_queue = Queue()

def apply_filter(image_path, filter_choice):
    if not os.path.exists(image_path):
        return "Erro ao carregar a imagem: caminho inválido"

    image = cv2.imread(image_path)
    
    if image is None:
        return "Erro ao carregar a imagem"

    scale_percent = 50
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        cv2.rectangle(resized_image, (x, y), (x+w, y+h), (255, 0, 0), 2)

    if filter_choice == '1':
        filtered_image = cv2.blur(resized_image, (5, 5))
    elif filter_choice == '2':
        filtered_image = cv2.GaussianBlur(resized_image, (15, 15), 0)
    elif filter_choice == '3':
        filtered_image = cv2.Canny(resized_image, 50, 150)
    elif filter_choice == '4':
        filtered_image = cv2.medianBlur(resized_image, 5)
    elif filter_choice == '5':
        filtered_image = cv2.bilateralFilter(resized_image, 9, 75, 75)
    elif filter_choice == '6':
        filtered_image = cv2.Laplacian(resized_image, cv2.CV_64F)
    else:
        filtered_image = resized_image

    output_path = 'filtered_image.jpg'
    cv2.imwrite(output_path, filtered_image)

    result_queue.put(output_path)

    return output_path

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def signal_handler(signal, frame):
    print("Encerrando o servidor...")
    server.shutdown()
    server.server_close()

signal.signal(signal.SIGINT, signal_handler)

def start_xmlrpc_server():
    with SimpleXMLRPCServer(('localhost', 9000), requestHandler=RequestHandler, logRequests=True) as server:
        server.register_function(apply_filter, 'apply_filter')
        print("Servidor RPC em execução na porta 9000...")
        server.serve_forever()

async def websocket_handler(websocket, path):
    try:
        await websocket.send("Conexão estabelecida".encode())

        image_path = await websocket.recv()
        filter_choice = await websocket.recv()

        result = apply_filter(image_path, filter_choice)

        if result.startswith("Erro"):
            await websocket.send(result.encode())
            return

        with open(result, 'rb') as f:
            image_bytes = f.read()

        await websocket.send(image_bytes)
    except Exception as e:
        await websocket.send(f"Erro: {str(e)}".encode())

async def start_websocket_server():
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()  # Mantém o servidor rodando

if __name__ == "__main__":
    xmlrpc_thread = threading.Thread(target=start_xmlrpc_server)
    xmlrpc_thread.start()

    asyncio.run(start_websocket_server())
