import os

import cv2
import requests

base_path = os.path.dirname(os.path.realpath(__file__))


class NeuralNetwork:
    def __init__(self):
        # Init deep learning machine
        self.CLASSES = {
            0: "background",
            1: "aeroplane",
            2: "bicycle",
            3: "bird",
            4: "boat",
            5: "bottle",
            6: "bus",
            7: "car",
            8: "cat",
            9: "chair",
            10: "cow",
            11: "diningtable",
            12: "dog",
            13: "horse",
            14: "motorbike",
            15: "person",
            16: "pottedplant",
            17: "sheep",
            18: "sofa",
            19: "train",
            20: "tvmonitor",
        }

        self.network = cv2.dnn.readNetFromCaffe(
            base_path + "/MobileNetSSD_deploy.prototxt.txt",
            base_path + "/MobileNetSSD_deploy.caffemodel",
        )

    def detect(self, image_url):
        # Detect cats in image
        try:
            img_data = requests.get(image_url).content
        except requests.Timeout:
            return []
        except requests.ConnectionError:
            return []

        with open("tmp.jpg", "wb") as tmp_image:
            tmp_image.write(img_data)

        image = cv2.imread("tmp.jpg")
        cv2.resize(image, (300, 300))

        # Convert for network
        blob = cv2.dnn.blobFromImage(image, 0.007843, (300, 300), 127.5)
        self.network.setInput(blob)

        detections = self.network.forward()

        sub_detection = []

        for i in range(0, 3):
            classe = self.CLASSES[int(detections[0, 0, i, 1])]
            confidence = detections[0, 0, i, 2] * 100

            sub_detection.append({"classe": classe, "confidence": confidence})

        return sub_detection
