import asyncio


DEFAULT_PORT = 8000

class RoverServer:
    def __init__(self, driver, udp_protocol, tcp_server, port=DEFAULT_PORT):
        self.driver = driver
        self.udp_protocol = udp_protocol
        self.tcp_server = tcp_server
        self.port = port

    async def listen_and_serve(self, loop, stop_event):
        print('🚀 Starting rover server...')
        self.stop_event = stop_event
        await self.driver.start(stop_event)
        # await self.tcp_server.start()

        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: self.udp_protocol,
            local_addr=('0.0.0.0', self.port))

        try:
            await asyncio.sleep(3600 * 9)
        finally:
            await self.shutdown()

    async def shutdown(self):
        print("Shutting down rover server...")
        self.driver.shutdown()
        self.stop_event.set()
        self.transport.close()

