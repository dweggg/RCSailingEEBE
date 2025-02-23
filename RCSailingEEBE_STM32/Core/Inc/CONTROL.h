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
	uint32_t width1;
	uint32_t width2;
	uint32_t width3;
	uint32_t width4;
} RadioData_t;


typedef struct {
	float ctrl1;
	float ctrl2;
	float ctrl3;
	float ctrl4;
	float ctrl5;
	float ctrl6;
} ControlData_t;

void control(void);

#endif /* INC_CONTROL_H_ */
