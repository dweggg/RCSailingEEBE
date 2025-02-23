/*
 * IMU.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef INC_IMU_H_
#define INC_IMU_H_

typedef struct {
    float roll;
    float pitch;
    float yaw;

    float aX;
    float aY;
    float aZ;

    float wX;
    float wY;
    float wZ;

    float muX;
    float muY;
    float muZ;
} ImuData_t;

void imu_read(void);

#endif /* INC_IMU_H_ */
