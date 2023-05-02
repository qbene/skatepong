#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

from mpu6050 import mpu6050
import time

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

class Gyro_one_axis(mpu6050):
    """
    Handles gyroscope measurements along one axis.
    """
    # i2c addresses for MPU6050 sensors
    I2C_ADDRESS_1 = 0x68 # Default (or A0 connected to GND)
    I2C_ADDRESS_2 = 0x69 # A0 connected to VCC
    
    def __init__(self, address, axis, sensitivity, bus = 1):
        # Calling '__init__' of mother class:
        mpu6050.__init__(self, address, bus = 1)
        mpu6050.set_gyro_range(self, sensitivity)
        self.numerical_sensitivity = mpu6050.read_gyro_range(self)
        # Personal class init:
        self.axis = axis # 'x' / 'y' / 'z'
        self.sensitivity = sensitivity # Used for gyroscope init
        self.prev_time = time.time()
        """
        For sensitivity, use one of the following constants:
        mpu6050.GYRO_RANGE_250DEG = 0x00 # +/- 125 deg/s
        mpu6050.GYRO_RANGE_500DEG = 0x08 # +/- 250 deg/s
        mpu6050.GYRO_RANGE_1000DEG = 0x10 # +/- 500 deg/s
        mpu6050.GYRO_RANGE_2000DEG = 0x18 # +/- 1000 deg/s
        """
        self.offset = 0
        self.error = False
        self.ready_for_reinit = False
        self.pos = 0 # Position in degrees (0 = center, >0 = right)

    def get_data(self):
        """
        Returns angular rotation (in deg/s) along the chosen axis.
        """
        gyro_data = self.get_gyro_data()[self.axis]
        return gyro_data

    def measure_gyro_offset(self, nb_calib_pts = 500):
        """
        Calculates the average gyro offset along the chosen axis.
        """
        i = 1
        gyro_sum = 0
        while i <= nb_calib_pts:
            if i == 1:
                print("Gyroscope average offset (" + self.axis + \
                      " axis) calculation ongoing...")
            gyro_sum += self.get_data()
            i += 1
        gyro_offset = gyro_sum / nb_calib_pts
        print("Gyroscope average offset measured ("+ self.axis + \
              " axis) :", str(round(gyro_offset, 2)))
        self.offset = gyro_offset
        return gyro_offset

    def get_position(self):
        """
        Returns the position (deg) of the gyroscope on the given axis.
        0 deg = skateboard in the middle position
        >0 deg = skateboard to the right
        <0 deg = skateboard to the left
        """
        cur_time = time.time()
        gyro_raw = self.get_data()
        gyro_calib = gyro_raw - self.offset
        if gyro_calib < -0.3 or gyro_calib > 0.3: # Filter
            self.pos += gyro_calib * (cur_time - self.prev_time)
        self.prev_time = cur_time
        
    
def main():
    gyro_1 = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_1, 'y', \
             mpu6050.GYRO_RANGE_1000DEG)
    gyro_2 = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_2, 'y', \
             mpu6050.GYRO_RANGE_1000DEG)

    print("Gyroscope 1 :")
    print("Sensitivity:", str(gyro_1.numerical_sensitivity), "deg/s")
    gyro_1_offset = gyro_1.measure_gyro_offset()
    print("Gyroscope 2 :")
    print("Sensitivity:", str(gyro_2.numerical_sensitivity), "deg/s")
    gyro_2_offset = gyro_2.measure_gyro_offset()
    
    while True:
        gyro_1_raw = gyro_1.get_data()
        gyro_2_raw = gyro_2.get_data()
        gyro_1_calibrated = gyro_1_raw - gyro_1_offset
        gyro_2_calibrated = gyro_2_raw - gyro_2_offset
        print("Gyro 1 (" + gyro_1.axis + " axis) => Raw data :", \
              str(round(gyro_1_raw,2)), "/ Calibrated data :", \
              str(round(gyro_1_calibrated,2)))
        gyro_1.get_position()
        #gyro_2.get_position()
        print ("Gyro 1 position =", str(round(gyro_1.pos,3)), "deg/s")
        #print("Gyro 2 (" + gyro_2.axis + " axis) => Raw data :", \
        #      str(round(gyro_2_raw,2)), "/ Calibrated data :", \
        #      str(round(gyro_2_calibrated,2)))
        print("-------------------------------")
        #time.sleep(1/20)

if __name__ == '__main__':
    main()
