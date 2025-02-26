/*
 * CONTROL.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "CONTROL.h"
#include "tim.h"
#include "cmsis_os.h"  // For queue handling

/* Global static struct to hold received radio data (pulse widths in µs) */
static RadioData_t radioDataReceived;

/* Global structure to store mapping boundaries (min/max for each channel, in µs) */
typedef struct {
    uint32_t ch1_min;
    uint32_t ch1_max;
    uint32_t ch2_min;
    uint32_t ch2_max;
    uint32_t ch3_min;
    uint32_t ch3_max;
    uint32_t ch4_min;
    uint32_t ch4_max;
} RadioMapping_t;

/* Initialize boundaries to extremes */
static RadioMapping_t mappingBoundaries = {
    .ch1_min = 0xFFFFFFFF, .ch1_max = 0,
    .ch2_min = 0xFFFFFFFF, .ch2_max = 0,
    .ch3_min = 0xFFFFFFFF, .ch3_max = 0,
    .ch4_min = 0xFFFFFFFF, .ch4_max = 0
};
#define MIN_VALID_PULSE_US 100  // Only consider pulse widths >100 µs as valid

/* Global mode flag:
   mappingMode = 1: capture min/max boundaries (no servo output)
   bypassMode = 0: normal mode (compute percentage and output to servo)
*/
typedef enum {
    MAPPING_MODE,
    BYPASS_MODE,
    NUM_MODES // Keep track of the number of modes
} OperationMode;

static OperationMode currentMode = MAPPING_MODE;  // Start in mapping mode

/* External queue handle (make sure this is defined elsewhere) */
extern osMessageQueueId_t radioQueueHandle;

/* Simple float mapping function */
float map_float(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

/* Function to handle mapping mode */
void handleMappingMode(void) {
    if (radioDataReceived.ch1 < mappingBoundaries.ch1_min && radioDataReceived.ch1 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch1_min = radioDataReceived.ch1;
    if (radioDataReceived.ch1 > mappingBoundaries.ch1_max)
        mappingBoundaries.ch1_max = radioDataReceived.ch1;

    if (radioDataReceived.ch2 < mappingBoundaries.ch2_min && radioDataReceived.ch2 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch2_min = radioDataReceived.ch2;
    if (radioDataReceived.ch2 > mappingBoundaries.ch2_max)
        mappingBoundaries.ch2_max = radioDataReceived.ch2;

    if (radioDataReceived.ch3 < mappingBoundaries.ch3_min && radioDataReceived.ch3 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch3_min = radioDataReceived.ch3;
    if (radioDataReceived.ch3 > mappingBoundaries.ch3_max)
        mappingBoundaries.ch3_max = radioDataReceived.ch3;

    if (radioDataReceived.ch4 < mappingBoundaries.ch4_min && radioDataReceived.ch4 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch4_min = radioDataReceived.ch4;
    if (radioDataReceived.ch4 > mappingBoundaries.ch4_max)
        mappingBoundaries.ch4_max = radioDataReceived.ch4;
}

/* Function to handle normal mode (bypassMode) */
void handleBypassMode(void) {
    uint32_t pulseWidth[4] = {
        radioDataReceived.ch1,
        radioDataReceived.ch2,
        radioDataReceived.ch3,
        radioDataReceived.ch4
    };

    uint32_t min_val[4] = {
        mappingBoundaries.ch1_min,
        mappingBoundaries.ch2_min,
        mappingBoundaries.ch3_min,
        mappingBoundaries.ch4_min
    };

    uint32_t max_val[4] = {
        mappingBoundaries.ch1_max,
        mappingBoundaries.ch2_max,
        mappingBoundaries.ch3_max,
        mappingBoundaries.ch4_max
    };

    /* Avoid division by zero if boundaries are not properly set */
    for (int i = 0; i < 4; i++) {
        if (max_val[i] <= min_val[i])
            return;  // Invalid range

        /* Calculate percentage (0.0 to 1.0) for each channel */
        float percent = (float)(pulseWidth[i] - min_val[i]) / (float)(max_val[i] - min_val[i]);
        if (percent < 0.0F) percent = 0.0F;
        if (percent > 1.0F) percent = 1.0F;

        /* Map percentage to servo pulse width in ms.
           Desired servo range: 0.6 ms (0%) to 2.4 ms (100%)
        */
        float servoPulse_ms = map_float(percent, 0.0F, 1.0F, 0.6F, 2.4F);

        /* Convert servoPulse_ms to a timer compare value.
           (Assuming that your timer (htim4) is configured so that a full period equals 20ms,
            and the ARR is set such that 20ms corresponds to 59999 ticks.
            Adjust the scaling factor as needed.)
        */
        float compare_val = servoPulse_ms * 59999.0F / 20.0F;

        /* Set the compare value for the corresponding timer channel */
        switch (i) {
            case 0:
                __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, (long)compare_val);
                break;
            case 1:
                __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_2, (long)compare_val);
                break;
            case 2:
                __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_3, (long)compare_val);
                break;
            case 3:
                __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_4, (long)compare_val);
                break;
        }
    }
}

/* Main control function */
void control(void) {
    RadioData_t newRadioData;

    /* Attempt non-blocking receive from the radio queue */
    if (osMessageQueueGet(radioQueueHandle, &newRadioData, NULL, 0) == osOK) {
        radioDataReceived = newRadioData;
    }

    /* Handle the current mode */
    switch (currentMode) {
        case MAPPING_MODE:
            handleMappingMode();  // Update min/max boundaries
            break;
        case BYPASS_MODE:
            handleBypassMode();  // Calculate and output servo values
            break;
        default:
            // Handle any new modes that are added in the future
            break;
    }
}
