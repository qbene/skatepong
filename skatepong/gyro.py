from mpu6050 import mpu6050
import time

class Gyro_one_axis(mpu6050):
    # i2c addresses for MPU6050 sensors
    I2C_ADDRESS_1 = 0x68 # Default (or A0 connected to GND)
    I2C_ADDRESS_2 = 0x69 # A0 connected to VCC
    
    def __init__(self, address, axis, sensitivity, bus=1):
        self.axis = axis
        """For axis, use one of the following parameter:
        'x'
        'y'
        'z'
        """        
        self.sensitivity = sensitivity
        """For sensitivity, use one of the following constants:
        mpu6050.GYRO_RANGE_250DEG
        mpu6050.GYRO_RANGE_500DEG
        mpu6050.GYRO_RANGE_1000DEG
        mpu6050.GYRO_RANGE_2000DEG
        """
        self.offset = 0
        self.error = False
        self.ready_for_reinit = False
        
        # Calling __init__ of mother class :
        mpu6050.__init__(self,address, bus=1)
    
    def get_data(self):

        gyro_data = self.get_gyro_data()[self.axis]

        return gyro_data

    
    def measure_gyro_offset(self, nb_calib_pts = 500):
        """
        Calculates the average offset given by the gyroscope on the chosen axis.
        """
        i = 1
        gyro_sum = 0
        while i <= nb_calib_pts:
            if i == 1:
                print("Gyroscope average offset (" + self.axis + " axis) calculation ongoing...")
            #gyro_sum += self.get_gyro_data()[self.axis]
            gyro_sum += self.get_data()
            i += 1
        gyro_offset = gyro_sum / nb_calib_pts
        print("Gyroscope average offset measured ("+ self.axis + " axis) :", str(round(gyro_offset,2)))
        self.offset = gyro_offset
        return gyro_offset
    
def main():
    gyro_1 = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_1, 'y', mpu6050.GYRO_RANGE_500DEG)
    gyro_2 = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_2, 'y', mpu6050.GYRO_RANGE_500DEG)
    print("Gyroscope 1 :")
    gyro_1_offset = gyro_1.measure_gyro_offset(500)
    print("Gyroscope 2 :")
    gyro_2_offset = gyro_2.measure_gyro_offset(500)
    
    while True:
        gyro_1_raw = gyro_1.get_data()
        gyro_2_raw = gyro_2.get_data()
        gyro_1_calibrated = gyro_1_raw - gyro_1_offset
        gyro_2_calibrated = gyro_2_raw - gyro_2_offset
        print("Gyro 1 (" + gyro_1.axis + " axis) => Raw data :", str(round(gyro_1_raw,2)), "/ Calibrated data :", str(round(gyro_1_calibrated,2)))
        print("Gyro 2 (" + gyro_2.axis + " axis) => Raw data :", str(round(gyro_2_raw,2)), "/ Calibrated data :", str(round(gyro_2_calibrated,2)))
        print("-------------------------------")
        time.sleep(1)


if __name__ == '__main__':
    main()
