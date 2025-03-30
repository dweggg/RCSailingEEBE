/*
 * CONTROL.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef CONTROL_H_
#define CONTROL_H_

#include <stdint.h>
#include "RADIO.h"
#include "SERVO.h"

// Enumeration of the control modes.
typedef enum {
    MODE_CALIBRATION  = -1,  // Calibration mode
    MODE_DIRECT_INPUT =  0,  // Direct input mode
    MODE_AUTO_1       =  1,  // Automatic control mode 1
    MODE_AUTO_2       =  2,  // Automatic control mode 2
    MODE_AUTO_3       =  3,  // Automatic control mode 3
    MODE_AUTO_4       =  4   // Automatic control mode 4
} ControlMode_t;

// Structure to hold control output values (in mechanical angles).
typedef struct {
    float rudder;
    float twist;
    float trim;
    float extra;
} ControlData_t;

// The main control task, which is run by the RTOS.
void control(void);

#endif /* CONTROL_H_ */
