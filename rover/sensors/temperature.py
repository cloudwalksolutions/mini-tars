

class TemperatureSensor:
    def __init__(self, dht_device):
        self.dht_device = dht_device


    def temp_c(self) -> float:
        """
        Return temperature in degrees Celsius
        """
        try:
            return self.dht_device.temperature
        except Exception as e:
            print("Error reading temperature:", e)
            return 0


    def temp_c_display(self) -> str:
        """
        Return rounded temperature in degrees Celsius as a string
        """
        temp = self.temp_c()
        return f'{temp:.2f}°C'


    def temp_f(self) -> float:
        """
        Return temperature in degrees Fahrenheit
        """
        return self.temp_c() * (9 / 5) + 32


    def temp_f_display(self) -> str:
        """
        Return rounded temperature in degrees Fahrenheit as a string
        """
        temp = self.temp_f()
        return f'{temp:.2f}°F'


    def humidity(self) -> float:
        """
        Return humidity as a percentage
        """
        return self.dht_device.humidity


    def humidity_display(self) -> str:
        """
        Return humidity as a percentage in string format
        """
        return f'{self.humidity():.2f}%'
