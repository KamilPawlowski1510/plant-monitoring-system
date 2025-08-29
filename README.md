# Video Demo Link
https://youtu.be/cGkcwfD4578

# Lemon tree monitoring and protection system
#### Student Name: *Kamil Pawlowski*
#### Student ID: *20102337*

I have a 3 year old lemon tree in my room on the floor. There are a bunch of things that I must manage to make sure it stays healthy. As is I need to check and deal with these things manually, I thought it would be interesting to automate this whole process. On top of that I want to add a system where, should the pot be touched or bumped in any way, a camera can take a picture of who did it and using a trained model figure out specifically who it was. 

The chores I have to do for the tree include:
- Watering it once the soil is dry
- Making sure it gets adequate lighting
- Mist it every third day
- Rotate it 90 degrees every day so that it gets light from all sides

## Tools, Technologies and Equipment

General:
- VSCode
- Raspberry pi
- MS Azure account
- Blynk
- Python
- Managing regular checks (such as light) and daily checks (such as soil moisture) in an efficient manner

Soil:
- Soil moisture sensor

Light:
- Light sensor
- Relay (to simulate turning on the grow light)

Monitoring:
- Camera to snap pictures
- Motion detection (through sense HAT accelerometer)
- Custom Vision model trained with potential plant harassers
- Upload taken pictures to MS Azure

## Project Repository
https://github.com/KamilPawlowski1510/plant-monitoring-system
