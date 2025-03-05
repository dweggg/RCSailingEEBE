/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
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
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "CONTROL.h"
#include "ANALOG.h"
#include "IMU.h"
#include "TELEMETRY.h"

#include "tim.h"
#include "stm32f4xx_it.h"
#include "queue.h"
#include "adc.h"
#include "i2c.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define CONTROL_DELAY 10
#define TELEMETRY_DELAY 500
#define IMU_DELAY 10
#define ADC_DELAY 10

#define INCLUDE_vTaskList               1

#ifdef __cplusplus
extern "C" {
#endif
__attribute__((used))
const int uxTopUsedPriority = configMAX_PRIORITIES - 1;
#ifdef __cplusplus
}
#endif

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */
uint32_t idle_dummy, control_dummy, telemetry_dummy, imu_dummy, adc_dummy;
/* USER CODE END Variables */
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for control_task */
osThreadId_t control_taskHandle;
const osThreadAttr_t control_task_attributes = {
  .name = "control_task",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityHigh,
};
/* Definitions for imu_read_task */
osThreadId_t imu_read_taskHandle;
const osThreadAttr_t imu_read_task_attributes = {
  .name = "imu_read_task",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for adc_read_task */
osThreadId_t adc_read_taskHandle;
const osThreadAttr_t adc_read_task_attributes = {
  .name = "adc_read_task",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for telemetry_task */
osThreadId_t telemetry_taskHandle;
const osThreadAttr_t telemetry_task_attributes = {
  .name = "telemetry_task",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for radioQueue */
osMessageQueueId_t radioQueueHandle;
const osMessageQueueAttr_t radioQueue_attributes = {
  .name = "radioQueue"
};
/* Definitions for adcQueue */
osMessageQueueId_t adcQueueHandle;
const osMessageQueueAttr_t adcQueue_attributes = {
  .name = "adcQueue"
};
/* Definitions for imuQueue */
osMessageQueueId_t imuQueueHandle;
const osMessageQueueAttr_t imuQueue_attributes = {
  .name = "imuQueue"
};
/* Definitions for telemetryQueue */
osMessageQueueId_t controlQueueHandle;
const osMessageQueueAttr_t controlQueue_attributes = {
  .name = "controlQueue"
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);
void _control_task(void *argument);
void _imu_read_task(void *argument);
void _adc_read_task(void *argument);
void _telemetry_task(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* Hook prototypes */
void configureTimerForRunTimeStats(void);
unsigned long getRunTimeCounterValue(void);

/* USER CODE BEGIN 1 */
/* Functions needed when configGENERATE_RUN_TIME_STATS is on */
__weak void configureTimerForRunTimeStats(void)
{
	HAL_TIM_Base_Start_IT(&htim11);
}

extern volatile unsigned long ulHighFrequencyTimerTicks;
__weak unsigned long getRunTimeCounterValue(void)
{
	return ulHighFrequencyTimerTicks;
}
/* USER CODE END 1 */

/* USER CODE BEGIN PREPOSTSLEEP */
__weak void PreSleepProcessing(uint32_t ulExpectedIdleTime)
{
/* place for user code */
}

__weak void PostSleepProcessing(uint32_t ulExpectedIdleTime)
{
/* place for user code */
}
/* USER CODE END PREPOSTSLEEP */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

	// Start all 4 input captures
	HAL_TIM_IC_Start_IT(&htim3, TIM_CHANNEL_1);
	HAL_TIM_IC_Start_IT(&htim3, TIM_CHANNEL_2);
	HAL_TIM_IC_Start_IT(&htim3, TIM_CHANNEL_3);
	HAL_TIM_IC_Start_IT(&htim3, TIM_CHANNEL_4);

	HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_2);
	HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_3);
	HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_4);
  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* creation of radioQueue */
  radioQueueHandle = osMessageQueueNew (1, sizeof(RadioData_t), &radioQueue_attributes);

  /* creation of adcQueue */
  adcQueueHandle = osMessageQueueNew (1, sizeof(AdcData_t), &adcQueue_attributes);

  /* creation of imuQueue */
  imuQueueHandle = osMessageQueueNew (1, sizeof(ImuData_t), &imuQueue_attributes);

  /* creation of telemetryQueue */
  controlQueueHandle = osMessageQueueNew (1, sizeof(ControlData_t), &controlQueue_attributes);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */

  // Allowing the kernel-aware debugger to get to know our queues
  vQueueAddToRegistry( radioQueueHandle, "radioQueue" );
  vQueueAddToRegistry( adcQueueHandle, "adcQueue" );
  vQueueAddToRegistry( imuQueueHandle, "imuQueue" );
  vQueueAddToRegistry( controlQueueHandle, "controlQueue" );
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of control_task */
  control_taskHandle = osThreadNew(_control_task, NULL, &control_task_attributes);

  /* creation of imu_read_task */
  imu_read_taskHandle = osThreadNew(_imu_read_task, NULL, &imu_read_task_attributes);

  /* creation of adc_read_task */
  adc_read_taskHandle = osThreadNew(_adc_read_task, NULL, &adc_read_task_attributes);

  /* creation of telemetry_task */
  telemetry_taskHandle = osThreadNew(_telemetry_task, NULL, &telemetry_task_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN StartDefaultTask */
  /* Infinite loop */
  for(;;)
  {
	idle_dummy++; // Keep incrementing the dummy variable
    osDelay(1); // A small delay to avoid task starvation
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header__control_task */
/**
* @brief Function implementing the control_task thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header__control_task */
void _control_task(void *argument)
{
  /* USER CODE BEGIN _control_task */
  for(;;)
  {
	control_dummy++;
    control(); // Execute control function
    osDelay(CONTROL_DELAY);
  }
  /* USER CODE END _control_task */
}

/* USER CODE BEGIN Header__imu_read_task */
/**
* @brief Function implementing the imu_read_task thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header__imu_read_task */
void _imu_read_task(void *argument)
{
  /* USER CODE BEGIN _imu_read_task */
  for(;;)
  {
	imu_dummy++;
    imu_read(); // Execute imu read function
    osDelay(IMU_DELAY);
  }
  /* USER CODE END _imu_read_task */
}

/* USER CODE BEGIN Header__adc_read_task */
/**
* @brief Function implementing the adc_read_task thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header__adc_read_task */
void _adc_read_task(void *argument)
{
  /* USER CODE BEGIN _adc_read_task */
  for(;;)
  {
	adc_dummy++;
    adc_read(); // Execute ADC read function
    osDelay(ADC_DELAY);
  }
  /* USER CODE END _adc_read_task */
}

/* USER CODE BEGIN Header__telemetry_task */
/**
* @brief Function implementing the telemetry_task thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header__telemetry_task */
void _telemetry_task(void *argument)
{
  /* USER CODE BEGIN _telemetry_task */
  for(;;)
  {
	telemetry_dummy++;
    telemetry(); // Execute telemetry function
    osDelay(TELEMETRY_DELAY);
  }
  /* USER CODE END _telemetry_task */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

