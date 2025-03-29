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
} TelemetryData_t;

void telemetry(void);

#endif /* INC_TELEMETRY_H_ */
