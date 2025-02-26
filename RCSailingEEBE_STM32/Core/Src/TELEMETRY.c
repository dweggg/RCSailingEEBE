/*
 * TELEMETRY.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg
 */

#include "TELEMETRY.h"


#include "cmsis_os.h"
#include "ANALOG.h"
#include <stdio.h>
#include <string.h>
#include "usart.h"

extern osMessageQueueId_t adcQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

void telemetry(void) {
    char uartBuffer[128];  // Increased buffer size

    AdcData_t adcDataReceived;
    ImuData_t imuDataReceived;
    RadioData_t radioDataReceived;
    ControlData_t controlDataReceived;

    for (;;) {
        if (osMessageQueueGetCount(imuQueueHandle) > 0) {
			// Get ADC Data
        	osMessageQueueGet(adcQueueHandle, (void*)&adcDataReceived, NULL, osWaitForever);
            // Send ADC Data
            snprintf(uartBuffer, sizeof(uartBuffer), "DIR: %.2f\r\n", adcDataReceived.windDirection);
            HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
            snprintf(uartBuffer, sizeof(uartBuffer), "BAT: %.2f\r\n", adcDataReceived.batteryVoltage);
            HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
            snprintf(uartBuffer, sizeof(uartBuffer), "EX1: %.2f\r\n", adcDataReceived.extra1);
            HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
            snprintf(uartBuffer, sizeof(uartBuffer), "EX2: %.2f\r\n", adcDataReceived.extra2);
            HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
        }

        if (osMessageQueueGetCount(imuQueueHandle) > 0) {
			// Get IMU Data
			osMessageQueueGet(imuQueueHandle, (void*)&imuDataReceived, NULL, osWaitForever);
			// Send IMU Data
			snprintf(uartBuffer, sizeof(uartBuffer), "ROL: %.2f\r\n", imuDataReceived.roll);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "PIT: %.2f\r\n", imuDataReceived.pitch);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "YAW: %.2f\r\n", imuDataReceived.yaw);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);

			snprintf(uartBuffer, sizeof(uartBuffer), "ACX: %.2f\r\n", imuDataReceived.accelX);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "ACY: %.2f\r\n", imuDataReceived.accelY);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "ACZ: %.2f\r\n", imuDataReceived.accelZ);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);

			snprintf(uartBuffer, sizeof(uartBuffer), "GYX: %.2f\r\n", imuDataReceived.gyroX);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "GYY: %.2f\r\n", imuDataReceived.gyroY);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "GYZ: %.2f\r\n", imuDataReceived.gyroZ);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);

			snprintf(uartBuffer, sizeof(uartBuffer), "MGX: %.2f\r\n", imuDataReceived.magX);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "MGY: %.2f\r\n", imuDataReceived.magY);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "MGZ: %.2f\r\n", imuDataReceived.magZ);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
        }

        if (osMessageQueueGetCount(radioQueueHandle) > 0) {
			// Get Radio Data
			osMessageQueueGet(radioQueueHandle, (void*)&radioDataReceived, NULL, osWaitForever);
			// Send Radio Data
			snprintf(uartBuffer, sizeof(uartBuffer), "RW1: %.2f\r\n", (float)radioDataReceived.ch1);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "RW2: %.2f\r\n", (float)radioDataReceived.ch2);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "RW3: %.2f\r\n", (float)radioDataReceived.ch3);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "RW4: %.2f\r\n", (float)radioDataReceived.ch4);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);

        }

        if (osMessageQueueGetCount(controlQueueHandle)>0){

			// Get Radio Data
			osMessageQueueGet(controlQueueHandle, (void*)&controlDataReceived, NULL, osWaitForever);
			// Send Radio Data
			snprintf(uartBuffer, sizeof(uartBuffer), "CT1: %.2f\r\n", (float)controlDataReceived.ctrl1);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "CT2: %.2f\r\n", (float)controlDataReceived.ctrl2);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "CT3: %.2f\r\n", (float)controlDataReceived.ctrl3);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "CT4: %.2f\r\n", (float)controlDataReceived.ctrl4);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "CT5: %.2f\r\n", (float)controlDataReceived.ctrl5);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
			snprintf(uartBuffer, sizeof(uartBuffer), "CT6: %.2f\r\n", (float)controlDataReceived.ctrl6);
			HAL_UART_Transmit(&huart1, (uint8_t*)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);
        }
    }
}



