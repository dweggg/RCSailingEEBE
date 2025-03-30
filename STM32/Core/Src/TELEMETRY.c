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
extern osMessageQueueId_t telemetryQueueHandle;

AdcData_t    adcDataReceived;
ImuData_t    imuDataReceived;
RadioData_t  radioDataReceived;
ControlData_t controlDataReceived;

// DMA RX circular buffer
#define RX_BUFFER_SIZE 16
static char uartRxBuffer[RX_BUFFER_SIZE] = {0};

#define TX_BUFFER_SIZE 16
static char uartTxBuffer[TX_BUFFER_SIZE];  // TX buffer (larger size for safety)

/**
 * @brief Transmits a telemetry value with a given key.
 *
 * The message is formatted as "KEY:VALUE\r\n".
 */
static void telemetry_transmit(const char *key, float value) {
    snprintf(uartTxBuffer, sizeof(uartTxBuffer), "%s:%.2f\r\n", key, value);
    HAL_UART_Transmit(&huart1, (uint8_t *)uartTxBuffer, strlen(uartTxBuffer), 1);
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

// Define a sufficiently large temporary buffer for complete messages.
#define TEMP_BUFFER_SIZE 64

bool telemetry_receive(const char *key, float *value) {
    // Static variables to keep state across function calls
    static uint16_t last_read_index = 0;
    static char tempBuffer[TEMP_BUFFER_SIZE];
    static uint16_t tempIndex = 0;

    // Determine the current index in the DMA circular buffer.
    // RX_BUFFER_SIZE is defined in the file as 16.
    // __HAL_DMA_GET_COUNTER returns the number of bytes remaining.
    uint16_t dma_remaining = __HAL_DMA_GET_COUNTER(huart1.hdmarx);
    uint16_t current_index = RX_BUFFER_SIZE - dma_remaining;

    // Process all new characters in the circular buffer
    while (last_read_index != current_index) {
        char ch = uartRxBuffer[last_read_index];
        // Update the read pointer, wrapping around if necessary.
        last_read_index = (last_read_index + 1) % RX_BUFFER_SIZE;

        // Append the character to the temporary buffer if space is available.
        if (tempIndex < TEMP_BUFFER_SIZE - 1) {
            tempBuffer[tempIndex++] = ch;
        } else {
            // Overflow protection: reset temp buffer if it gets too full.
            tempIndex = 0;
        }

        // Check if the last two characters form the "\r\n" delimiter.
        if (tempIndex >= 2 &&
            tempBuffer[tempIndex - 2] == '\r' &&
            tempBuffer[tempIndex - 1] == '\n') {

            // Null-terminate the message (overwrite '\r' with '\0').
            tempBuffer[tempIndex - 2] = '\0';

            // Check if the message starts with the given key followed by a colon.
            size_t keyLen = strlen(key);
            if (strncmp(tempBuffer, key, keyLen) == 0 && tempBuffer[keyLen] == ':') {
                // Convert the string after the colon to a float.
                *value = (float)atof(&tempBuffer[keyLen + 1]);
                // Reset the temporary buffer for the next message.
                tempIndex = 0;
                return true;
            }
            // Message was complete but did not match the key.
            // Clear the temp buffer and continue processing.
            tempIndex = 0;
        }
    }

    // No complete message with the requested key was received.
    return false;
}

int telemetry_initialized = 0;

void telemetry(void) {
    if (!telemetry_initialized) {

    	// Start RX DMA (assumes this only needs to be done once)
    	telemetry_start_rx_dma();
    	telemetry_initialized = 1;
    }

	// Send a simple "OK" heartbeat
	snprintf(uartTxBuffer, sizeof(uartTxBuffer), "OK\r\n");
	HAL_UART_Transmit(&huart1, (uint8_t *)uartTxBuffer, strlen(uartTxBuffer), HAL_MAX_DELAY);

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
		telemetry_transmit("SPE", imuDataReceived.speed);
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
	    ControlData_t controlDataReceived;
	    osMessageQueueGet(controlQueueHandle, (void *)&controlDataReceived, NULL, osWaitForever);

	    telemetry_transmit("RUD", controlDataReceived.rudder);
	    telemetry_transmit("TWI", controlDataReceived.twist);
	    telemetry_transmit("TRI",  controlDataReceived.trim);
	    //telemetry_transmit("CEX", controlDataReceived.extra);
	}

    float modeValue = 0.0f;
    if (telemetry_receive("MOD", &modeValue)) {
        // Create a TelemetryData_t structure and assign the received value.
        TelemetryData_t telemetryData;
        telemetryData.mode = (ControlMode_t)(int)modeValue;

        // Send the telemetry data over the telemetry queue.
        osMessageQueuePut(telemetryQueueHandle, (void *)&telemetryData, 0, 0);
    }
}
