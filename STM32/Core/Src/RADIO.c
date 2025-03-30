/*
 * RADIO.c
 *
 *  Created on: Mar 30, 2025
 *      Author: dweggg
 */


// radio.c
#include "RADIO.h"
//#include "stm32f4xx_hal.h"
#include "tim.h"
#include "cmsis_os.h"

#define MIN_VALID_PULSE_US 100

// Initialize raw radio data.
RadioData_t radioDataSent = {0};

// Initialize calibration boundaries to extreme values.
RadioCalibration_t radioCalibration = {
    .ch1_min = 0xFFFFFFFF, .ch1_max = 0,
    .ch2_min = 0xFFFFFFFF, .ch2_max = 0,
    .ch3_min = 0xFFFFFFFF, .ch3_max = 0,
    .ch4_min = 0xFFFFFFFF, .ch4_max = 0
};

// Updates calibration boundaries for each channel.
// In Calibration Mode, this function should be called repeatedly.
void update_radio_calibration(void) {
    if (radioDataSent.ch1 > MIN_VALID_PULSE_US) {
        if (radioDataSent.ch1 < radioCalibration.ch1_min)
            radioCalibration.ch1_min = radioDataSent.ch1;
        if (radioDataSent.ch1 > radioCalibration.ch1_max)
            radioCalibration.ch1_max = radioDataSent.ch1;
    }
    if (radioDataSent.ch2 > MIN_VALID_PULSE_US) {
        if (radioDataSent.ch2 < radioCalibration.ch2_min)
            radioCalibration.ch2_min = radioDataSent.ch2;
        if (radioDataSent.ch2 > radioCalibration.ch2_max)
            radioCalibration.ch2_max = radioDataSent.ch2;
    }
    if (radioDataSent.ch3 > MIN_VALID_PULSE_US) {
        if (radioDataSent.ch3 < radioCalibration.ch3_min)
            radioCalibration.ch3_min = radioDataSent.ch3;
        if (radioDataSent.ch3 > radioCalibration.ch3_max)
            radioCalibration.ch3_max = radioDataSent.ch3;
    }
    if (radioDataSent.ch4 > MIN_VALID_PULSE_US) {
        if (radioDataSent.ch4 < radioCalibration.ch4_min)
            radioCalibration.ch4_min = radioDataSent.ch4;
        if (radioDataSent.ch4 > radioCalibration.ch4_max)
            radioCalibration.ch4_max = radioDataSent.ch4;
    }
}

// Helper function to map a raw channel value to 0.0–1.0.
static float normalize(uint32_t value, uint32_t min, uint32_t max) {
    if (max <= min) return 0.0F;
    return ((float)(value - min)) / (max - min);
}

// Map a normalized radio value to a mechanical angle.
float map_radio(float radio_val, float min, float max) {
    return radio_val * (max - min) + min;
}

float get_radio_ch1(void) {
    return normalize(radioDataSent.ch1, radioCalibration.ch1_min, radioCalibration.ch1_max);
}
float get_radio_ch2(void) {
    return normalize(radioDataSent.ch2, radioCalibration.ch2_min, radioCalibration.ch2_max);
}
float get_radio_ch3(void) {
    return normalize(radioDataSent.ch3, radioCalibration.ch3_min, radioCalibration.ch3_max);
}
float get_radio_ch4(void) {
    return normalize(radioDataSent.ch4, radioCalibration.ch4_min, radioCalibration.ch4_max);
}

// Timer callback for radio capture
extern osMessageQueueId_t radioQueueHandle; // Declare the queue handle

/* Global variables for channel 1 */
volatile uint8_t ic1_rising = 1;  // 1: next capture is rising edge; 0: falling edge expected
volatile int16_t ic1_rising_val = 0;
volatile int16_t pulseWidth_CH1 = 0;

/* Global variables for channel 2 */
volatile uint8_t ic2_rising = 1;
volatile int16_t ic2_rising_val = 0;
volatile int16_t pulseWidth_CH2 = 0;

/* Global variables for channel 3 */
volatile uint8_t ic3_rising = 1;
volatile int16_t ic3_rising_val = 0;
volatile int16_t pulseWidth_CH3 = 0;

/* Global variables for channel 4 */
volatile uint8_t ic4_rising = 1;
volatile int16_t ic4_rising_val = 0;
volatile int16_t pulseWidth_CH4 = 0;


/* Helper function to send updated data to the queue */
static void SendRadioData(void)
{
    RadioData_t radioData;
    radioData.ch1 = pulseWidth_CH1;
    radioData.ch2 = pulseWidth_CH2;
    radioData.ch3 = pulseWidth_CH3;
    radioData.ch4 = pulseWidth_CH4;
    /* Non-blocking put into the queue */
    osMessageQueuePut(radioQueueHandle, &radioData, 0, 0);
}

/* Input capture callback handling all four channels */
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM3)
    {
        if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)
        {
            if (ic1_rising)
            {
                /* Capture rising edge time for CH1 */
                ic1_rising_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
                ic1_rising = 0;
                /* Switch polarity to falling edge */
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_FALLING);
            }
            else
            {
                /* Capture falling edge time for CH1 */
                int16_t falling_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
                if (falling_val >= ic1_rising_val)
                    pulseWidth_CH1 = falling_val - ic1_rising_val;
                else
                    pulseWidth_CH1 = (htim->Init.Period - ic1_rising_val) + falling_val + 1;
                ic1_rising = 1;
                /* Switch back to rising edge capture */
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_RISING);
                /* Send updated data */
                SendRadioData();
            }
        }
        else if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2)
        {
            if (ic2_rising)
            {
                /* Capture rising edge time for CH2 */
                ic2_rising_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_2);
                ic2_rising = 0;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_2, TIM_INPUTCHANNELPOLARITY_FALLING);
            }
            else
            {
                int16_t falling_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_2);
                if (falling_val >= ic2_rising_val)
                    pulseWidth_CH2 = falling_val - ic2_rising_val;
                else
                    pulseWidth_CH2 = (htim->Init.Period - ic2_rising_val) + falling_val + 1;
                ic2_rising = 1;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_2, TIM_INPUTCHANNELPOLARITY_RISING);
                SendRadioData();
            }
        }
        else if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_3)
        {
            if (ic3_rising)
            {
                /* Capture rising edge time for CH3 */
                ic3_rising_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_3);
                ic3_rising = 0;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_3, TIM_INPUTCHANNELPOLARITY_FALLING);
            }
            else
            {
                int16_t falling_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_3);
                if (falling_val >= ic3_rising_val)
                    pulseWidth_CH3 = falling_val - ic3_rising_val;
                else
                    pulseWidth_CH3 = (htim->Init.Period - ic3_rising_val) + falling_val + 1;
                ic3_rising = 1;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_3, TIM_INPUTCHANNELPOLARITY_RISING);
                SendRadioData();
            }
        }
        else if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_4)
        {
            if (ic4_rising)
            {
                /* Capture rising edge time for CH4 */
                ic4_rising_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_4);
                ic4_rising = 0;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_4, TIM_INPUTCHANNELPOLARITY_FALLING);
            }
            else
            {
                int16_t falling_val = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_4);
                if (falling_val >= ic4_rising_val)
                    pulseWidth_CH4 = falling_val - ic4_rising_val;
                else
                    pulseWidth_CH4 = (htim->Init.Period - ic4_rising_val) + falling_val + 1;
                ic4_rising = 1;
                __HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_4, TIM_INPUTCHANNELPOLARITY_RISING);
                SendRadioData();
            }
        }
    }
}
