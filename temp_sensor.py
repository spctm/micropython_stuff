"""
Python program to read temperature data from the following two sensors

    Sensor 1 : Analog Devices TMP36
    Sensor 2 : Sensirion SHT31-DI

TMP36 is an analog device and the sensor can be read via ADC, while SHT31-DI 
is an I2C device and this sensor can be read via I2C protocol.

A timer interrupt is set up that fires every 10 seconds when both the sensors
are read. The resulting sensor data is converted into Celsius using calculation
provided in the respective sensors' datasheet. Finally, this temperature value
is converted from Celsius to Fahrenheit before sending them to host computer
via serial communication protocol.


Author: Govindarajan
"""


import os
import time
import pyb
import micropython


class TMP36():
    """
    Set up a simple class for Analog Devices TMP36 sensor
    """

    def __init__(self, pin_num):
        """
        Initialize pin and set up ADC instance
        """
        pin = pyb.Pin(pin_num)
        self.adc = pyb.ADC(pin)
        
    def read(self):
        """
        Read sensor and retrieve the raw value reported by the sensor
        """
        return self.adc.read()
        
    def get_temperature(self, val=None, fahrenheit=False):
        """
        Method to convert the raw sensor data to temperature. By default
        temperature is returned in units of Celsius but when fahrenheit flag is
        set to True, temperature is returned as Fahrenheit value
        """
        raw_val = val
        
        if not raw_val:
            raw_val = self.read()
        
        # Convert raw sensor value into millivolts
        # vRef is 3300mv and resolution of 12-bits
        mv = raw_val  * 3300/4095
        # Offset of 500mv has to be subtracted as per datasheet and divided
        # by 10 to arrive at Celsius value
        celsius = (mv - 500)/10.0
        ratio = 9.0/5.0
        
        if fahrenheit:
            # Convert Celsius to Fahrenheit
            return ((celsius * ratio) + 32)
        
        return celsius
    

class SHT31D():
    """
    Class for Sensirion SHT31-DI I2C temperature and humidity sensor
    """
    def __init__(self, bus=1, address=0x44):
        """
        Initialize the SHT31-D device with the correct I2C address of 0x44. The
        device is conncted to either I2C bus 1 or 2 on the Micropython board as
        it has two I2C buses. Finally, create the I2C instance
        """
        
        if not address or not bus:
            raise Exception("I2C address not provided")
        
        self.address = address
        self.i2c = pyb.I2C(bus)
        
    def read(self):
        """
        Read sensor and retrieve the raw value reported by the sensor. Since
        data is gathered under One-Shot mode, the I2C bus has to initialized
        each time sensor is read. Clock stretching is assumed to be disabled.
        A hex code of 0x2400 is sent to the sensor corresponding to a high
        repeatability condition. Then 6 bytes are read from the sensor, which
        has the raw temperature data.
        """
        self.i2c.init(pyb.I2C.MASTER, addr=self.address, baudrate=100000)
        time.sleep_ms(50)
        ret = self.i2c.send(b'\x24\x00', self.address)
        time.sleep_ms(50)
        raw_val = self.i2c.recv(6, self.address)
        return raw_val
        
    def get_temperature(self, val=None, fahrenheit=False):
        """
        Given the raw sensor data (6 bytes) this method calculates the actual
        temperature by left shifting by 8 the first element of the given array
        and adding the second element to it. Finally, Celsius value is calculated
        by dividing this value by 65535 , multiplying the result by 175 and then
        finally subtracting 45 from that result.
        If fahrenheit flag is set to True, result is converted to Fahrenheit and
        returned.
        """
        raw_val = val

        if not raw_val:
            raw_val = self.read()
        
        # Convert raw sensor data to Celsius
        raw_temp = (raw_val[0] << 8) + raw_val[1]
        celsius = (175 * raw_temp/65535) - 45
        ratio = 9.0/5.0
        
        if fahrenheit:
            # Convert Celsius to Fahrenheit
            return (315 * raw_temp/65535) - 49
        
        return celsius


class SensorTemp():
    """
    Wrapper class to initialize both sensors and read from them after
    setting up a Timer interrupt
    """
    def __init__(self):
        self.seconds = 0
        self.tmp36 = TMP36('Y12')
        self.sht31d = SHT31D(bus=1, address=0x44)
        self.tmp36_ref = self.tmp36.get_temperature
        self.sht31d_ref = self.sht31d.get_temperature
        self.get_temp_ref = self.get_temperature
        self.serial = pyb.UART(1, 115200)
        self.serial.init(9600, bits=8, parity=None, stop=1)
        self.strf_format = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'
    
    def collect(self):
        """
        Set up Timer interrupt that fires every 10 seconds. Clock used for this
        in the Micropython board is 84MHz. Prescaler of 83 + 1 sclaes this 
        frequency to 1MHz. Finally, a period of 9999999 + 1 = 10000000 equates to
        10 seconds. Call back function is specified in the timer instance.
        """
        header = "Time, Elapsed(s), TMP36(F), SHT31D(F)"
        self.serial.write(header)
        print(header)
        self.timer = pyb.Timer(2, prescaler=83, period=9999999)
        micropython.alloc_emergency_exception_buf(100)
        self.timer.callback(self.schedule)

    def schedule(self, tim):
        """
        A simple call back function that just schedules get_temperature method.
        """
        micropython.schedule(self.get_temp_ref, 0)

    def get_temperature(self, _):
        """
        Call the needed sensor methods and get the temperature values from both
        of them. Create an output string and append temperature values to the
        time string before writing to serial port so that the same can be
        received by the host machine.
        """
        t = time.localtime()
        strf_time = self.strf_format.format(t[0], t[1], t[2], t[3], t[4], t[5])
        tmp36_fahrenheit = self.tmp36_ref(fahrenheit=True)
        sht31d_fahrenheit = self.sht31d_ref(fahrenheit=True)
        output_string = "%s, %s, %.2f, %.2f" % (str(strf_time), str(self.seconds),
                                                tmp36_fahrenheit, sht31d_fahrenheit)
        print(output_string)
        # Write to serial port
        self.serial.write(output_string)
        self.seconds += 10
        
        if self.seconds > 1000:
            # Stop collecting temperature data after 1000 seconds
            print("Finished collecting temperature data")
            self.timer.deinit()
        
    os.sync()

s = SensorTemp()
s.collect()
