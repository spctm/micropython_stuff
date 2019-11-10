"""
Micropython program to determin the RPM of a motor (with blades). It utilizes
an IR LED and a Phototransistor facing each other to sense any interruption
(like a blade) passing in between. Each falling edge in the ADC pin
fires an interrupt. This can be used to calculate the RPM of the fan.


Author: Govindarajan
"""

import pyb
import time
import micropython


class Tachometer():
    """
    Tachometer class
    """
    def __init__(self, pin_num=None, interval=2, num_blades=5, max_duration=300):
        """
        Set up pin and ADC instances.
        Initialize IRQ counter that counts the number of IRQs received, which
        in turn denotes the number of times fan blade passes across the
        phototransistor
        
        :param pin_num: Pin number on the board where phototransistor output is
                         is connected to. Default is None
        :param interval: Number of seconds to count interrupts for. Default = 2
        :param num_blades: Number of blades on the motor. Default = 5
        :return: None
        """
        self. pin = pyb.Pin(pin_num)
        self.adc = pyb.ADC(self.pin)
        self.irq_count = 0
        self.sample_period = interval
        self.blades = num_blades
        self.num_seconds = 0
        self.max_duration = max_duration
        header = "Seconds, RPM"
        print(header)
        

    def measure(self, line):
        """
        Increment irq counter every time an interrupt is raised
        
        :param line: Default parameter (interrupt line attached) passed by
                     ExtInt()
        :return: None
        """
        self.irq_count += 1
        
    def main(self):
        """
        Main function where interrupt handler is initialized and a callback
        function passed
        
        :param: None
        :return: None
        """
        # Allocate exception buffer since heap cannot be allocated within an ISR context
        micropython.alloc_emergency_exception_buf(100)
        # Set up interrupt handler
        ext_int = pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_FALLING,
                             pyb.Pin.PULL_NONE, self.measure)
        
        while self.num_seconds < (self.max_duration // self.sample_period):
            # Sleep for specified interval to count number of interrupts received
            time.sleep(self.sample_period)
            # Disable IRQs and process result
            pyb.disable_irq()
            rpm = self.irq_count * 60 / (2 * self.blades)
            output_str = str(self.num_seconds) + "," + "{0:.2f}".format(rpm)
            # Print the result to serial console
            print(output_str)
            # Reset IRQ counter for the next interval
            self.irq_count = 0
            self.num_seconds += self.sample_period
            # Enable IRQs
            pyb.enable_irq()
            

# Sleep for a few seconds to let the fan speed settle
time.sleep(15)
pyb.LED(4).toggle()
time.sleep(1)
pyb.LED(4).toggle()
time.sleep(1)
tc = Tachometer(pin_num='X12', max_duration=300)
tc.main()
