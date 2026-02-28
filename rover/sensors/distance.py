import asyncio


class UltrasonicDistanceSensor:
    def __init__(self, ultrasonic_sensor, sensor_led):
        self.sensor_led = sensor_led
        self.ultrasonic_sensor = ultrasonic_sensor


    def distance_display(self) -> str:
        return f'{self.check_distance():.2f}m'


    def check_distance(self) -> float:
        return self.ultrasonic_sensor.distance


    def object_found(self, threshold) -> bool:
        if type(threshold) not in [int, float]:
            print('INVALID THRESHOLD')
            return False

        found = self.check_distance() <= threshold
        if found:
            self.sensor_led.on()
        else:
            self.sensor_led.off()

        return found


    async def scan(self, stop_event, threshold=.5):
        while not stop_event.is_set():
            self.object_found(threshold)
            print("SLEEPING AFTER DISTANCE SCAN")
            await asyncio.sleep(.2)
            print("DONE SLEEPING AFTER DISTANCE SCAN")

        self.sensor_led.off()
