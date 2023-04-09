from mpu6050 import mpu6050
import time

class Gyro(mpu6050):
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
        
        # Calling __init__ of mother class :
        mpu6050.__init__(self,address, bus=1)
    
    def get_gyro(mpu):
        gyro_data = mpu.get_gyro_data()
        gyro_y = round(gyro_data['y'],2)
        if  gyro_y < -200:
            vy = -30
        elif  (gyro_y >= -200 and gyro_y < -50):
            vy = -20
        elif (gyro_y >= -50 and gyro_y < -10): 
            vy = -10    
        elif (gyro_y >= -10 and gyro_y < 10):
            vy = 0
        elif (gyro_y >= 10 and gyro_y < 50):
            vy = 10
        elif (gyro_y >= 50 and gyro_y < 200):
            vy = 20
        elif gyro_y >= 200:
            vy = 30
        else:
            vy = 5
        print("Gyro Y : MPU1 => ", gyro_y, "    vy = ", vy)
        print("-------------------------------")
        return vy
    
    def calibrate():
        pass
    
def main():
    gyro_1=Gyro(Gyro.I2C_ADDRESS_1, 'y', mpu6050.GYRO_RANGE_500DEG)
    gyro_2=Gyro(Gyro.I2C_ADDRESS_2, 'y', mpu6050.GYRO_RANGE_500DEG)
    while True:
        gyro_1_data = gyro_1.get_gyro_data()
        gyro_2_data = gyro_2.get_gyro_data()
        print("Gyro Y : G1 => "+str(round(gyro_1_data[gyro_1.axis],2))+"    G2 => "+str(round(gyro_2_data[gyro_2.axis],2)))
        print("-------------------------------")
        time.sleep(1)

if __name__ == '__main__':
    main()
