from datetime import datetime
import time
from time import sleep

from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.storage.blob import ContainerClient, ContentSettings
import BlynkLib
from msrest.authentication import ApiKeyCredentials

from hardware_manager import HardwareManager


# Interface creation attempts limit
MAX_INTERFACE_ATTEMPTS = 3

# Authentication
BLYNK_AUTH = "7os_iwPxKnhgay7WX-KhXgzXi9mgb2Ib"
AZURE_CONTAINER_AUTH = "DefaultEndpointsProtocol=https;AccountName=smskman1510;AccountKey=6uIe1RPi+CLyvKpJHIGExkPAse9pRepXThBE+tIkobiPawHuPIQS5NvoiT/ycuJP8Uw9HGn3o8+3+AStJoSimQ==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME = "plant-monitoring-images"
CUSTOM_VISION_URL = 'https://northeurope.api.cognitive.microsoft.com/customvision/v3.0/Prediction/675f1359-659d-416c-a23f-134e3c3ca9ba/classify/iterations/Iteration2/image'
CUSTOM_VISION_KEY = 'd09e97f6ea7f48f3b7b9128c9fc5bc58'
CUSTOM_VISION_URL_PARTS = CUSTOM_VISION_URL.split('/')
CUSTOM_VISION_ENDPOINT = 'https://' + CUSTOM_VISION_URL_PARTS[2]
CUSTOM_VISION_PROJECT_ID = CUSTOM_VISION_URL_PARTS[6]
CUSTOM_VISION_ITERATION_NAME = CUSTOM_VISION_URL_PARTS[9]

# Delays (seconds)
MOTION_CHECK_DELAY = 0.1 # Between motion checks
MOTION_CHECK_COOLDOWN = 2 # Ignore motion after detection
SENSOR_CHECK_COOLDOWN = 60 # Between non-motion sensor checks

# Sensor thresholds
LIGHT_MIN_VALUE = 300 # Before turning on relay
MOISTURE_MAX_VALUE = 1200 # Before watering notification
MISTING_FREQUENCY = 2 # Days between misting (every xth day)


# Hardware and cloud interfaces
hardware_manager = None
blynk = None
container = None # Azure blob storage container client
custom_vision = None

# User config
daily_task_hour = 12

# Timestamps
motion_check_unblock_time = 0 # Next time motion checks are allowed from
sensor_check_time = 0
daily_task_time = 0

# Blynk notification values
misting_counter = 0
watering_needed = False


def attempt_interface_creation(interface_name: str, function: callable) -> None:
    """Makes multiple attempts to run a interface creating function, shuts down program if all fail"""
    print(f"Attempting to create {interface_name} interface")

    for attempt in range(MAX_INTERFACE_ATTEMPTS):
        try:
            function()
            print("Success")
            break
        except Exception as e:
            print(e)
            if attempt == MAX_INTERFACE_ATTEMPTS - 1:
                print("Max connections attempts exceeded, shutting down app")
                exit()
            else:
                print("Attempting connection again")


def create_hardware_interface() -> None:
    """Creates interface for interacting with hardware"""
    global hardware_manager
    hardware_manager = HardwareManager()


def create_blynk_interface() -> None:
    """Creates interface for interacting with Blynk"""
    global blynk
    blynk = BlynkLib.Blynk(BLYNK_AUTH)
    blynk.on("V4", blynk_daily_hour_change)


def create_container_interface() -> None:
    """Creates interface for interacting with an Azure blob storage container"""
    global container
    container = ContainerClient.from_connection_string(
    AZURE_CONTAINER_AUTH,
    AZURE_CONTAINER_NAME
) 


def create_custom_vision_interface() -> None:
    """Creates interface for interacting with Custom Vision AI"""
    global custom_vision
    prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": CUSTOM_VISION_KEY})
    custom_vision = CustomVisionPredictionClient(CUSTOM_VISION_ENDPOINT, prediction_credentials)


def process_light_data() -> None:
    """Read light sensor data, control relay as needed, update Blynk."""
    light = hardware_manager.get_light_data()
    blynk.virtual_write(0, light)
    print("Sent light data to Blynk")

    if light < LIGHT_MIN_VALUE:
        hardware_manager.turn_on_relay()
        blynk.virtual_write(2, "Currently On")
    else:
        hardware_manager.turn_off_relay()
        blynk.virtual_write(2, "Currently Off")
    print("Sent relay status to Blynk")


def process_moisture_data() -> None:
    """Read moisture sensor data, update Blynk, decide if watering is needed."""
    global watering_needed
    moisture = hardware_manager.get_moisture_data()
    blynk.virtual_write(1, moisture)
    print("Sent moisture data to Blynk")

    watering_needed = moisture > MOISTURE_MAX_VALUE


def update_daily_task_time() -> None:
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


def blynk_daily_hour_change(value):
    """Updates daily_task_hour based on user input through Blynk."""
    global daily_task_hour
    daily_task_hour = int(value[0])
    print(f'User set daily task hour to: {daily_task_hour}')

    update_daily_task_time()


def send_daily_notification() -> None:
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
    print("Sent daily notification to Blynk with message:", message)


def upload_image() -> None:
    """Upload image from Pi camera to Azure Blob Storage"""
    with open(file="image.jpg", mode="rb") as data:
        container.upload_blob(
            name="image.jpg",
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type="image/jpeg")
        )
    print("Uploaded image to Azure blob storage")


def get_attacker_from_image() -> None:
    """Upload image to custom vision and return who was the attacker"""
    with open(file="image.jpg", mode="rb") as image:
        results = custom_vision.classify_image(CUSTOM_VISION_PROJECT_ID, CUSTOM_VISION_ITERATION_NAME, image)
        print("Sent image to Custom Vision")

        print("Attacker predictions:")
        for prediction in results.predictions:
            print(f'{prediction.tag_name}: {prediction.probability * 100:.2f}%')
        
        attacker = results.predictions[0].tag_name.capitalize()
        message = f"{attacker} has touched your plant!"
        blynk.log_event("attack_notification", message)
        print("Sent attacker notification to Blynk with message:", message)


# Main loop to process sensor data, send and receive data to/from Blynk, upload images to azure and custom vision and manage timekeeping
if __name__ == "__main__":
    print("Attempting to create interfaces")
    attempt_interface_creation("hardware", create_hardware_interface)
    attempt_interface_creation("Blynk", create_blynk_interface)
    attempt_interface_creation("Azure blob storage container", create_container_interface)
    attempt_interface_creation("Custom Vision", create_custom_vision_interface)
    print()

    try:
        while True:
            current_time = time.time()

            # Motion detection
            if current_time >= motion_check_unblock_time and hardware_manager.detect_motion():
                motion_check_unblock_time = current_time + MOTION_CHECK_COOLDOWN

                hardware_manager.capture_image()
                upload_image()
                get_attacker_from_image()
                print()
            
            # Sensor checks
            if current_time >= sensor_check_time:
                print("Processing regular tasks")

                print("Running blynk events")
                blynk.run()  # Process Blynk events

                process_light_data()

                # Daily tasks
                if current_time >= daily_task_time:
                    print(f"\nProcessing daily tasks")
                    
                    process_moisture_data()
                    send_daily_notification()

                    update_daily_task_time()

                sensor_check_time = current_time + SENSOR_CHECK_COOLDOWN
                print()

            sleep(MOTION_CHECK_DELAY)

    except KeyboardInterrupt:
        print("Blynk application stopped.")
    
    finally:
        hardware_manager.turn_off_relay()
        blynk.virtual_write(2, "Currently Off")