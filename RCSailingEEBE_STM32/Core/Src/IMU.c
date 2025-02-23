/*
 * IMU.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "IMU.h"
#include "bno055_stm32.h"  // Library from https://github.com/ivyknob/bno055_stm32
#include "cmsis_os.h"      // For osMessageQueuePut
extern osMessageQueueId_t imuQueueHandle;

void imu_read(void){
    ImuData_t imuData = {0};

    // Get fused Euler angles from the BNO055 sensor.
    // In the library’s example, bno055_getVectorEuler() returns a bno055_vector_t with:
    //   x = Heading, y = Roll, and z = Pitch.
    bno055_vector_t euler = bno055_getVectorEuler();

    // Map the Euler angles to our IMU data structure:
    imuData.yaw   = euler.x;  // Heading
    imuData.roll  = euler.y;
    imuData.pitch = euler.z;

    bno055_vector_t accel = bno055_getVectorAccelerometer();

    imuData.accelX = accel.x;
    imuData.accelY = accel.y;
    imuData.accelZ = accel.z;

    bno055_vector_t gyro = bno055_getVectorGyroscope();
    imuData.gyroX = gyro.x;
    imuData.gyroY = gyro.y;
    imuData.gyroZ = gyro.z;

    bno055_vector_t mag = bno055_getVectorMagnetometer();
    imuData.magX = mag.x;
    imuData.magY = mag.y;
    imuData.magZ = mag.z;

    // Post the sensor data to the message queue.
    osMessageQueuePut(imuQueueHandle, &imuData, 0, 0);
}
