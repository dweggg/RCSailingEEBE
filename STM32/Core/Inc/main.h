/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define ANALOG1_Pin GPIO_PIN_1
#define ANALOG1_GPIO_Port GPIOA
#define ANALOG2_Pin GPIO_PIN_2
#define ANALOG2_GPIO_Port GPIOA
#define ANALOG3_Pin GPIO_PIN_3
#define ANALOG3_GPIO_Port GPIOA
#define ANALOG4_Pin GPIO_PIN_4
#define ANALOG4_GPIO_Port GPIOA
#define IN1_Pin GPIO_PIN_6
#define IN1_GPIO_Port GPIOA
#define IN2_Pin GPIO_PIN_7
#define IN2_GPIO_Port GPIOA
#define IN3_Pin GPIO_PIN_0
#define IN3_GPIO_Port GPIOB
#define IN4_Pin GPIO_PIN_1
#define IN4_GPIO_Port GPIOB
#define IMU_CLK_Pin GPIO_PIN_8
#define IMU_CLK_GPIO_Port GPIOA
#define TEL_TX_Pin GPIO_PIN_9
#define TEL_TX_GPIO_Port GPIOA
#define TEL_RX_Pin GPIO_PIN_10
#define TEL_RX_GPIO_Port GPIOA
#define IMU_SDA_Pin GPIO_PIN_4
#define IMU_SDA_GPIO_Port GPIOB
#define OUT1_Pin GPIO_PIN_6
#define OUT1_GPIO_Port GPIOB
#define OUT2_Pin GPIO_PIN_7
#define OUT2_GPIO_Port GPIOB
#define OUT3_Pin GPIO_PIN_8
#define OUT3_GPIO_Port GPIOB
#define OUT4_Pin GPIO_PIN_9
#define OUT4_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
