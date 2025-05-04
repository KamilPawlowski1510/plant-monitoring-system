#import BlynkLib
from time import sleep
from grove.grove_relay import GroveRelay
import time
#from seeed_dht import DHT
import io
from picamera import PiCamera
from grove.grove_moisture_sensor import GroveMoistureSensor
from grove.adc import ADC
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from sense_hat import SenseHat


adc = ADC(0x08)
# sensor = DHT("11", 16)

#initialise Relay
relay = GroveRelay(5)

#initialise Light sensor
light_sensor = GroveLightSensor(2)
light_sensor.adc = adc

#initialise Moisture sensor
moisture_sensor = GroveMoistureSensor(3)
moisture_sensor.adc = adc


#initialise Camera
camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 180
#time.sleep(2)

#initialise Sense hat
sense = SenseHat()



# # Register handler for virtual pin V1 write event
# @blynk.on("V1")
# def handle_v1_write(value):
#     button_value = value[0]
#     print(f'Current swith value: {button_value}')
#     if button_value=="1":
#         relay.on()
#     else:
#         relay.off()


# Main loop to keep the Blynk connection alive and process events
if __name__ == "__main__":
    while True:
        print()
        print("Sensor test started")
        print("Test 1: Relay")
        print("Test 2: Camera")
        print("Test 3: Moisture")
        print("Test 4: Light")
        print("Test 5: Sense Hat")
        choice = input("Type 1-5 to run a test: ")

        # Relay tests
        if choice == "1":
            print("Turning relay on")
            relay.on()
            time.sleep(3)
            print("Turning relay off")
            relay.off()
        
        # Camera tests
        elif choice == "2":
            print("Capturing picture")
            image = io.BytesIO()
            camera.capture(image, 'jpeg')
            image.seek(0)

            with open('image.jpg', 'wb') as image_file:
                image_file.write(image.read())
        
        # Moisture tests
        elif choice == "3":
            print(f"Moisture: {moisture_sensor.moisture} mV")
            #print(f"Moisture: {adc.read(3)}")
        
        # Light tests
        elif choice == "4":
            #print(f"Light: {adc.read(1)}")
            print(f"Light: {light_sensor.light}")
        
        elif choice == "5":
            #sense.show_message("Hello world!")
            while True:
                print(sense.get_accelerometer_raw())
                #print(sense.get_orientation())
                sleep(0.1)

    # try:
    #     last_temp_time = 0  # Track the last time temperature was sent
    #     while True:
    #         blynk.run()  # Process Blynk events
    #         current_time = time.time()

    #         if current_time - last_temp_time >= 10: #send temp message every 10 seconds
    #             _, temp = sensor.read()
    #             blynk.virtual_write(0, temp)
    #             last_temp_time = current_time

    #         time.sleep(2)  # Run every 2 second
    # except KeyboardInterrupt:
    #     print("Blynk application stopped.")
