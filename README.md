# General Overview of Mock HVAC

## Files Included:
- Freenove_DHT.py
- Mock HVAC.py  

"Freenove_DHT" is an open-source library and is required for basic functionality
 of the Digital Humidity and Temperature (DHT) sensor. "Mock HVAC" is the main
 program using multithreading to split initializing event detection from sensors
  and measure ambient temperature to update display with live readings.

## LCD Display Status
The LCD provides information on the HVAC System letting the user know whether
the door is open/closed, whether the AC/Heater is turned on, the temperature
the HVAC System is set to, the current ambient temperature reading, and if the
"light" in the room in turned on/off.

## Temperature Control
The Blue and Red buttons control increasing/decreasing (respectively) what
temperature the HVAC System is set to. If the measured temperature and the
ambient room temperature differ by more than 3+ degrees, then the AC/Heater will
kick on. Lastly, the range of the HVAC System is restricted to stay between
65-85 degrees, inclusive.

## Motion Controlled Lighting
The system isn't directly connected to a light source, but acts as if there was
one connected. When the Passive Infrared (PIR) Sensor detects movement, it
signals for the light source to turn on. When there is no longer any movement,
the light will stay on for an additional 10 seconds before turning off.

## Perimeter Monitoring
Pressing the green button is meant to imitate entering/exiting the household.
If the door is left open and the AC/Heater is on, the HVAC System will
automatically turn off the AC/Heater to save on the energy bill. Once the door
is closed, it will resume the original state prior to opening the door.
