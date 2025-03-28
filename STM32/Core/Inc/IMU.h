/*
 * IMU.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef INC_IMU_H_
#define INC_IMU_H_

#include "bno055.h"

typedef struct {
    float roll;
    float pitch;
    float yaw;

    float accelX;
    float accelY;
    float accelZ;

    float gyroX;
    float gyroY;
    float gyroZ;

    float magX;
    float magY;
    float magZ;
} ImuData_t;

void imu_read(void);

int is_imu_initialized(void);

#endif /* INC_IMU_H_ */
