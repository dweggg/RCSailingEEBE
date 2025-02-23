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
    ImuData_t imuData;
    RadioData_t radioData;
    AdcData_t adcData;

} TelemetryData_t;

void telemetry(void);

#endif /* INC_TELEMETRY_H_ */
