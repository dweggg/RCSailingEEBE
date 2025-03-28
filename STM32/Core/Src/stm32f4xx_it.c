/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32f4xx_it.c
  * @brief   Interrupt Service Routines.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32f4xx_it.h"
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "cmsis_os.h"
#include "CONTROL.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN TD */

/* USER CODE END TD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */
volatile unsigned long ulHighFrequencyTimerTicks = 0;
extern osMessageQueueId_t radioQueueHandle; // Declare the queue handle
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/* External variables --------------------------------------------------------*/
extern DMA_HandleTypeDef hdma_adc1;
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim11;
extern DMA_HandleTypeDef hdma_usart1_rx;
extern TIM_HandleTypeDef htim10;

/* USER CODE BEGIN EV */

/* USER CODE END EV */

/******************************************************************************/
/*           Cortex-M4 Processor Interruption and Exception Handlers          */
/******************************************************************************/
/**
  * @brief This function handles Non maskable interrupt.
  */
void NMI_Handler(void)
{
  /* USER CODE BEGIN NonMaskableInt_IRQn 0 */

  /* USER CODE END NonMaskableInt_IRQn 0 */
  /* USER CODE BEGIN NonMaskableInt_IRQn 1 */
   while (1)
  {
  }
  /* USER CODE END NonMaskableInt_IRQn 1 */
}

/**
  * @brief This function handles Hard fault interrupt.
  */
void HardFault_Handler(void)
{
  /* USER CODE BEGIN HardFault_IRQn 0 */

  /* USER CODE END HardFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_HardFault_IRQn 0 */
    /* USER CODE END W1_HardFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Memory management fault.
  */
void MemManage_Handler(void)
{
  /* USER CODE BEGIN MemoryManagement_IRQn 0 */

  /* USER CODE END MemoryManagement_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_MemoryManagement_IRQn 0 */
    /* USER CODE END W1_MemoryManagement_IRQn 0 */
  }
}

/**
  * @brief This function handles Pre-fetch fault, memory access fault.
  */
void BusFault_Handler(void)
{
  /* USER CODE BEGIN BusFault_IRQn 0 */

  /* USER CODE END BusFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_BusFault_IRQn 0 */
    /* USER CODE END W1_BusFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Undefined instruction or illegal state.
  */
void UsageFault_Handler(void)
{
  /* USER CODE BEGIN UsageFault_IRQn 0 */

  /* USER CODE END UsageFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_UsageFault_IRQn 0 */
    /* USER CODE END W1_UsageFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Debug monitor.
  */
void DebugMon_Handler(void)
{
  /* USER CODE BEGIN DebugMonitor_IRQn 0 */

  /* USER CODE END DebugMonitor_IRQn 0 */
  /* USER CODE BEGIN DebugMonitor_IRQn 1 */

  /* USER CODE END DebugMonitor_IRQn 1 */
}

/******************************************************************************/
/* STM32F4xx Peripheral Interrupt Handlers                                    */
/* Add here the Interrupt Handlers for the used peripherals.                  */
/* For the available peripheral interrupt handler names,                      */
/* please refer to the startup file (startup_stm32f4xx.s).                    */
/******************************************************************************/

/**
  * @brief This function handles TIM1 update interrupt and TIM10 global interrupt.
  */
void TIM1_UP_TIM10_IRQHandler(void)
{
  /* USER CODE BEGIN TIM1_UP_TIM10_IRQn 0 */

  /* USER CODE END TIM1_UP_TIM10_IRQn 0 */
  HAL_TIM_IRQHandler(&htim10);
  /* USER CODE BEGIN TIM1_UP_TIM10_IRQn 1 */

  /* USER CODE END TIM1_UP_TIM10_IRQn 1 */
}

/**
  * @brief This function handles TIM1 trigger and commutation interrupts and TIM11 global interrupt.
  */
void TIM1_TRG_COM_TIM11_IRQHandler(void)
{
  /* USER CODE BEGIN TIM1_TRG_COM_TIM11_IRQn 0 */

  /* USER CODE END TIM1_TRG_COM_TIM11_IRQn 0 */
  HAL_TIM_IRQHandler(&htim11);
  /* USER CODE BEGIN TIM1_TRG_COM_TIM11_IRQn 1 */
  ulHighFrequencyTimerTicks++;

  /* USER CODE END TIM1_TRG_COM_TIM11_IRQn 1 */
}

/**
  * @brief This function handles TIM3 global interrupt.
  */
void TIM3_IRQHandler(void)
{
  /* USER CODE BEGIN TIM3_IRQn 0 */

  /* USER CODE END TIM3_IRQn 0 */
  HAL_TIM_IRQHandler(&htim3);
  /* USER CODE BEGIN TIM3_IRQn 1 */

  /* USER CODE END TIM3_IRQn 1 */
}

/**
  * @brief This function handles DMA2 stream0 global interrupt.
  */
void DMA2_Stream0_IRQHandler(void)
{
  /* USER CODE BEGIN DMA2_Stream0_IRQn 0 */

  /* USER CODE END DMA2_Stream0_IRQn 0 */
  HAL_DMA_IRQHandler(&hdma_adc1);
  /* USER CODE BEGIN DMA2_Stream0_IRQn 1 */

  /* USER CODE END DMA2_Stream0_IRQn 1 */
}

/**
  * @brief This function handles DMA2 stream2 global interrupt.
  */
void DMA2_Stream2_IRQHandler(void)
{
  /* USER CODE BEGIN DMA2_Stream2_IRQn 0 */

  /* USER CODE END DMA2_Stream2_IRQn 0 */
  HAL_DMA_IRQHandler(&hdma_usart1_rx);
  /* USER CODE BEGIN DMA2_Stream2_IRQn 1 */

  /* USER CODE END DMA2_Stream2_IRQn 1 */
}

/* USER CODE BEGIN 1 */

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

/* USER CODE END 1 */
