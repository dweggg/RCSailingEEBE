/*
 * CONTROL.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "CONTROL.h"
#include "tim.h"
#include "cmsis_os.h"  // Include RTOS for queue handling

/* Global static struct to hold received data */
static RadioData_t radioDataReceived;

/* Channel selector global variable (default to CH1) */
uint8_t selectedChannel = 1;

extern osMessageQueueId_t radioQueueHandle; // Ensure this is defined in your main.c or relevant RTOS file

int16_t pulse = 0;
float compare = 0;
float ms = 0;
float map(float x, float in_min, float in_max, float out_min, float out_max);

void control(void) {
    /* Receive from the queue (non-blocking) */
    RadioData_t newRadioData;
    if (osMessageQueueGet(radioQueueHandle, &newRadioData, NULL, 0) == osOK) {
        /* Update the global radioDataReceived */
        radioDataReceived = newRadioData;
    }

    /* Get the selected channel value */
    uint32_t selectedPulseWidth;
    switch (selectedChannel) {
        case 1: selectedPulseWidth = radioDataReceived.ch1; break;
        case 2: selectedPulseWidth = radioDataReceived.ch2; break;
        case 3: selectedPulseWidth = radioDataReceived.ch3; break;
        case 4: selectedPulseWidth = radioDataReceived.ch4; break;
        default: selectedPulseWidth = radioDataReceived.ch1; break; // Default to CH1 if invalid
    }

    /* Convert pulse width from µs to ms */
    ms = (float)selectedPulseWidth / 1000.0F; // Convert µs to ms

    /* Ensure the value is within the valid servo range */
    if (ms < 1.0F) ms = 1.0F;
    if (ms > 2.0F) ms = 2.0F;

    /* Scale for timer compare value */
    compare = ms * 59999.0F / 20.0F;

    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, (long)compare);
}

float map(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
