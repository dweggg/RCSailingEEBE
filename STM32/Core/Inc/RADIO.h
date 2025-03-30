/*
 * RADIO.h
 *
 *  Created on: Mar 30, 2025
 *      Author: dweggg
 */


#ifndef RADIO_H_
#define RADIO_H_

#include <stdint.h>

// Structure for raw radio pulse widths (in µs)
typedef struct {
    int16_t ch1;
    int16_t ch2;
    int16_t ch3;
    int16_t ch4;
} RadioData_t;

// Structure for storing calibration boundaries for each channel
typedef struct {
    uint32_t ch1_min;
    uint32_t ch1_max;
    uint32_t ch2_min;
    uint32_t ch2_max;
    uint32_t ch3_min;
    uint32_t ch3_max;
    uint32_t ch4_min;
    uint32_t ch4_max;
} RadioCalibration_t;

// Global calibration data (updated in calibration mode).
extern RadioCalibration_t radioCalibration;

// Call this function periodically (or from an ISR) to update calibration boundaries.
void update_radio_calibration(void);

float map_radio(float radio_val, float min, float max);

// Functions to get a normalized value (0.0–1.0) for each channel.
float get_radio_ch1(void);
float get_radio_ch2(void);
float get_radio_ch3(void);
float get_radio_ch4(void);

#endif /* RADIO_H_ */
