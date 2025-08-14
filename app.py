from datetime import datetime
import time
from time import sleep

import BlynkLib
from azure.storage.blob import ContainerClient, ContentSettings

from hardware_manager import HardwareManager

# Authentication
BLYNK_AUTH = "7os_iwPxKnhgay7WX-KhXgzXi9mgb2Ib"
AZURE_CONTAINER_AUTH = "DefaultEndpointsProtocol=https;AccountName=smskman1510;AccountKey=6uIe1RPi+CLyvKpJHIGExkPAse9pRepXThBE+tIkobiPawHuPIQS5NvoiT/ycuJP8Uw9HGn3o8+3+AStJoSimQ==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME = "plant-monitoring-images"

# Delays (seconds)
MOTION_CHECK_DELAY = 0.1 # Between motion checks
MOTION_CHECK_COOLDOWN = 2 # Ignore motion after detection
SENSOR_CHECK_COOLDOWN = 60 # Between non-motion sensor checks

# Sensor thresholds
LIGHT_MIN_VALUE = 300 # Before turning on relay
MOISTURE_MAX_VALUE = 1200 # Before watering notification
MISTING_FREQUENCY = 2 # Days between misting (every xth day)


# Hardware and cloud interfaces
hardware_manager = HardwareManager()
blynk = BlynkLib.Blynk(BLYNK_AUTH) # Initialise the Blynk instance
container_client = ContainerClient.from_connection_string(
    AZURE_CONTAINER_AUTH,
    AZURE_CONTAINER_NAME
) # Azure blob storage container

# User config
daily_task_hour = 12
# TODO Make light min, soil max, and misting delay be customisable by user

# Timestamps
motion_check_unblock_time = 0 # Next time motion checks are allowed from
sensor_check_time = 0
daily_task_time = 0

# Blynk notification values
misting_counter = 0
watering_needed = False


def process_light_data():
    """Read light sensor data, control relay as needed, update Blynk."""
    light = hardware_manager.get_light_data()
    blynk.virtual_write(0, light)

    if light < LIGHT_MIN_VALUE:
        hardware_manager.turn_on_relay()
        blynk.virtual_write(2, "Currently On")
    else:
        hardware_manager.turn_off_relay()
        blynk.virtual_write(2, "Currently Off")


def process_moisture_data():
    """Read moisture sensor data, update Blynk, decide if watering is needed."""
    global watering_needed
    moisture = hardware_manager.get_moisture_data()
    blynk.virtual_write(1, moisture)

    watering_needed = moisture > MOISTURE_MAX_VALUE


def update_daily_task_time():
    """Updates daily_task_time to the next instance of the daily_task_hour."""
    global daily_task_time

    daily_task_time = datetime.now().replace(
        hour=daily_task_hour,
        minute=0,
        second=0,
        microsecond=0
    ).timestamp()

    # Add a day if it's past the daily task hour
    if daily_task_time <= current_time:
        daily_task_time += 86400
    
    time_str = datetime.fromtimestamp(daily_task_time).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Next time for daily tasks: {time_str}")


@blynk.on("V4")
#def handle_v4_write(value):
def blynk_daily_hour_change(value):
    """Updates daily_task_hour based on user input through Blynk."""
    global daily_task_hour
    daily_task_hour = value[0]
    print(f'User set daily task hour to: {daily_task_hour}')

    update_daily_task_time()


def send_daily_notification():
    """Determine todays tasks for the user and send a notification via Blynk."""
    global misting_counter
    message = "Todays tasks: Rotate the plant"

    if misting_counter >= MISTING_FREQUENCY -1:
        message += ", mist the plant"
        misting_counter = 0
    else:
        misting_counter += 1

    if watering_needed:
        message += ", water the plant"
        
    blynk.log_event("daily_notification", message)
    # TODO Add to dashboard daily tasks, for user clarity


def upload_image():
    """Upload image from Pi camera to Azure Blob Storage"""
    with open(file="image.jpg", mode="rb") as data:
        container_client.upload_blob(
            name="image.jpg",
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type="image/jpeg")
        )


# Main loop to process sensor data, send and receive data to/from Blynk, upload images to azure and manage timekeeping
if __name__ == "__main__":
    try:
        while True:
            current_time = time.time()

            # Motion detection
            if current_time >= motion_check_unblock_time and hardware_manager.detect_motion():
                motion_check_unblock_time = current_time + MOTION_CHECK_COOLDOWN

                hardware_manager.capture_image()
                upload_image()
                # TODO: Notification here
            
            # Sensor checks
            if current_time >= sensor_check_time:
                blynk.run()  # Process Blynk events
                process_light_data()

                # Daily tasks
                if current_time >= daily_task_time:
                    process_moisture_data()
                    send_daily_notification()

                    update_daily_task_time()

                sensor_check_time = current_time + SENSOR_CHECK_COOLDOWN

            sleep(MOTION_CHECK_DELAY)

    except KeyboardInterrupt:
        print("Blynk application stopped.")