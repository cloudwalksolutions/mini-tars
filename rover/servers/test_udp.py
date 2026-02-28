import unittest
from unittest.mock import MagicMock
import asyncio
import json

from rover.driver.driver import Driver
from rover.sensors.distance import UltrasonicDistanceSensor
from rover.sensors.temperature import TemperatureSensor
from rover.sensors.gps import Location, GPSTracker
from rover.sensors.audio import AudioSensor
from rover.sensors.vision import VisionSensor
from rover.arm.arm import RobotArm
from .udp import RoverServerUDP


class TestRoverServerUDP(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()
        self.addr = ('127.0.0.1', 12345)

        self.visual = "something"
        self.distance = .12
        self.temp = 43.4
        self.humidity = 32.5
        self.location = Location(12.3, 45.6)
        self.sensor_data = {
            "visual": self.visual,
            "distance": self.distance,
            "distance_units": "m",
            "temperature": self.temp,
            "temperature_units": "°F",
            "humidity": self.humidity,
            "humidity_units": "%",
            "latitude": self.location.latitude,
            "latitude_units": "°",
            "longitude": self.location.longitude,
            "longitude_units": "°",
        }
        self.sensor_json = json.dumps(self.sensor_data).encode("utf-8")

        self.driver = MagicMock(spec=Driver)

        self.driver.distance_sensor = MagicMock(spec=UltrasonicDistanceSensor)
        self.driver.distance_sensor.check_distance.return_value = self.distance

        self.driver.temperature_sensor = MagicMock(spec=TemperatureSensor)
        self.driver.temperature_sensor.temp_f.return_value = self.temp
        self.driver.temperature_sensor.humidity.return_value = self.humidity

        self.driver.gps_tracker = MagicMock(spec=GPSTracker)
        self.driver.gps_tracker.location.return_value = self.location

        self.driver.audio_sensor = MagicMock(spec=AudioSensor)
        self.driver.audio_sensor.listen.return_value = 'audio_data'
        self.driver.audio_sensor.transcribe.return_value = 'hello world'

        self.driver.arm = MagicMock(spec=RobotArm)

        self.driver.vision_sensor = MagicMock(spec=VisionSensor)
        self.driver.vision_sensor.analyze.return_value = self.visual

        self.transport = MagicMock()
        self.protocol = RoverServerUDP(loop=self.loop, stop_event=self.stop_event, driver=self.driver)
        self.protocol.connection_made(transport=self.transport)
        self.assertEqual(self.protocol.transport, self.transport)


    def test_connection_lost(self):
        self.protocol.connection_lost("error")


    def test_empty_datagrams(self):
        self.protocol.datagram_received(None, self.addr)
        self.driver.handle_command.assert_not_called()

        self.protocol.datagram_received("", self.addr)
        self.driver.handle_command.assert_not_called()

        self.protocol.datagram_received(" ".encode('utf-8'), self.addr)
        self.driver.handle_command.assert_not_called()


    def test_datagram_received(self):
        message = "move:forward"
        encoded_message = message.encode('utf-8')
        response = "ack"
        self.driver.handle_command.return_value = response

        self.protocol.datagram_received(encoded_message, self.addr)

        self.driver.handle_command.assert_called_with(message)


    async def test_start_sensor_stream(self):
        self.protocol.datagram_received(b"sensor:start", self.addr)
        self.assertEqual(self.protocol.sensor_clients[self.addr].is_set(), False)
        await asyncio.sleep(.5)

        self.assert_sensor_data_sent()

        self.protocol.datagram_received(b"sensor:stop", self.addr)
        await asyncio.sleep(.5)
        self.assertEqual(self.protocol.sensor_clients[self.addr].is_set(), True)


    async def test_start_sensor_stream_duplicate(self):
        self.protocol.datagram_received(b"sensor:start", self.addr)
        self.protocol.datagram_received(b"sensor:start", self.addr)
        self.assertEqual(len(self.protocol.sensor_clients), 1)
        self.assertEqual(self.protocol.sensor_clients[self.addr].is_set(), False)

        self.protocol.datagram_received(b"sensor:stop", self.addr)
        self.protocol.datagram_received(b"sensor:stop", self.addr)
        self.assertEqual(self.protocol.sensor_clients[self.addr].is_set(), True)
        self.assertEqual(len(self.protocol.sensor_clients), 1)


    async def test_stream_sensor_data(self):
        stop_event = asyncio.Event()

        send_task = asyncio.create_task(self.protocol.stream_sensor_data(self.addr, stop_event))

        await asyncio.sleep(.5)
        stop_event.set()
        await send_task
        self.assert_sensor_data_sent()


    def test_send_sensor_data(self):
        self.protocol.send_sensor_data(self.addr)
        self.assert_sensor_data_sent()


    def test_send_sensor_data_without_sensors(self):
        self.driver.vision_sensor = None
        self.driver.distance_sensor = None
        self.driver.temperature_sensor = None
        self.driver.gps_tracker = None

        self.protocol.send_sensor_data(self.addr)

        self.transport.sendto.assert_not_called()


    async def test_listen(self):
        self.protocol.datagram_received(b"listen:start", self.addr)
        await asyncio.sleep(.5)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), False)
        self.driver.listen_and_respond.assert_called_once()

        self.protocol.datagram_received(b"listen:stop", self.addr)
        await asyncio.sleep(.5)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), True)


    async def test_listen_duplicate(self):
        self.protocol.datagram_received(b"listen:start", self.addr)
        self.protocol.datagram_received(b"listen:start", self.addr)
        self.assertEqual(len(self.protocol.listen_clients), 1)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), False)

        self.protocol.datagram_received(b"listen:stop", self.addr)
        self.protocol.datagram_received(b"listen:stop", self.addr)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), True)

        self.protocol.datagram_received(b"listen:start", self.addr)
        self.assertEqual(len(self.protocol.listen_clients), 1)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), False)

        self.protocol.datagram_received(b"listen:stop", self.addr)
        self.assertEqual(self.protocol.listen_clients[self.addr].is_set(), True)


    def test_invalid_robot_arm_command(self):
        self.protocol.datagram_received(b"arm:rotate:", self.addr)
        self.driver.handle_arm_command.assert_not_called()


    def test_robot_arm_command(self):
        self.protocol.datagram_received(b"arm:rotate:right", self.addr)
        self.driver.handle_arm_command.assert_called_with("rotate", "right")


    def assert_sensor_data_sent(self):
        self.transport.sendto.assert_called_with(self.sensor_json, self.addr)
