import RPi.GPIO as GPIO
import time
import requests
import Freenove_DHT
from rpi_lcd import LCD
import threading
import datetime

#GPIO mappings
greenLED = 13  #motion detector light
redLED = 19  #heater led
blueLED = 26  #AC led

greenButton = 16
blueButton = 21
redButton = 20

motionDetector = 24  #motion detector sensor

dhtSignal = 6  #Humidity Sensor signal (board pin #, not GPIO)

# LCD Initialization
lcd = LCD()

#global variables
hvac_temperature = 70
weather = 0
hvac_setting = ""
doorOpen = False
humidity = 0
hvac_start = datetime.datetime.now()
kWH_used = 0.0
total_cost = 0.0
lock = threading.Lock()
motion_detected = False

#setup(): intializes all the sensors/lcd/buttons to either an input or an output
def setup():
    print("Initializing GPIO I/O")
    print("Initializing LCD settings")

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM) 
    GPIO.setup(motionDetector, GPIO.IN) 
    GPIO.setup(greenButton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(blueButton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    GPIO.setup(redButton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    
    #setup lcd
    lcd.backlight(True)

    GPIO.setup(greenLED, GPIO.OUT)    
    GPIO.setup(blueLED, GPIO.OUT)   
    GPIO.setup(redLED, GPIO.OUT)
    
    kWH_used = 0.0
    total_cost = 0.0

def increase_temp(ev = None):
    global hvac_temperature
    global weather
    global hvac_setting
    global lock
    
    if hvac_temperature < 85:
        hvac_temperature += 1
        print("Raising temperature to :%d"%hvac_temperature)
        with lock:
            if doorOpen == True:
                lcd.text("%d/%d     D:OPEN"%(hvac_temperature ,weather), 1)
            else:
                lcd.text("%d/%d     D:SAFE"%(hvac_temperature ,weather), 1)
            if motion_detected == True:
                lcd.text("H:%s     L:ON"%(hvac_setting), 2)
            else:
                lcd.text("H:%s     L:OFF"%(hvac_setting), 2)

def decrease_temp(ev = None):
    global hvac_temperature
    global weather
    global hvac_setting
    global lock

    if hvac_temperature > 65:
        hvac_temperature -= 1
        print("Lowering temperature to :%d"%hvac_temperature)
        with lock:
            if doorOpen == True:
                    lcd.text("%d/%d     D:OPEN"%(hvac_temperature ,weather), 1)
            else:
                    lcd.text("%d/%d     D:SAFE"%(hvac_temperature ,weather), 1)
            if motion_detected == True:
                lcd.text("H:%s     L:ON"%(hvac_setting), 2)
            else:
                lcd.text("H:%s     L:OFF"%(hvac_setting), 2)

def door_movement(ev = None):
    global doorOpen
    global hvac_temperature
    global weather
    global hvac_setting
    global lock
    global hvac_start
    
    
    if doorOpen == False:
        GPIO.output(blueLED,GPIO.LOW)
        GPIO.output(redLED,GPIO.LOW)
        doorOpen = True
        with lock:
            lcd.text("DOOR/WINDOW OPEN", 1)
            lcd.text("HVAC HALTED", 2)
            time.sleep(3)  #time to let lcd print
            energyCalc()
    elif doorOpen == True:
        GPIO.output(greenLED,GPIO.LOW)
        doorOpen = False
        hvac_start = datetime.datetime.now()  #sets start time of when HVAC turns on
        with lock:
            lcd.text("DOOR CLOSED", 1)
            lcd.text("HVAC RESUMED", 2)
            time.sleep(3)  #time to let lcd print

    with lock:
        if doorOpen == True:
            lcd.text("%d/%d     D:OPEN"%(hvac_temperature ,weather), 1)
        else:
            lcd.text("%d/%d     D:SAFE"%(hvac_temperature ,weather), 1)
        if motion_detected == True:
            lcd.text("H:%s     L:ON"%(hvac_setting), 2)
        else:
            lcd.text("H:%s     L:OFF"%(hvac_setting), 2)

#thread will use this function and keep track of when HVAC is on/off
#when HVAC is turned off, will report overall energy cost from duration being on
def energyCalc():
    global hvac_setting
    global hvac_start
    global total_cost
    global kWH_used

    hvac_stop = datetime.datetime.now()
    hours = ((datetime.datetime.now() - hvac_start).total_seconds() ) / 3600
    if hvac_setting == "AC  ":
        kWH_used = round(kWH_used + (hours * 18), 2)  #18 is the # of kWatts consumed by AC per hour
    else:
        kWH_used = round(kWH_used + (hours * 36), 2)  #36 is the # of kWatts consumed by AC per hour
    total_cost = round(kWH_used * 0.5, 2)  #.50 is the cost per kWH
    lcd.text("ENERGY: " + str(kWH_used) + "KWH", 1)
    lcd.text("COST: $" + str(total_cost), 2)
    time.sleep(3)

#if the sensor is triggered turn on the lights
def motionDetect(ev = None):
    global motion_detected
    
    motion_detected = True
    GPIO.output(greenLED,GPIO.HIGH) 
    with lock:
        lcd.text("PERSON DETECTED", 1)
        lcd.text("LIGHT ON", 2)
        time.sleep(1)
    print("Movement Detected turning on light")
    time.sleep(9)  # 10 second delay in combination with previous sleep()
    # if GPIO.input(motionDetector)!=GPIO.HIGH:
    GPIO.output(greenLED,GPIO.LOW)
    print ("No movement, turning off lights")
    motion_detected = False

# loop(): accepts a parameter of humidity and functions as the "main" function to loop
# through various tasks in order to display the proper result
def loop():

    #intialize LEDs to turn off
    GPIO.output(greenLED,GPIO.LOW)
    GPIO.output(blueLED,GPIO.LOW)
    GPIO.output(redLED,GPIO.LOW)

    #global variables
    global hvac_temperature
    global weather
    global hvac_setting
    global lock

    #print to LCD to wait for the 3 second calculation of the temperature
    lcd.text("GATHERING DATA", 1)
    lcd.text("PLEASE WAIT", 2)
    time.sleep(3)  #time to let lcd print

    print("Gathering data for finding average temperature")

    #initialize variables needed in the while loop
    dht = DHT.Freenove_DHT(dhtSignal)
    counts = 0
    avg_temp = 0
    
    while True:
        #global hvac_temperature
        counts += 1
        for i in range(0,15):
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk is dht.DHTLIB_OK):#read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                break

        avg_temp += dht.temperature #variable to caclule the avg temp

        # for every 3 seconds we are going to update the display and check if we need to change the hysterirs
        if (counts % 3 == 0):
            avg_temp = avg_temp / 3
            avg_temp = (avg_temp* (9/5)) + 32
            weather = avg_temp + (0.05 * float(humidity))
            if(hvac_temperature+3 <= weather):
                hvac_setting = "AC  "
                GPIO.output(redLED,GPIO.LOW)
                if doorOpen:
                    GPIO.output(blueLED,GPIO.LOW)
                else:
                    GPIO.output(blueLED,GPIO.HIGH)
            elif(hvac_temperature-3 >= weather):
                hvac_setting = "HEAT"
                GPIO.output(blueLED,GPIO.LOW)
                if doorOpen:
                    GPIO.output(redLED,GPIO.LOW)
                else:
                    GPIO.output(redLED,GPIO.HIGH)

            with lock:
                if doorOpen:
                    lcd.text("%d/%d     D:OPEN"%(hvac_temperature ,weather), 1)
                else:
                    lcd.text("%d/%d     D:SAFE"%(hvac_temperature ,weather), 1)
                if motion_detected == True:
                    lcd.text("H:%s     L:ON"%(hvac_setting), 2)
                else:
                    lcd.text("H:%s     L:OFF"%(hvac_setting), 2)
            time.sleep(3)  #time to let lcd print
            avg_temp = 0;

#destroy(): will release all the GPIO resources
def destroy():
        GPIO.cleanup()                    

if __name__ == '__main__':     # Program entrance
    print("Starting HVAC system")
    setup()
    appKey = '5da604a5-2ac0-4bb5-a0af-2ead523a0602'
    stationID = '75'
    startDate = datetime.datetime.now()
    endDate = datetime.datetime.now()
    dataItems = 'hly-rel-hum'
    hour = int(startDate.strftime("%H") ) - 7  #hour used for CIMIS hourly humidity in PST
    URL = "http://et.water.ca.gov/api/data?appKey=" + appKey + "&targets=" + stationID + "&startDate=" + \
          startDate.strftime('%Y-%m-%d') + "&endDate=" + endDate.strftime('%Y-%m-%d') + "&dataItems=" + dataItems + '&unitOfMeasure=M'
    
    try:
        r = requests.get(url = URL)
        data = r.json()
        humidity = data['Data']['Providers'][0]['Records'][hour]['HlyRelHum']['Value']
        print("Succesfully recieved CIMIS data")
    except Exception as e:
        print("Failure in getting CIMIS data")
        destroy()
    try:
        #initializing threads
        thread1 = threading.Thread(target = loop)
        thread1.setDaemon(True)
        thread1.start()

        #initializing buttons events
        GPIO.add_event_detect(blueButton, GPIO.RISING, callback = decrease_temp, bouncetime = 300)
        GPIO.add_event_detect(redButton, GPIO.RISING, callback = increase_temp, bouncetime = 300)
        GPIO.add_event_detect(greenButton, GPIO.RISING, callback = door_movement, bouncetime = 300)
        GPIO.add_event_detect(motionDetector, GPIO.RISING, callback = motionDetect, bouncetime = 300)
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()