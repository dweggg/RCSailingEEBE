/*
 * ANALOG.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "ANALOG.h"
#include "CONTROL.h"
#include "adc.h"
#include "cmsis_os.h"

extern osMessageQueueId_t adcQueueHandle;
volatile uint16_t adc_raw_readings[4];

float windDirectionGain = 1.0f;
float windDirectionOffset = 0.0f;

float batteryVoltageGain = 0.00355F; //1.0F/((68.0F/(220.0F+68.0F)) * (4096.0F/3.3F)) gives 0.034 aprox and its a bit more
float batteryVoltageOffset = 0.0f;

float extra1Gain = 1.0f;
float extra1Offset = 0.0f;

float extra2Gain = 1.0f;
float extra2Offset = 0.0f;
AdcData_t adcDataSent;

float windDirection = 0.0F, batteryVoltage = 0.0F, extra1 = 0.0F, extra2 = 0.0F;

float alphaVoltage = 0.1F;

void adc_read(void) {
    // Start ADC conversion using DMA
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_raw_readings, 4);

    // Create a struct to hold the processed ADC data
    windDirection = ((float)adc_raw_readings[0] * windDirectionGain) - windDirectionOffset;
    batteryVoltage = ((float)adc_raw_readings[1] * batteryVoltageGain) - batteryVoltageOffset;
    extra1 = ((float)adc_raw_readings[2] * extra1Gain) - extra1Offset;
    extra2 = ((float)adc_raw_readings[3] * extra2Gain) - extra2Offset;

    adcDataSent.windDirection = windDirection;
    adcDataSent.batteryVoltage = low_pass_filter(batteryVoltage, adcDataSent.batteryVoltage, alphaVoltage);
    adcDataSent.extra1 = extra1;
    adcDataSent.extra2 = extra2;

    // Send the struct to the ADC queue, overwriting previous value if full
    osMessageQueuePut(adcQueueHandle, &adcDataSent, 0, 0);
}

