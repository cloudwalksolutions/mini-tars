import unittest
from unittest.mock import MagicMock, patch

import asyncio
from gpiozero import LED
import numpy as np

from .vision import VisionSensor


class TestVisionSensor(unittest.TestCase):

    def setUp(self):
        self.light = MagicMock(spec=LED)
        self.camera = MagicMock()
        self.vision_sensor = VisionSensor(
            light=self.light,
            camera=self.camera,
        )
        self.assertEqual(self.vision_sensor.light, self.light)
        self.assertEqual(self.vision_sensor.camera, self.camera)


    def test_take_picture(self):
        image_path = "/tmp/image.jpg"

        res = self.vision_sensor.take_picture()

        self.assertEqual(res, image_path)
        self.camera.start_and_capture_file.assert_called_once_with(image_path)
        self.light.on.assert_called_once()
        self.light.off.assert_called_once()


    def test_classify_image_with_io_error(self):
        with self.assertRaises(IOError) as context:
            self.vision_sensor.classify_image('faulty_path.jpg')

        self.assertIn('No such file', str(context.exception))


    def test_classify_image(self):
        results = self.vision_sensor.classify_image('images/cicada.png')
        self.assertEqual(results[0][0], 'cicada')
        self.assertEqual(len(results), 3)

        results = self.vision_sensor.classify_image('images/shoe.png')
        self.assertEqual(results[0][0], 'running_shoe')
        self.assertEqual(len(results), 3)

    @patch('rover.sensors.vision.VisionSensor.classify_image')
    def test_analyze(self, mock_classify_image):
        mock_classify_image.return_value = [('running_shoe', 0.9), ('slipper', 0.1)]

        res = self.vision_sensor.analyze()

        self.camera.start_and_capture_file.assert_called_once()
        mock_classify_image.assert_called_once()
        self.assertEqual(res, 'running_shoe')