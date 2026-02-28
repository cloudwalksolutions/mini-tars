import serial
import pynmea2


class Location:
    def __init__(self, latitude=0.0, longitude=0.0):
        self.latitude = latitude
        self.longitude = longitude


class GPSTracker:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port = None

    def read_gps_data(self):
        try:
            print("STARTING TO READ GPS DATA")
            self.serial_port = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
            data = self.serial_port.readline()
            print("DONE READING GPS DATA")
            return data
        except Exception as e:
            print("Error reading GPS data from serial port", e)

    def parse_gps_data(self, data):
        location = Location()
        if "$GPRMC" in str(data):
            decoded_data = data.decode('utf-8')
            msg = pynmea2.parse(decoded_data)
            location.latitude = msg.latitude
            location.longitude = msg.longitude

        return location

    def location(self) -> Location:
        data = self.read_gps_data()
        return self.parse_gps_data(data)

