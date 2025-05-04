from datetime import datetime
import io
import math
import time
from time import sleep

#import BlynkLib
from picamera import PiCamera
from sense_hat import SenseHat

from grove.adc import ADC
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from grove.grove_moisture_sensor import GroveMoistureSensor
from grove.grove_relay import GroveRelay


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

MOTION_CHECK_DELAY = 0.1 # How often to check for motion
MOTION_THRESHOLD = 0.05 # g's acceptable above and below 1 (gravity)
MOTION_CHECK_COOLDOWN = 1.5 # How long to not check for motion after motion was detected
motion_cooldown_time = 0

SENSOR_CHECK_COOLDOWN = 60 # How long to wait between dealing with none motion sensors
sensor_check_next_time = 0

light_check_cooldown = 60 # Every minute by default
light_check_next_time = 0
light_min_value = 300 # Minimum amount of light before turning on relay

soil_check_cooldown = 60 # Every minute by default #TODO Add the correct time (do we want to do it the same hour each day?)
soil_check_next_time = 0
soil_max_value = 1200 # Maximum mV before the plant needs to be watered again

# TODO Figure out how to deal with rotation (do we ask the user how many days to wait?)
# TODO Figure out how to do misting (For ease, we can also do how many days, for fancy version we can do a thing where you select the days)


def log_data(data_type, value, unit):
    date_time = datetime.fromtimestamp(current_time).strftime('%d/%m/%Y, %H:%M:%S')
    formatted_data = f"[{date_time}] {data_type}: {value} {unit}\n"
    with open("logged_data.txt", "a") as f:
        f.write(formatted_data)
    print(formatted_data)

def detect_motion() -> bool:
    data = sense_hat.get_accelerometer_raw()
    force = math.sqrt(data["x"]**2 + data["y"]**2 + data["z"]**2)
    if abs(force - 1) > MOTION_THRESHOLD:
        global motion_cooldown_time
        motion_cooldown_time = time.time() + MOTION_CHECK_COOLDOWN
        log_data("Motion Detected", force, "g")
        return True
    else:
        return False

def process_light_data():
    light = light_sensor.light
    log_data("Light", light, "")
    # TODO Add data to Blynk
    if light < light_min_value:
        relay.on()
        # TODO Add to Blynk that relay true
    else:
        relay.off()
        # TODO Add to Blynk that relay false

def process_soil_data():
    moisture_mv = moisture_sensor.moisture
    log_data("Soil Moisture", moisture_mv, "mV")
    # TODO Add data to Blynk
    if moisture_mv > soil_max_value:
        pass # TODO Push a notification here to Blynk

# TODO ADD BLYNK FUNCTIONS FOR UPDATING VALUES

# Main loop to keep the Blynk connection alive and process events
if __name__ == "__main__":
    while True:
        current_time = time.time()

        if not motion_cooldown_time or current_time >= motion_cooldown_time:
            motion_cooldown_time = 0 # TODO This isn't fully efficient but hardly matters
            if detect_motion():
                pass
                # TODO Implement azure functionality

                # Camera stuff
                #image = io.BytesIO()
                #camera.capture(image, 'jpeg')
                #image.seek(0)
                #with open('image.jpg', 'wb') as image_file:
                    #image_file.write(image.read())
        
        if current_time >= sensor_check_next_time:
            #blynk.run()  # Process Blynk events
            if current_time >= light_check_next_time:
                process_light_data()
                light_check_next_time = current_time + light_check_cooldown
            if current_time >= soil_check_next_time:
                process_soil_data()
                soil_check_next_time = current_time + soil_check_cooldown
            # Rotate plant notification
            # Mist plant notification
            sensor_check_next_time = current_time + SENSOR_CHECK_COOLDOWN

        sleep(MOTION_CHECK_DELAY)
