/*
 * TELEMETRY.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg (refactored by yours truly)
 */

#include "TELEMETRY.h"
#include "cmsis_os.h"
#include "ANALOG.h"
#include "IMU.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "usart.h"

extern osMessageQueueId_t adcQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

AdcData_t    adcDataReceived;
ImuData_t    imuDataReceived;
RadioData_t  radioDataReceived;
ControlData_t controlDataReceived;

// DMA RX circular buffer
#define RX_BUFFER_SIZE 16
static char uartRxBuffer[RX_BUFFER_SIZE] = {0};
float modValue = 0.0f;

/**
 * @brief Transmits a telemetry value with a given key.
 *
 * The message is formatted as "KEY:VALUE\r\n".
 */
static void telemetry_transmit(const char *key, float value) {
    char buffer[32];
    snprintf(buffer, sizeof(buffer), "%s:%.2f\r\n", key, value);
    HAL_UART_Transmit(&huart1, (uint8_t *)buffer, strlen(buffer), HAL_MAX_DELAY);
}

/**
 * @brief Starts UART RX in DMA mode using a circular buffer.
 *
 * Only the pointer to the buffer is passed so that the DMA hardware
 * writes directly into uartRxBuffer.
 */
static void telemetry_start_rx_dma(void) {
    HAL_UART_Receive_DMA(&huart1, (uint8_t *)uartRxBuffer, RX_BUFFER_SIZE);
}

#define TEMP_BUFFER_SIZE RX_BUFFER_SIZE

static void copy_circular_buffer(char *dest, const char *src, int start, int count) {
    // Copy from start index to the end of the buffer
    int firstPart = (start + count > RX_BUFFER_SIZE) ? RX_BUFFER_SIZE - start : count;
    memcpy(dest, &src[start], firstPart);

    // If the data wraps around, copy the rest from the beginning
    if (count > firstPart) {
        memcpy(dest + firstPart, src, count - firstPart);
    }
    dest[count] = '\0'; // Ensure null termination
}

static bool telemetry_receive(const char *key, float *value, int dmaHead, int dmaTail) {
    // Calculate the length of the data currently in the buffer.
    int dataLength;
    if (dmaHead >= dmaTail) {
        dataLength = dmaHead - dmaTail;
    } else {
        dataLength = RX_BUFFER_SIZE - dmaTail + dmaHead;
    }

    char tempBuffer[TEMP_BUFFER_SIZE + 1];
    copy_circular_buffer(tempBuffer, uartRxBuffer, dmaTail, dataLength);

    char *start = strstr(tempBuffer, key);
    if (start) {
        char *colon = strchr(start, ':');
        if (colon) {
            char *end = strstr(colon, "\r\n");
            if (end) {
                *end = '\0';
                *value = (float)atof(colon + 1);
                // Optionally adjust dmaTail based on how many bytes were processed
                return true;
            }
        }
    }
    return false;
}


void telemetry(void) {
    char uartBuffer[16];  // TX buffer (larger size for safety)

    // Start RX DMA (assumes this only needs to be done once)
    telemetry_start_rx_dma();

    for (;;) {
        // Send a simple "OK" heartbeat
        snprintf(uartBuffer, sizeof(uartBuffer), "OK\r\n");
        HAL_UART_Transmit(&huart1, (uint8_t *)uartBuffer, strlen(uartBuffer), HAL_MAX_DELAY);

        // Transmit ADC data if available.
        if (osMessageQueueGetCount(adcQueueHandle) > 0) {
            osMessageQueueGet(adcQueueHandle, (void *)&adcDataReceived, NULL, osWaitForever);
            telemetry_transmit("DIR", adcDataReceived.windDirection);
            telemetry_transmit("BAT", adcDataReceived.batteryVoltage);
            telemetry_transmit("EX1", adcDataReceived.extra1);
            telemetry_transmit("EX2", adcDataReceived.extra2);
        }

        // Transmit IMU data if available and initialized.
        if (osMessageQueueGetCount(imuQueueHandle) > 0 && is_imu_initialized()) {
            osMessageQueueGet(imuQueueHandle, (void *)&imuDataReceived, NULL, osWaitForever);
            telemetry_transmit("ROL", imuDataReceived.roll);
            telemetry_transmit("PIT", imuDataReceived.pitch);
            telemetry_transmit("YAW", imuDataReceived.yaw);
            telemetry_transmit("ACX", imuDataReceived.accelX);
            telemetry_transmit("ACY", imuDataReceived.accelY);
            telemetry_transmit("ACZ", imuDataReceived.accelZ);
            telemetry_transmit("GYX", imuDataReceived.gyroX);
            telemetry_transmit("GYY", imuDataReceived.gyroY);
            telemetry_transmit("GYZ", imuDataReceived.gyroZ);
            telemetry_transmit("MGX", imuDataReceived.magX);
            telemetry_transmit("MGY", imuDataReceived.magY);
            telemetry_transmit("MGZ", imuDataReceived.magZ);
        }

        // Transmit Radio data if available.
        if (osMessageQueueGetCount(radioQueueHandle) > 0) {
            osMessageQueueGet(radioQueueHandle, (void *)&radioDataReceived, NULL, osWaitForever);
            telemetry_transmit("RW1", (float)radioDataReceived.ch1);
            telemetry_transmit("RW2", (float)radioDataReceived.ch2);
            telemetry_transmit("RW3", (float)radioDataReceived.ch3);
            telemetry_transmit("RW4", (float)radioDataReceived.ch4);
        }

        // Transmit Control data if available.
        if (osMessageQueueGetCount(controlQueueHandle) > 0) {
            osMessageQueueGet(controlQueueHandle, (void *)&controlDataReceived, NULL, osWaitForever);
            telemetry_transmit("CT1", (float)controlDataReceived.ctrl1);
            telemetry_transmit("CT2", (float)controlDataReceived.ctrl2);
            telemetry_transmit("CT3", (float)controlDataReceived.ctrl3);
            telemetry_transmit("CT4", (float)controlDataReceived.ctrl4);
            telemetry_transmit("CT5", (float)controlDataReceived.ctrl5);
            telemetry_transmit("CT6", (float)controlDataReceived.ctrl6);
        }

        // Example: receive a variable (e.g., "MOD") from the circular DMA buffer.
        {
            if (telemetry_receive("MOD", &modValue)) {
            }
        }

    }
}
