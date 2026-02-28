import os
import asyncio

DEFAULT_TCP_PORT = 8001

class RoverServerTCP:
    def __init__(self, host='localhost', port=DEFAULT_TCP_PORT):
        self.host = host
        self.port = port

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        await self.server.serve_forever()

    async def handle_client(self, reader, writer):
        try:
            file_name = await reader.read(1024)  # Read the file name
            file_name = file_name.decode().strip()
            file_path = os.path.join('/tmp', file_name)

            with open(file_path, 'wb') as f:
                while True:
                    data = await reader.read(1024)
                    if not data:
                        break
                    f.write(data)

            writer.write(b"File received")
        finally:
            writer.close()
