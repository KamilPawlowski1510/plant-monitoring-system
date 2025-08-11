from datetime import datetime
import io
import math
import time
from time import sleep

import BlynkLib
from picamera import PiCamera
from sense_hat import SenseHat

from grove.adc import ADC
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from grove.grove_moisture_sensor import GroveMoistureSensor
from grove.grove_relay import GroveRelay
from azure.storage.blob import ContainerClient, ContentSettings

# Blynk authentication token
BLYNK_AUTH = "7os_iwPxKnhgay7WX-KhXgzXi9mgb2Ib"

# Initialise the Blynk instance
blynk = BlynkLib.Blynk(BLYNK_AUTH)

# Needed for Light sensor and Moisture sensor
adc = ADC(0x08)

# Initialise Light sensor
light_sensor = GroveLightSensor(2)
light_sensor.adc = adc

#initialise Moisture sensor
moisture_sensor = GroveMoistureSensor(3)
moisture_sensor.adc = adc

# Initialise Relay
relay = GroveRelay(5)

# Initialise Sense hat
sense_hat = SenseHat()

# Initialise Camera
camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 180
#time.sleep(2)

# Azure blob storage container
container_client = ContainerClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=smskman1510;AccountKey=6uIe1RPi+CLyvKpJHIGExkPAse9pRepXThBE+tIkobiPawHuPIQS5NvoiT/ycuJP8Uw9HGn3o8+3+AStJoSimQ==;EndpointSuffix=core.windows.net", "plant-monitoring-images")

MOTION_CHECK_DELAY = 0.1 # How often to check for motion
MOTION_THRESHOLD = 0.05 # g's acceptable above and below 1 (gravity)
MOTION_CHECK_COOLDOWN = 2 # How long to not check for motion after motion was detected
motion_cooldown_time = 0

SENSOR_CHECK_COOLDOWN = 60 # How long to wait between dealing with none motion sensors
sensor_check_next_time = 0

LIGHT_CHECK_COOLDOWN = 300 # Every minute by default
light_check_next_time = 0
light_min_value = 300 # Minimum amount of light before turning on relay

daily_task_hour = 12
daily_task_next_time = 0

soil_max_value = 1200 # Maximum mV before the plant needs to be watered again
watering_needed = False

misting_counter = 0
mist_every_x_days = 2

def log_data(data):
    date_time = datetime.fromtimestamp(current_time).strftime('%d/%m/%Y, %H:%M:%S')
    formatted_data = f"[{date_time}] {data}\n"
    with open("logged_data.txt", "a") as f:
        f.write(formatted_data)
    print(formatted_data)

def detect_motion() -> bool:
    data = sense_hat.get_accelerometer_raw()
    force = math.sqrt(data["x"]**2 + data["y"]**2 + data["z"]**2)
    if abs(force - 1) > MOTION_THRESHOLD:
        global motion_cooldown_time
        motion_cooldown_time = time.time() + MOTION_CHECK_COOLDOWN
        log_data(f"Motion Detected: {force} g")
        return True
    else:
        return False

def process_light_data():
    light = light_sensor.light / 10.0
    log_data(f"Light: {light}%")
    blynk.virtual_write(0, light)
    if light < light_min_value:
        relay.on()
        blynk.virtual_write(2, "Currently On")
    else:
        relay.off()
        blynk.virtual_write(2, "Currently Off")

def process_soil_data():
    moisture_mv = moisture_sensor.moisture
    log_data(f"Soil Moisture: {moisture_mv} mV")
    blynk.virtual_write(1, moisture_mv)
    if moisture_mv > soil_max_value:
        watering_needed = True
    else:
        watering_needed = False

def get_next_daily_task_time():
    global daily_task_next_time
    current_date = datetime.fromtimestamp(current_time)
    daily_task_date = current_date.replace(hour=daily_task_hour, minute=0, second=0, microsecond=0)

    daily_task_next_time = daily_task_date.timestamp()
    if daily_task_next_time <= current_time:
        daily_task_next_time += 86400
    
    print("Next date for daily task: ", datetime.fromtimestamp(daily_task_next_time).strftime("%Y-%m-%d %H:%M:%S"))

# Register handler for virtual pin V4 write event
@blynk.on("V4")
def handle_v4_write(value):
    global daily_task_hour
    daily_task_hour = value[0]
    print(f'Daily task hour updated to: {daily_task_hour}')
    get_next_daily_task_time()

def send_daily_notification():
    global misting_counter
    message = "Todays tasks: Rotate the plant"
    if misting_counter >= mist_every_x_days -1:
        message += ", mist the plant"
        misting_counter = 0
    else:
        misting_counter += 1
    if watering_needed:
        message += ", water the plant"
    blynk.log_event("daily_notification", message)

def capture_image():
    image = io.BytesIO()
    camera.capture(image, 'jpeg')
    image.seek(0)

    with open('image.jpg', 'wb') as image_file:
        image_file.write(image.read())
    
    log_data("Image captured")

def upload_image():
    with open(file="image.jpg", mode="rb") as data:
        container_client.upload_blob(name="image.jpg", data=data, overwrite=True, content_settings=ContentSettings(content_type="image/jpeg"))

# Main loop to keep the Blynk connection alive and process events
if __name__ == "__main__":
    try:
        while True:
            current_time = time.time()

            if not motion_cooldown_time or current_time >= motion_cooldown_time:
                if motion_cooldown_time:
                    motion_cooldown_time = 0
                if detect_motion():
                    capture_image()
                    upload_image()
            
            if current_time >= sensor_check_next_time:
                blynk.run()  # Process Blynk events
                if current_time >= light_check_next_time:
                    process_light_data()
                    light_check_next_time = current_time + LIGHT_CHECK_COOLDOWN
                if current_time >= daily_task_next_time:
                    process_soil_data()
                    send_daily_notification()
                    get_next_daily_task_time()
                sensor_check_next_time = current_time + SENSOR_CHECK_COOLDOWN

            sleep(MOTION_CHECK_DELAY)
    except KeyboardInterrupt:
        print("Blynk application stopped.")