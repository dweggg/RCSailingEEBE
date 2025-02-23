/*
 * CONTROL.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "CONTROL.h"
#include "cmsis_os.h"
#include "ANALOG.h"  // Ensure this contains AdcData_t
#include <string.h>

extern osMessageQueueId_t adcQueueHandle;

// Buffer to store latest ADC data
volatile AdcData_t adcDataReceived;

void control(void) {
    while (1) {
        // Wait indefinitely for new ADC data
        osMessageQueueGet(adcQueueHandle, (void*)&adcDataReceived, NULL, osWaitForever);

        // Now, adcBuffer contains the latest ADC data from the queue
    }
}
