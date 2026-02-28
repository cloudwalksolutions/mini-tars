import unittest
from unittest.mock import MagicMock, PropertyMock

from .temperature import TemperatureSensor


class TestTemperatureSensor(unittest.TestCase):

    def setUp(self):
        self.dht_device = MagicMock()
        self.temperature_sensor = TemperatureSensor(dht_device=self.dht_device)


    def test_temperature(self):
        type(self.dht_device).temperature = PropertyMock(return_value=20.567)

        self.assertEqual(self.temperature_sensor.temp_c(), 20.567)
        self.assertEqual(self.temperature_sensor.temp_c_display(), "20.57°C")

        self.assertEqual(self.temperature_sensor.temp_f(), 69.0206)
        self.assertEqual(self.temperature_sensor.temp_f_display(), "69.02°F")


    def test_humidity(self):
        type(self.dht_device).humidity = PropertyMock(return_value=10.532)
        self.assertEqual(self.temperature_sensor.humidity(), 10.532)
        self.assertEqual(self.temperature_sensor.humidity_display(), "10.53%")
