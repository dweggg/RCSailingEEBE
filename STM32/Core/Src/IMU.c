/*
 * IMU.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "IMU.h"
#include "CONTROL.h"
#include "cmsis_os.h"      // For osMessageQueuePut
#include "i2c.h"      // For osMessageQueuePut
#include <math.h>

extern osMessageQueueId_t imuQueueHandle;


static bno055_t bno = (bno055_t){
    .i2c = &hi2c3, .addr = BNO_ADDR, .mode = BNO_MODE_NDOF,
};
ImuData_t imuDataSent= {0};

int imu_initialized = 0;
enum _error_bno imu_error;

static float speed = 0.0f, accelMagnitude = 0.0F;  // Current speed components
static uint32_t lastUpdateTime = 0;  // Last time speed was updated


float alphaAccel = 0.9;

void imu_read(void) {

    if (!imu_initialized) {
    	osDelay(1000);
        // Initialize the sensor
        imu_error = bno055_init(&bno);
        if (imu_error == BNO_OK) {imu_initialized = 1;}
    } else {
		// Fetch accelerometer data (already gravity-compensated)
		bno055_vec3_t accelData;
		if (bno055_acc(&bno, &accelData) == BNO_OK) {
			imuDataSent.accelX = accelData.x;
			imuDataSent.accelY = accelData.y;
			imuDataSent.accelZ = accelData.z;

			// Compute time difference (in seconds)
			uint32_t currentTime = osKernelGetTickCount();
			float deltaTime = (currentTime - lastUpdateTime) * 0.001f;  // Convert ms to s
			lastUpdateTime = currentTime;

			// Integrate acceleration to get speed (v = v0 + a * dt)
			accelMagnitude = sqrtf(accelData.x * accelData.x + accelData.y * accelData.y + accelData.z * accelData.z) - 9.81F;
			speed += accelMagnitude * deltaTime;
			if (accelMagnitude < 0.3f) {
				speed = 0.0f;
			}

			// Store the magnitude of speed (or individual components)
			imuDataSent.speed = low_pass_filter(speed, imuDataSent.speed, alphaAccel);
		} else {
			imu_initialized = 0;
		}

		// Fetch gyroscope data (X, Y, Z)
		bno055_vec3_t gyroData;
		if (bno055_gyro(&bno, &gyroData) == BNO_OK) {
			imuDataSent.gyroX = gyroData.x;
			imuDataSent.gyroY = gyroData.y;
			imuDataSent.gyroZ = gyroData.z;
		} else {
			imu_initialized = 0;
		}

		// Fetch magnetometer data (X, Y, Z)
		bno055_vec3_t magData;
		if (bno055_mag(&bno, &magData) == BNO_OK) {
			imuDataSent.magX = magData.x;
			imuDataSent.magY = magData.y;
			imuDataSent.magZ = magData.z;
		} else {
			imu_initialized = 0;
		}

		// Fetch Euler angles (Roll, Pitch, Yaw)
		bno055_euler_t eulerData;
		if (bno055_euler(&bno, &eulerData) == BNO_OK) {
			imuDataSent.roll = eulerData.roll;
			imuDataSent.pitch = eulerData.pitch;
			imuDataSent.yaw = eulerData.yaw;
		} else {
			imu_initialized = 0;
		}

		// Post the sensor data to the message queue.
		osMessageQueuePut(imuQueueHandle, &imuDataSent, 0, 0);
    }
}

int is_imu_initialized(void){
    return imu_initialized;
}
