/*
 * ANALOG.h
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#ifndef INC_ANALOG_H_
#define INC_ANALOG_H_

#include <stdint.h>

volatile extern uint16_t adc_raw_readings[4];

typedef struct {
	float windDirection;
	float batteryVoltage;
	float extra1;
	float extra2;
} AdcData_t;

void adc_read(void);

#endif /* INC_ANALOG_H_ */
