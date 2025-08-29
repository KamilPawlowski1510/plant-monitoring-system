import io
import math
from datetime import datetime

from grove.adc import ADC
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from grove.grove_moisture_sensor import GroveMoistureSensor
from grove.grove_relay import GroveRelay
from picamera import PiCamera
from sense_hat import SenseHat


class HardwareManager:
    """Manages all interactions with grove modules and logging sensor data."""
    _DEFAULT_ADC = ADC(0x08) # Needed for Light and Moisture sensors
    _MOTION_THRESHOLD = 0.05 # g's acceptable above and below 1 (gravity)
    _CAMERA_RESOLUTION = (1280, 720)

    def __init__(self) -> None:
        """Initialise grove modules."""
        self.light_sensor = GroveLightSensor(2)
        self.moisture_sensor = GroveMoistureSensor(3)
        self.relay = GroveRelay(5)
        self.sense_hat = SenseHat()
        self.camera = PiCamera(resolution=self._CAMERA_RESOLUTION)

        # Correct ADCs
        self.light_sensor.adc = self._DEFAULT_ADC
        self.moisture_sensor.adc = self._DEFAULT_ADC

    def log_sensor_data(self, data) -> None:
        """Log sensor data to file with timestamp."""
        date_time = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        formatted_data = f"[{date_time}] {data}\n"

        with open("logged_data.txt", "a") as f:
            f.write(formatted_data)

        print(formatted_data[:-1])

    def detect_motion(self) -> bool:
        """Check for motion using sense HAT's accelerometer."""
        data = self.sense_hat.get_accelerometer_raw()
        force = math.sqrt(data["x"]**2 + data["y"]**2 + data["z"]**2)

        if abs(force - 1) > self._MOTION_THRESHOLD:
            self.log_sensor_data(f"Motion Detected: {force} g")
            return True
        return False

    def get_light_data(self) -> float:
        """Return light data from light sensor and log data."""
        light = self.light_sensor.light / 10.0
        self.log_sensor_data(f"Light: {light}%")
        return light

    def get_moisture_data(self) -> int:
        """Return soils moisture from moisture sensor and log data."""
        moisture = self.moisture_sensor.moisture
        self.log_sensor_data(f"Soil Moisture: {moisture} mV")
        return moisture

    def capture_image(self) -> None:
        """Capture image using Pi camera and log image capture."""
        image = io.BytesIO()
        self.camera.capture(image, 'jpeg')
        image.seek(0)

        with open('image.jpg', 'wb') as image_file:
            image_file.write(image.read())
        
        self.log_sensor_data("Image captured")
    
    def turn_on_relay(self) -> None:
        """Turn on relay."""
        self.relay.on()
        print("Relay turned on")
    
    def turn_off_relay(self) -> None:
        """Turn off relay."""
        self.relay.off()
        print("Relay turned off")