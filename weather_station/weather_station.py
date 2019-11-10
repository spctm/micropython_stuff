"""
Program to read temperature and humidity from SHT31-DI sensor, display them
to a SSD1306 OLED display, and upload the values to thingspeak.com.

The program uses MQTT protocol to communicate with thingspeak and upload the
data. MQTT is a machine-to-machine IoT connectivity protocol. It was designed
as an extremely lightweight publish/subscribe messaging transport.


Author: Govindarajan
"""


from machine import I2C
from machine import Pin
from machine import Timer
import time
import micropython
import network
from umqtt.simple import MQTTClient

from sht31d import SHT31D
from ssd1306 import SSD1306_I2C as ssd


# ThingSpeak Credentials:
SERVER = "mqtt.thingspeak.com"
CHANNEL_ID = "888456"
WRITE_API_KEY = "IDXXXXXXXXXXX"
INTERVAL = 60
INTERVAL_MS = INTERVAL * 1000
# WiFi Credentials 
WIFI_SSID = "GuestSSID"
WIFI_PASS = "PASSWD"

# Initialize I2C and the devices (sensor and oled display)
i2c = I2C(sda=Pin(21), scl=Pin(22))
sht31 = SHT31D(sda=21, scl=22, address=69)
oled = ssd(128, 64, i2c, 0x3c)
# Initialize MQTT client object
client = MQTTClient("umqtt_client", SERVER)
# Create the MQTT topic string
topic = "channels/" + CHANNEL_ID + "/publish/" + WRITE_API_KEY
# Initialize temperature and humidity values
temp = 0.0
humidity = 0.0


def clear_display():
    """
    Function to clear the ssd1306 oled display
    
    :param: None
    :return: None
    """
    oled.fill(0)
    oled.show()

def connect_wifi(timeout=60):
    """
    Function to connect ESP32 device to WiFi network
    
    :param timeout: Timeout value beyond which an exception is raised
    :return: None
    """
    oled.fill(0)
    oled.text("Connecting to", 5, 18)
    oled.text("   WiFi ...  ", 3, 36)
    oled.show()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            if timeout < 1:
                raise Exception("Failed to connect to Wifi")
            time.sleep(1)
            timeout = timeout - 1
        print("Got IP address %s" % wlan.ifconfig()[0])
        clear_display()
        oled.fill(0)
        oled.text("WiFi Connected", 4, 30)
        oled.show()
        time.sleep(1)
        
def publish_data(_):
    """
    Function to publish the sampled data to thingspeak channel
    
    :param _: Argument needed for micropython schedule method. Not used
    :return: None
    """
    temp, humidity = sht31.get_data()
    print("Temp : %.2f C" % temp)
    print("Humi : %.2f " % humidity + "%")
    oled.fill(0)
    oled.text("Temp : %.2f C" % temp, 2, 16)
    oled.text("Humi : %.2f " % humidity + "%", 2, 36)
    oled.show()
    payload = "field1=" + str(temp) + "&field2=" + str(humidity)
    client.connect()
    client.publish(topic, payload)
    client.disconnect()
    
def schedule(tim):
        """
        A simple call back function that just schedules publish_data function
        
        :param: None
        :return: None
        """
        micropython.schedule(publish_data, 0)

def main():
    """
    Main entry point into this program
    
    :param: None
    :return: None
    """
    micropython.alloc_emergency_exception_buf(100)
    connect_wifi()
    oled.fill(0)
    oled.text("Waiting for data", 0, 29)
    oled.show()
    timer = Timer(-1)
    timer.init(mode=Timer.PERIODIC, period=INTERVAL_MS, callback=schedule)

    
if __name__ == '__main__':
    main()
