/*
 * TELEMETRY.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef INC_TELEMETRY_H_
#define INC_TELEMETRY_H_

#include "CONTROL.h"
#include "IMU.h"
#include "ANALOG.h"


typedef struct {
    ControlMode_t mode;

    float rudder_servo_angle;
    float trim_servo_angle;
    float twist_servo_angle;
    float extra_servo_angle;

    float Kp_roll;
    float Ki_roll;
    float Kp_yaw;
    float Ki_yaw;

} TelemetryData_t;

void telemetry(void);

#endif /* INC_TELEMETRY_H_ */
