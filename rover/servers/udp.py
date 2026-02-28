import asyncio
import json


class RoverServerUDP:
    def __init__(self, loop, stop_event, driver):
        self.loop = loop
        self.stop_event = stop_event
        self.driver = driver
        self.sensor_clients = {}
        self.listen_clients = {}
        self.recordings = []


    def connection_made(self, transport):
        self.transport = transport


    def connection_lost(self, e):
        for event in self.sensor_clients.values():
            event.set()


    def datagram_received(self, data, addr):
        if not isinstance(data, bytes) or data is None:
            return


        message = data.decode('utf-8').strip().lower()
        print('DATA RECEIVED FROM', addr, message)

        if message:
            if message == "sensor:start":
                if addr not in self.sensor_clients:
                    print("STARTING TO SEND SENSOR DATA TO", addr)
                    stop_event = asyncio.Event()
                    self.sensor_clients[addr] = stop_event
                    self.loop.create_task(self.stream_sensor_data(addr, stop_event))

            elif message == "sensor:stop":
                if addr in self.sensor_clients:
                    print("DONE SENDING SENSOR DATA TO", addr)
                    self.sensor_clients[addr].set()

            elif message == "listen:start":
                if addr not in self.listen_clients or self.listen_clients[addr].is_set():
                    print("STARTING TO LISTEN", addr)
                    stop_event = asyncio.Event()
                    self.listen_clients[addr] = stop_event
                    self.loop.create_task(self.driver.listen_and_respond(stop_event))

            elif message == "listen:stop":
                if addr in self.listen_clients:
                    print("DONE LISTENING", addr)
                    self.listen_clients[addr].set()

            elif message.startswith("arm:"):
                print("ARM COMMAND", message)
                message = message[4:]
                if self.driver.arm is not None:
                    message_parts = message.split(":")
                    print("ARM COMMAND PARTS", message_parts)
                    if len(message_parts) > 1 and message_parts[1]:
                        self.driver.handle_arm_command(message_parts[0], message_parts[1])

            else:
                self.driver.handle_command(message)


    async def stream_sensor_data(self, addr, stop_event):
        print("STARTING TO SEND SENSOR DATA TO", addr)
        while not stop_event.is_set():
            await asyncio.to_thread(self.send_sensor_data, addr)
            await asyncio.sleep(2)


    def send_sensor_data(self, addr):
        data = {}

        if self.driver.vision_sensor is not None:
            data["visual"] = self.driver.vision_sensor.analyze()

        if self.driver.distance_sensor is not None:
            data["distance"] = self.driver.distance_sensor.check_distance()
            data["distance_units"] = "m"

        if self.driver.temperature_sensor is not None:
            data["temperature"] = self.driver.temperature_sensor.temp_f()
            data["temperature_units"] = "°F"
            data["humidity"] = self.driver.temperature_sensor.humidity()
            data["humidity_units"] = "%"

        if self.driver.gps_tracker is not None:
            location = self.driver.gps_tracker.location()
            if location is not None:
                data["latitude"] = location.latitude
                data["latitude_units"] = "°"
                data["longitude"] = location.longitude
                data["longitude_units"] = "°"

        if len(data.items()) > 0:
            message = json.dumps(data).encode("utf-8")
            print("SENDING SENSOR DATA TO ", addr, message)
            self.transport.sendto(message, addr)



