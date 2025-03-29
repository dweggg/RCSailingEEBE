/*
 * CONTROL.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef INC_CONTROL_H_
#define INC_CONTROL_H_

#include <stdint.h>

typedef struct {
    int16_t ch1;
    int16_t ch2;
    int16_t ch3;
    int16_t ch4;
} RadioData_t;

typedef struct {
    float ctrl1;
    float ctrl2;
    float ctrl3;
    float ctrl4;
    float ctrl5;
    float ctrl6;
} ControlData_t;

typedef enum {
    MODE_CALIBRATION  = -1,  // Calibration mode
    MODE_DIRECT_INPUT =  0,  // Direct input mode
    MODE_AUTO_1       =  1,  // Automatic control mode 1
    MODE_AUTO_2       =  2,  // Automatic control mode 2
    MODE_AUTO_3       =  3,  // Automatic control mode 3
    MODE_AUTO_4       =  4   // Automatic control mode 4
} ControlMode_t;

void control(void);

#endif /* INC_CONTROL_H_ */
