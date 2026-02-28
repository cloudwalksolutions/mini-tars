import unittest
from unittest.mock import patch

from .gps import GPSTracker, Location

class TestGPSTracker(unittest.TestCase):
    def setUp(self):
        self.port = "/dev/ttyAMA0"
        self.baudrate = 9600
        self.timeout = 1
        self.gps_tracker = GPSTracker(self.port, self.baudrate, self.timeout)


    def test_empty_location(self):
        empty_location = Location()
        self.assertEqual(empty_location.latitude, 0.0)
        self.assertEqual(empty_location.longitude, 0.0)


    @patch('serial.Serial')
    def test_read_gps_data(self, mock_serial):
        mock_serial.return_value.readline.return_value = b'$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\r\n'

        data = self.gps_tracker.read_gps_data()

        mock_serial.return_value.readline.assert_called_once()
        self.assertEqual(data, b'$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\r\n')


    @patch('pynmea2.parse')
    def test_parse_empty_gps_data(self, mock_parse):
        data = b''

        location = self.gps_tracker.parse_gps_data(data)

        mock_parse.assert_not_called()
        self.assertEqual(location.latitude, 0)
        self.assertEqual(location.longitude, 0)


    @patch('pynmea2.parse')
    def test_parse_gps_data(self, mock_parse):
        mock_location = Location(48.1173, 11.5175)
        mock_parse.return_value = mock_location
        data = b'$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\r\n'

        location = self.gps_tracker.parse_gps_data(data)

        mock_parse.assert_called_once()
        self.assertEqual(location.latitude, 48.1173)
        self.assertEqual(location.longitude, 11.5175)


    def test_location(self):
        with patch.object(self.gps_tracker, 'read_gps_data', return_value=b'$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\r\n'), \
             patch.object(self.gps_tracker, 'parse_gps_data') as mock_parse:
            mock_parse.return_value = Location(48.1173, 11.5175)

            location = self.gps_tracker.location()

            self.assertEqual(location.latitude, 48.1173)
            self.assertEqual(location.longitude, 11.5175)

