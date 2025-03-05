/*
 * IMU.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "IMU.h"
#include "cmsis_os.h"      // For osMessageQueuePut
#include "i2c.h"      // For osMessageQueuePut
extern osMessageQueueId_t imuQueueHandle;


static bno055_t bno = (bno055_t){
    .i2c = &hi2c3, .addr = BNO_ADDR, .mode = BNO_MODE_NDOF,
};
ImuData_t imuDataSent= {0};


void imu_read(void) {

    static int initialized = 0;
    if (!initialized) {
        // Initialize the sensor
        bno055_init(&bno);
        initialized = 1;
    }


    // Fetch accelerometer data (X, Y, Z)
    bno055_vec3_t accelData;
    if (bno055_acc(&bno, &accelData) == BNO_OK) {
    	imuDataSent.accelX = accelData.x;
    	imuDataSent.accelY = accelData.y;
    	imuDataSent.accelZ = accelData.z;
    }

    // Fetch gyroscope data (X, Y, Z)
    bno055_vec3_t gyroData;
    if (bno055_gyro(&bno, &gyroData) == BNO_OK) {
    	imuDataSent.gyroX = gyroData.x;
    	imuDataSent.gyroY = gyroData.y;
    	imuDataSent.gyroZ = gyroData.z;
    }

    // Fetch magnetometer data (X, Y, Z)
    bno055_vec3_t magData;
    if (bno055_mag(&bno, &magData) == BNO_OK) {
    	imuDataSent.magX = magData.x;
    	imuDataSent.magY = magData.y;
    	imuDataSent.magZ = magData.z;
    }

    // Fetch Euler angles (Roll, Pitch, Yaw)
    bno055_euler_t eulerData;
    if (bno055_euler(&bno, &eulerData) == BNO_OK) {
    	imuDataSent.roll = eulerData.roll;
    	imuDataSent.pitch = eulerData.pitch;
    	imuDataSent.yaw = eulerData.yaw;
    }

    // Post the sensor data to the message queue.
    osMessageQueuePut(imuQueueHandle, &imuDataSent, 0, 0);
}
