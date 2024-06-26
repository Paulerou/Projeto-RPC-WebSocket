import asyncio
import websockets
import xmlrpc.client
import os

async def websocket_client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        image_path = os.path.abspath(r"C:\Users\Paulo\Desktop\python\b.jpg")
        await websocket.send(image_path)
        
        filter_choice = input("Escolha o filtro (1-6): ")
        await websocket.send(filter_choice)

        response = await websocket.recv()
        
        if isinstance(response, str) and response.startswith("Erro"):
            print(response)
        else:
            with open("received_image.jpg", "wb") as f:
                f.write(response)
            print("Imagem filtrada recebida e salva como 'received_image.jpg'")

async def call_rpc_server(image_path, filter_choice):
    with xmlrpc.client.ServerProxy("http://localhost:9000/RPC2") as proxy:
        result = proxy.apply_filter(image_path, filter_choice)
        print("Resultado do servidor XML-RPC:", result)

async def main():
    await websocket_client()

    image_path = os.path.abspath(r"C:\Users\Paulo\Desktop\python\b.jpg")
    filter_choice = input("Escolha o filtro (1-6): ")
    await call_rpc_server(image_path, filter_choice)

if __name__ == "__main__":
    asyncio.run(main())
