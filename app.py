import time

import mediapipe as mp
import cv2
import requests
import modi_plus

SERVER_URL = "http://localhost:8000"
LEFT = -1
RIGHT = 1


class Robot:
    def __init__(self):
        bundle = modi_plus.MODIPlus()
        self.imu = bundle.imus[0]
        self.left_motor = bundle.motors[1]
        self.right_motor = bundle.motors[0]

        self.direction = LEFT

    def turn_angle(self, angle):
        self.left_motor.append_angle(angle * 2)
        self.right_motor.append_angle(angle * 2)

    def update(self):
        if self.direction == LEFT:
            self.turn_angle(15)
        elif self.direction == RIGHT:
            self.turn_angle(-15)
        
        if self.imu.yaw < -60:
            self.direction = RIGHT
        elif self.imu.yaw > 60:
            self.direction = LEFT

    def stop(self):
        self.left_motor.set_speed(0)
        self.right_motor.set_speed(0)


class FaceDetector:
    def __init__(self):
        self.result = mp.tasks.vision.FaceDetectorResult
        self.detector = mp.tasks.vision.FaceDetector
        self.create_detector()
    
    def create_detector(self):
        def update_result(result, output_image, timestamp_ms):
            self.result = result

        options = mp.tasks.vision.FaceDetectorOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path="./model/blaze_face_short_range.tflite"),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            min_detection_confidence=0.7,
            result_callback=update_result
        )

        self.detector = self.detector.create_from_options(options)

    def detect_async(self, image):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        self.detector.detect_async(mp_image, int(time.time() * 1000))

    def close(self):
        self.detector.close()


def draw_rectangle_on_faces(image, result):
    try:
        annotated_image = image.copy()
        for detection in result.detections:
            x = detection.bounding_box.origin_x
            y = detection.bounding_box.origin_y
            w = detection.bounding_box.width
            h = detection.bounding_box.height
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 5)
        return annotated_image
    except:
        return image


def main():
    cap = cv2.VideoCapture(0)
    detector = FaceDetector()
    robot = Robot()

    prev_time = time.time()
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        image = cv2.flip(image, 1)
        detector.detect_async(image)

        if time.time() - prev_time >= 3:
            if len(detector.result.detections) != 0:
                _, img_encoded = cv2.imencode(".jpg", image)
                requests.post(
                    f"{SERVER_URL}/upload/",
                    files={"file": img_encoded.tobytes()},
                    data={"location": location})
            robot.update()
            prev_time = time.time()

        image = draw_rectangle_on_faces(image, detector.result)
        cv2.imshow("Daegu Modern Culture", image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    detector.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    location = input("기기가 작동될 위치를 입력하세요: ")
    main()