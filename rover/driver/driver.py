import asyncio

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class Driver:
    def __init__(self,
                 on_light=None,
                 forward_light=None,
                 backward_light=None,
                 front_robot=None,
                 back_robot=None,
                 distance_sensor=None,
                 distance_threshold=None,
                 detection_light=None,
                 temperature_sensor=None,
                 gps_tracker=None,
                 audio_sensor=None,
                 vision_sensor=None,
                 camera_mount_servo=None,
                 arm=None,
                 oled_device=None,
                ):
        self.on_light = on_light
        self.forward_light = forward_light
        self.backward_light = backward_light

        self.front_robot = front_robot
        self.back_robot = back_robot

        self.distance_sensor = distance_sensor
        self.distance_threshold = distance_threshold
        self.detection_light = detection_light
        self.object_found = False
        self.forward_locked = False

        self.temperature_sensor = temperature_sensor

        self.gps_tracker = gps_tracker

        self.audio_sensor = audio_sensor
        self.recordings = []
        self.transcriptions = []

        self.vision_sensor = vision_sensor

        self.camera_mount_servo = camera_mount_servo
        self.camera_mount_position = 0

        self.arm = arm

        self.oled_device = oled_device

        self.stop_event = None
        self.obstruction_detector_task = None
        self.oled_task = None


    async def start(self, stop_event=None):
        self.turn_on_light(self.on_light)
        self.stop_event = stop_event

        if self.distance_sensor:
            self.obstruction_detector_task = asyncio.create_task(self.stop_if_obstructed(stop_event))

        if self.oled_device:
            self.oled_task = asyncio.create_task(self.start_oled_display(stop_event))


    def shutdown(self):
        self.turn_off_light(self.on_light)
        if self.stop_event is not None:
            self.stop_event.set()


    def handle_command(self, command) -> str:
        if command == "move:forward":
            self.forward()
        elif command == "move:backward":
            self.backward()
        elif command == "move:left":
            self.left()
        elif command == "move:right":
            self.right()
        elif command == "move:stop":
            self.stop()
        elif command == "camera:left":
            print("COMMAND: MOVING LEFT")
            self.move_camera_mount("left")
        elif command == "camera:right":
            print("COMMAND: MOVING RIGHT")
            self.move_camera_mount("right")
        else:
            return "invalid command"

        return "ack"


    def handle_arm_command(self, command, value=None):
        """Dispatch commands to the robot arm."""
        try:
            print("ARM COMMAND:", command, value)
            if command == 'rotate':
                self.arm.rotate_base(value)
            elif command == 'shoulder':
                self.arm.move_shoulder(value)
            elif command == 'elbow':
                self.arm.move_elbow(value)
            elif command == 'wrist_pitch':
                self.arm.pitch_wrist(value)
            elif command == 'wrist_roll':
                self.arm.roll_wrist(value)
            elif command == 'gripper':
                self.arm.operate_gripper(value)
            else:
                return "invalid arm command"
            return "ack"
        except Exception as e:
            return str(e)

    def forward(self):
        self.forward_lights()

        self.robot_forward(self.front_robot)
        self.robot_forward(self.back_robot)


    def backward(self):
        self.backward_lights()

        self.robot_backward(self.front_robot)
        self.robot_backward(self.back_robot)


    def right(self):
        self.forward_lights()

        self.robot_right(self.front_robot)
        self.robot_left(self.back_robot)


    def left(self):
        self.forward_lights()

        self.robot_left(self.front_robot)
        self.robot_right(self.back_robot)


    def stop(self):
        self.turn_off_light(self.forward_light)
        self.turn_off_light(self.backward_light)

        self.robot_stop(self.front_robot)
        self.robot_stop(self.back_robot)


    def robot_forward(self, robot):
        if robot is not None and not self.forward_locked:
            robot.forward()


    def robot_backward(self, robot):
        if robot is not None:
            robot.backward()


    def robot_left(self, robot):
        if robot is not None:
            robot.left()


    def robot_right(self, robot):
        if robot is not None:
            robot.right()


    def robot_stop(self, robot):
        if robot is not None:
            robot.stop()


    def forward_lights(self):
        self.turn_on_light(self.forward_light)
        self.turn_off_light(self.backward_light)


    def backward_lights(self):
        self.turn_on_light(self.backward_light)
        self.turn_off_light(self.forward_light)


    def turn_on_light(self, light):
        if light is not None:
            light.on()


    def turn_off_light(self, light):
        if light is not None:
            light.off()


    def move_camera_mount(self, direction):
        print("CALLING MOVE CAMERA MOUNT")
        if self.camera_mount_servo is not None:
            print("MOVING CAMERA MOUNT")
            if direction == "right" and self.camera_mount_position > -1:
                print("MOVING LEFT")
                if self.camera_mount_position == 0:
                    print("MOVING LEFT TO MIN")
                    self.camera_mount_servo.min()
                else:
                    print("MOVING LEFT TO MID")
                    self.camera_mount_servo.mid()
                self.camera_mount_position -= 1
            elif direction == "left" and self.camera_mount_position < 1:
                print("MOVING RIGHT")
                if self.camera_mount_position == -1:
                    print("MOVING RIGHT TO MID")
                    self.camera_mount_servo.mid()
                else:
                    print("MOVING RIGHT TO MAX")
                    self.camera_mount_servo.max()
                self.camera_mount_position += 1


    async def stop_if_obstructed(self, stop_event):
        if self.distance_sensor:
            print("OBSTACLE DETECTION ENABLED")
            while not stop_event.is_set():
                if self.distance_sensor.object_found(self.distance_threshold):
                    if not self.object_found:
                        print("STOPPING DUE TO OBSTRUCTION")
                        self.object_found = True
                        self.object_in_range()
                        self.stop()
                elif self.object_found:
                    self.object_found = False
                    self.object_out_of_range()

                await asyncio.sleep(.1)


    def object_in_range(self):
        print("OBSTACLE IN RANGE")
        self.turn_on_light(self.detection_light)
        self.disable_forward()


    def object_out_of_range(self):
        print("OBSTACLE OUT OF RANGE")
        self.turn_off_light(self.detection_light)
        self.enable_forward()


    def enable_forward(self):
        print("ENABLING FORWARD MOVEMENT")
        self.forward_locked = False


    def disable_forward(self):
        print("DISABLING FORWARD MOVEMENT")
        print("ROBOT STATUS:", self.front_robot, self.back_robot)
        self.forward_locked = True


    async def listen_and_respond(self, stop_event):
        print("STARTING TO LISTEN AND RESPOND")
        if self.audio_sensor is not None:
            await self.audio_sensor.start_listening(stop_event)
            self.respond_to_audio()


    def respond_to_audio(self):
        print("PREPARING TO RESPOND TO AUDIO")
        context = self.get_context()

        if self.audio_sensor is not None:
            response = self.audio_sensor.respond_to_audio(context)
        else:
            print("NO AUDIO SENSOR DETECTED")
            response = "No audio sensor detected"

        return response


    async def start_oled_display(self, stop_event):
        print("STARTING OLED DISPLAY")
        while not stop_event.is_set():
            await asyncio.to_thread(self.write_to_oled_display)
            await asyncio.sleep(2)


    def write_to_oled_display(self):
        with canvas(self.oled_device) as draw:
            draw.rectangle(self.oled_device.bounding_box, outline="white", fill="black")
            draw.text((5, 0), "Cloud Rover", fill="white")

            context = self.get_context()

            height = 15

            if "visual" in context:
                draw.text((10, height), f'Visual: {context["visual"]}', fill="white")
                height += 10

            if "distance" in context:
                draw.text((10, height), f'Distance: {context["distance"]}', fill="white")
                height += 10

            if "temperature" in context:
                draw.text((10, height), f'Temp: {context["temperature"]}', fill="white")
                height += 10

            if "humidity" in context:
                draw.text((10, height), f'Humidity: {context["humidity"]}', fill="white")
                height += 10

            if "location" in context:
                draw.text((10, height), f'Location: {context["location"]}', fill="white")


    def get_context(self):
        context = {}

        if self.vision_sensor is not None:
            context["visual"] = self.vision_sensor.analyze()

        if self.distance_sensor is not None:
            context["distance"] = self.distance_sensor.distance_display()

        if self.temperature_sensor is not None:
            context["temperature"] = self.temperature_sensor.temp_f_display()
            context["humidity"] = self.temperature_sensor.humidity_display()

        if self.gps_tracker is not None:
            location = self.gps_tracker.location()
            if location is not None:
                context["location"] = f"{location.latitude}, {location.longitude}"

        return context
