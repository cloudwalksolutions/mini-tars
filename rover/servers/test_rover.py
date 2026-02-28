import unittest
from unittest.mock import MagicMock, AsyncMock, Mock, patch
import asyncio

from rover.driver.driver import Driver
from .rover import RoverServer, DEFAULT_PORT
from .udp import RoverServerUDP
from .tcp import RoverServerTCP


class TestRoverServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.driver = MagicMock(spec=Driver)
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()
        self.udp_protocol = RoverServerUDP(loop=self.loop, stop_event=self.stop_event, driver=self.driver)
        self.transport = MagicMock()
        self.udp_protocol.connection_made(self.transport)
        self.tcp_server = MagicMock(spec=RoverServerTCP)
        self.server = RoverServer(driver=self.driver, udp_protocol=self.udp_protocol, tcp_server=self.tcp_server)

        self.assertEqual(DEFAULT_PORT, self.server.port)
        self.assertEqual(self.udp_protocol, self.server.udp_protocol)
        self.assertEqual(self.server.tcp_server, self.tcp_server)


    def test_custom_port(self):
        self.port = 8001
        self.server = RoverServer(
            driver=self.driver,
            udp_protocol=self.udp_protocol,
            tcp_server=self.tcp_server,
            port=self.port,
        )
        self.assertEqual(self.port, self.server.port)


    @patch('asyncio.get_running_loop')
    async def test_listen_and_serve_exception(self, mock_loop):
        stop_event = asyncio.Event()
        with self.assertRaises(Exception):
            mock_loop.create_datagram_endpoint.side_effect = Exception("Failed")
            await self.server.listen_and_serve(mock_loop, stop_event)


    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('asyncio.get_running_loop')
    async def test_listen_and_serve(self, mock_loop, mock_sleep):
        mock_transport = MagicMock()
        mock_protocol = MagicMock()
        mock_loop.create_datagram_endpoint = AsyncMock(return_value=(mock_transport, mock_protocol))
        mock_sleep.return_value = None

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        serve_task = asyncio.create_task(self.server.listen_and_serve(mock_loop, stop_event))

        loop.call_later(0.1, self.server.shutdown)
        await serve_task

        self.assertIsNotNone(self.server.stop_event)
        self.driver.start.assert_called_once()
        self.driver.shutdown.assert_called_once()
        # self.tcp_server.start.assert_called_once()
        mock_loop.create_datagram_endpoint.assert_called_once()
        mock_transport.close.assert_called_once()
        self.assertTrue(stop_event.is_set())

