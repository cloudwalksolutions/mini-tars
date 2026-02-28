import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from .tcp import RoverServerTCP

class TestRoverServerTCP(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.host = 'localhost'
        self.tcp_port = 5000
        self.tcp_server = RoverServerTCP(self.host, self.tcp_port)

    async def test_server_starts_and_listens(self):
        with patch('asyncio.start_server') as mock_start_server:
            mock_start_server.return_value = AsyncMock()
            await self.tcp_server.start()
            mock_start_server.assert_called_once_with(self.tcp_server.handle_client, self.host, self.tcp_port)

    async def test_handle_client(self):
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_reader.read = AsyncMock(side_effect=[b'testfile.txt', b'hello', b''])
        mock_writer.write = MagicMock()

        await self.tcp_server.handle_client(mock_reader, mock_writer)

        mock_writer.write.assert_called()
        mock_writer.close.assert_called()
        with open('/tmp/testfile.txt', 'r') as f:
            content = f.read()
        self.assertEqual(content, 'hello')
