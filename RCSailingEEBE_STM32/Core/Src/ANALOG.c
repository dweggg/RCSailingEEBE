/*
 * ANALOG.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "ANALOG.h"
#include "adc.h"
#include "cmsis_os.h"

extern osMessageQueueId_t adcQueueHandle;
volatile uint16_t adc_raw_readings[4];

float windDirectionGain = 1.0f;
float windDirectionOffset = 0.0f;

float batteryVoltageGain = 1.0f;
float batteryVoltageOffset = 0.0f;

float extra1Gain = 1.0f;
float extra1Offset = 0.0f;

float extra2Gain = 1.0f;
float extra2Offset = 0.0f;

void adc_read(void) {
    // Start ADC conversion using DMA
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_raw_readings, 4);

    // Create a struct to hold the processed ADC data
    AdcData_t adcData;
    adcData.windDirection = ((float)adc_raw_readings[0] * windDirectionGain) - windDirectionOffset;
    adcData.batteryVoltage = ((float)adc_raw_readings[1] * batteryVoltageGain) - batteryVoltageOffset;
    adcData.extra1 = ((float)adc_raw_readings[2] * extra1Gain) - extra1Offset;
    adcData.extra2 = ((float)adc_raw_readings[3] * extra2Gain) - extra2Offset;

    // Send the struct to the ADC queue, overwriting previous value if full
    osMessageQueuePut(adcQueueHandle, &adcData, 0, 0);
}

