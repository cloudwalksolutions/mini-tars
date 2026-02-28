import unittest
from unittest.mock import MagicMock, PropertyMock
import asyncio

from gpiozero import DistanceSensor, LED

from .distance import UltrasonicDistanceSensor


class TestDistanceSensor(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.threshold = .1111
        self.sensor_led = MagicMock(spec=LED)
        self.uds = MagicMock(spec=DistanceSensor)
        type(self.uds).distance = PropertyMock(return_value=self.threshold)
        self.distance_sensor = UltrasonicDistanceSensor(self.uds, self.sensor_led)


    def test_distance_display(self):
        self.assertEqual(self.distance_sensor.distance_display(), "0.11m")


    def test_distance(self):
        distance = self.distance_sensor.check_distance()
        self.assertEqual(distance, self.threshold)


    def test_obstacle_found_invalid(self):
        self.assertFalse(self.distance_sensor.object_found(threshold=None))
        self.assertFalse(self.distance_sensor.object_found(threshold='invalid'))


    def test_obstacle_found(self):
        self.assertTrue(self.distance_sensor.object_found(self.threshold))
        self.sensor_led.on.assert_called_once()
        self.assertTrue(self.distance_sensor.object_found(self.threshold + .1))


    def test_obstacle_not_found(self):
        type(self.uds).distance = PropertyMock(return_value=.6)
        self.assertFalse(self.distance_sensor.object_found(.5))
        self.sensor_led.off.assert_called_once()


    async def test_loop(self):
        stop_event = asyncio.Event()

        task = asyncio.create_task(self.distance_sensor.scan(stop_event, self.threshold))

        await asyncio.sleep(0.5)
        stop_event.set()
        await task

        self.sensor_led.on.assert_called()
        self.sensor_led.off.assert_called()

