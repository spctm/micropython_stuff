"""
Python driver to read temperature and humidity data from Sensirion SHT31-DI
SHT31-DI is an I2C device and this sensor can be read via I2C protocol.

Raw temperature and humidity in the resulting sensor data is converted into 
Celsius and humidity percentage using calculation provided in the sensors'
datasheet. Temperature is converted from Celsius to Fahrenheit, if specified


Author: Govindarajan
"""


import time
import machine
import micropython


class SHT31D():
    """
    Class for Sensirion SHT31-DI I2C temperature and humidity sensor
    """
    def __init__(self, sda=None, scl=None, address=None):
        """
        Initialize the SHT31-D device with the correct I2C address of 0x44. The
        device is conncted to either I2C bus 1 or 2 on the Micropython board as
        it has two I2C buses. Finally, create the I2C instance
        """
        
        if not address or not sda or not scl:
            raise Exception("I2C address not provided")
        
        self.sda = machine.Pin(sda)
        self.scl = machine.Pin(scl)
        self.address = address
        self.i2c = machine.I2C(sda=self.sda, scl=self.scl, freq=400000)
        
    def init(self):
        """
        """
        self.i2c.init(sda=self.sda, scl=self.scl, freq=400000)
        time.sleep_ms(50)
        
    def _read(self):
        """
        Read sensor and retrieve the raw value reported by the sensor. Since
        data is gathered under One-Shot mode, the I2C bus has to initialized
        each time sensor is read. Clock stretching is assumed to be disabled.
        A hex code of 0x2400 is sent to the sensor corresponding to a high
        repeatability condition. Then 6 bytes are read from the sensor, which
        has the raw temperature data.
        """
        self.init()
        ret = self.i2c.writeto(self.address, b'\x24\x00')
        time.sleep_ms(50)
        raw_val = self.i2c.readfrom(self.address, 6)
        return raw_val
        
    def get_data(self, fahrenheit=False):
        """
        Raw sensor data (6 bytes) from sensor is retrieved and actual 
        temperature is calculated by left shifting by 8 the first element 
        of the returned array and adding the second element to it. Celsius value
        is calculated by dividing this value by 65535 , multiplying the result
        by 175 and then finally subtracting 45 from that result.
        
        Humidity is calculated by left shifting the 3rd element by 8 and adding
        fourth element to it. Actual humidity is then got by dividing the
        raw humidity value by 65535 and multiplying by 100
        
        If fahrenheit flag is set to True, result is converted to Fahrenheit 
        before returning.
        """
        raw_val = self._read()
        # Convert raw sensor data to Celsius
        (raw_temp, raw_humidity) = ((raw_val[0] << 8) + raw_val[1], 
                                   (raw_val[3] << 8) + raw_val[4])
        temperature = (175 * raw_temp/65535) - 45
        
        if fahrenheit:
            # Convert Celsius to Fahrenheit
            temperature = (315 * raw_temp/65535) - 49
        
        humidity = 100 * (raw_humidity/65535)
        
        return temperature, humidity
