# Lemon tree monitoring and protection system
#### Student Name: *Kamil Pawlowski*
#### Student ID: *20102337*

I have a 3 year old lemon tree in my room on the floor. There are a bunch of things that I must manage to make sure it stays healthy. As is I need to check and deal with these things manually, I thought it would be interesting to automate this whole process. On top of that I want to add a system where, should the pot be touched or bumped in any way, a camera can take a picture of who did it and using a trained model figure out specifically who it was. 

The chores I have to do for the tree include:
- Watering it once the soil is dry
- Making sure it gets adequate lighting
- Mist it on Tuesdays, Thursdays and Sundays
- Rotate it 180 degrees every day so that it gets light from all sides
- Feed it every second watering

## Tools, Technologies and Equipment

General:
- VSCode
- Raspberry pi
- Ms azure account
- Email account (to receive notifications)
- Python
- Managing regular checks (such as light) and daily checks (such as soil moisture) in an efficient manner

Soil:
- Soil moisture sensor

Light:
- Light sensor
- Relay (to simulate turning on the grow light)

Monitoring:
- Camera to snap pictures
- Motion detection (through phone or ultrasonic ranger)
- Custom vision trained model with potential plant harassers
- Way to distinguish between successful and failed attempts at indentifying harrassers (low probability is failure)
- Upload taken pictures somewhere (ideally send successful pictures one place and failed attempts elsewhere to simulate getting more training data)

## Project Repository
https://github.com/KamilPawlowski1510/plant-monitoring-system
