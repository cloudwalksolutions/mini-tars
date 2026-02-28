import openai
import numpy as np
from tensorflow.keras.applications import MobileNetV2, mobilenet_v2
from PIL import Image


class VisionSensor:
    def __init__(self, light, camera):
        self.light = light
        self.camera = camera

        self.model = MobileNetV2(weights='imagenet', include_top=True)


    def take_picture(self) -> str:
        """
        Captures an image from the camera and returns the path to the image.
        :return:
        """
        self.light.on()

        image_path = "/tmp/image.jpg"
        self.camera.start_and_capture_file(image_path)

        self.light.off()
        return image_path


    def classify_image(self, image_path) -> list:
        """
        Classifies an image using the MobileNetV2 model.
        :param image_path:
        :return:
        """
        img = Image.open(image_path).convert('RGB').resize((224, 224))
        img_array = np.expand_dims(np.array(img) / 255.0, axis=0)

        predictions = self.model.predict(img_array)

        decoded_predictions = mobilenet_v2.decode_predictions(predictions, top=3)[0]
        return [(prediction[1], prediction[2]) for prediction in decoded_predictions]


    def analyze(self) -> str:
        """
        Analyzes what is in sight using the MobileNetV2 model.
        :return:
        """
        image_path = self.take_picture()
        predictions = self.classify_image(image_path)
        if len(predictions) > 0:
            return predictions[0][0]

    # Load your API key
    openai.api_key = 'your-api-key'


    # Function to analyze image with CLIP
    def analyze_image_with_clip(self, image_path, descriptions):
        return openai.Image.create_search(
            model="clip-vit-base-patch32",
            file=open(image_path, "rb"),
            query=descriptions,
            return_similarities=True
        )
