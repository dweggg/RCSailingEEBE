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

// Queue externs
extern osMessageQueueId_t adcQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t controlQueueHandle;
extern osMessageQueueId_t telemetryQueueHandle;

// Data structures for incoming messages
AdcData_t    adcDataReceived;
ImuData_t    imuDataReceived;
RadioData_t  radioDataReceived;
ControlData_t controlDataReceived;

// DMA RX circular buffer
#define RX_BUFFER_SIZE 16
static char uartRxBuffer[RX_BUFFER_SIZE] = {0};

#define TX_BUFFER_SIZE 16
static char uartTxBuffer[TX_BUFFER_SIZE];  // TX buffer (larger size for safety)

// Define prescaler values for each telemetry group.
// Adjust these values as needed.
#define ADC_PRESCALER      5
#define IMU_PRESCALER      1
#define RADIO_PRESCALER    2
#define CONTROL_PRESCALER  2
#define CPU_PRESCALER      5

/**
 * @brief Transmits a telemetry value with a given key.
 *
 * The message is formatted as "KEY:VALUE\r\n".
 */
static void telemetry_transmit(const char *key, float value) {
    snprintf(uartTxBuffer, sizeof(uartTxBuffer), "%s:%.2f\r\n", key, value);
    HAL_UART_Transmit(&huart1, (uint8_t *)uartTxBuffer, strlen(uartTxBuffer), 10);
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

// Temporary buffer for complete messages
#define TEMP_BUFFER_SIZE 64

TelemetryData_t telemetryData = {
    .mode = MODE_DIRECT_INPUT,
    .rudder_servo_angle = 0.0f,
    .trim_servo_angle = 0.0f,
    .twist_servo_angle = 0.0f,
    .extra_servo_angle = 0.0f,

    .Kp_roll = 1.0f,
    .Ki_roll = 0.1f,
    .Kp_yaw  = 1.0f,
    .Ki_yaw  = 1.0f
};

bool telemetry_receive(const char *key, float *value) {
    static uint16_t last_read_index = 0;
    static char tempBuffer[TEMP_BUFFER_SIZE];
    static uint16_t tempIndex = 0;

    // Get current DMA index (number of bytes that have been transferred)
    uint16_t dma_remaining = __HAL_DMA_GET_COUNTER(huart1.hdmarx);
    uint16_t current_index = RX_BUFFER_SIZE - dma_remaining;

    // Process new characters in the circular buffer
    while (last_read_index != current_index) {
        char ch = uartRxBuffer[last_read_index];
        last_read_index = (last_read_index + 1) % RX_BUFFER_SIZE;

        if (tempIndex < TEMP_BUFFER_SIZE - 1) {
            tempBuffer[tempIndex++] = ch;
        } else {
            // Overflow protection: reset temp buffer if it gets too full.
            tempIndex = 0;
        }

        // Check for "\r\n" delimiter signaling end of message.
        if (tempIndex >= 2 &&
            tempBuffer[tempIndex - 2] == '\r' &&
            tempBuffer[tempIndex - 1] == '\n') {

            // Null-terminate the message (overwrite '\r' with '\0').
            tempBuffer[tempIndex - 2] = '\0';

            size_t keyLen = strlen(key);
            if (strncmp(tempBuffer, key, keyLen) == 0 && tempBuffer[keyLen] == ':') {
                *value = (float)atof(&tempBuffer[keyLen + 1]);
                tempIndex = 0;
                return true;
            }
            // Clear the buffer if the key did not match.
            tempIndex = 0;
        }
    }
    return false;
}

int telemetry_initialized = 0;

#define STATS_BUFFER_SIZE 512
static char statsBuffer[STATS_BUFFER_SIZE];

void telemetry(void) {
    // Initialize DMA only once.
    if (!telemetry_initialized) {
        telemetry_start_rx_dma();
        telemetry_initialized = 1;
    }

    // Transmit heartbeat.
    snprintf(uartTxBuffer, sizeof(uartTxBuffer), "OK\r\n");
    HAL_UART_Transmit(&huart1, (uint8_t *)uartTxBuffer, strlen(uartTxBuffer), HAL_MAX_DELAY);

    // Static prescaler counters for each telemetry group.
    static int adc_count = 0;
    static int imu_count = 0;
    static int radio_count = 0;
    static int control_count = 0;
    static int cpu_count = 0;

    // ADC telemetry group
    adc_count++;
    if (adc_count >= ADC_PRESCALER) {
        adc_count = 0;
        if (osMessageQueueGetCount(adcQueueHandle) > 0) {
            osMessageQueueGet(adcQueueHandle, (void *)&adcDataReceived, NULL, osWaitForever);
            telemetry_transmit("DIR", adcDataReceived.windDirection);
            telemetry_transmit("BAT", adcDataReceived.batteryVoltage);
            telemetry_transmit("EX1", adcDataReceived.extra1);
            telemetry_transmit("EX2", adcDataReceived.extra2);
        }
    }

    // IMU telemetry group (check initialization first)
    imu_count++;
    if (imu_count >= IMU_PRESCALER) {
        imu_count = 0;
        if (osMessageQueueGetCount(imuQueueHandle) > 0) {
            osMessageQueueGet(imuQueueHandle, (void *)&imuDataReceived, NULL, osWaitForever);
            telemetry_transmit("ROL", imuDataReceived.roll);
            telemetry_transmit("PIT", imuDataReceived.pitch);
            telemetry_transmit("YAW", imuDataReceived.yaw);
            telemetry_transmit("ACX", imuDataReceived.accelX);
            telemetry_transmit("ACY", imuDataReceived.accelY);
            telemetry_transmit("ACZ", imuDataReceived.accelZ);
//            telemetry_transmit("GYX", imuDataReceived.gyroX);
//            telemetry_transmit("GYY", imuDataReceived.gyroY);
//            telemetry_transmit("GYZ", imuDataReceived.gyroZ);
//            telemetry_transmit("MGX", imuDataReceived.magX);
//            telemetry_transmit("MGY", imuDataReceived.magY);
//            telemetry_transmit("MGZ", imuDataReceived.magZ);
            telemetry_transmit("SPE", imuDataReceived.speed);
        }
    }

    // Radio telemetry group
    radio_count++;
    if (radio_count >= RADIO_PRESCALER) {
        radio_count = 0;
        if (osMessageQueueGetCount(radioQueueHandle) > 0) {
            osMessageQueueGet(radioQueueHandle, (void *)&radioDataReceived, NULL, osWaitForever);
            telemetry_transmit("RW1", (float)radioDataReceived.ch1);
            telemetry_transmit("RW2", (float)radioDataReceived.ch2);
            telemetry_transmit("RW3", (float)radioDataReceived.ch3);
            telemetry_transmit("RW4", (float)radioDataReceived.ch4);
        }
    }

    // Control telemetry group
    control_count++;
    if (control_count >= CONTROL_PRESCALER) {
        control_count = 0;
        if (osMessageQueueGetCount(controlQueueHandle) > 0) {
            osMessageQueueGet(controlQueueHandle, (void *)&controlDataReceived, NULL, osWaitForever);
            telemetry_transmit("RUD", controlDataReceived.rudder);
            telemetry_transmit("TWI", controlDataReceived.twist);
            telemetry_transmit("TRI", controlDataReceived.trim);
            // telemetry_transmit("CEX", controlDataReceived.extra);
        }
    }

    // CPU usage telemetry group
    cpu_count++;
    if (cpu_count >= CPU_PRESCALER) {
        cpu_count = 0;
        vTaskGetRunTimeStats(statsBuffer);

        // Parse statsBuffer to locate the Idle task's execution time.
        char *idleTaskEntry = strstr(statsBuffer, "IDLE");
        if (idleTaskEntry != NULL) {
            unsigned long idleTime = 0;
            sscanf(idleTaskEntry, "IDLE %lu", &idleTime);

            // Calculate total runtime by summing each task's time.
            unsigned long totalTime = 0;
            char *line = strtok(statsBuffer, "\n");
            while (line != NULL) {
                unsigned long taskTime = 0;
                sscanf(line, "%*s %lu", &taskTime);
                totalTime += taskTime;
                line = strtok(NULL, "\n");
            }
            if (totalTime > 0) {
                float idlePercentage = (idleTime * 100.0f) / totalTime;
                float cpuUsage = 100.0f - idlePercentage;
                telemetry_transmit("CPU", cpuUsage);
            }
        }
    }


    float value = 0.0f;

    // Process any received mode change.
    if (telemetry_receive("MOD", &value)) {
        telemetryData.mode = (ControlMode_t)(int)value;
    }
    if (telemetry_receive("SRU", &value)) {
        telemetryData.rudder_servo_angle = value;
    }
    if (telemetry_receive("STR", &value)) {
        telemetryData.trim_servo_angle = value;
    }
    if (telemetry_receive("STW", &value)) {
        telemetryData.twist_servo_angle = value;
    }
    if (telemetry_receive("SEX", &value)) {
        telemetryData.extra_servo_angle = value;
    }
    if (telemetry_receive("KPR", &value)) {
        telemetryData.Kp_roll = value;
    }
    if (telemetry_receive("KIR", &value)) {
        telemetryData.Ki_roll = value;
    }
    if (telemetry_receive("KPY", &value)) {
        telemetryData.Kp_yaw = value;
    }
    if (telemetry_receive("KIY", &value)) {
        telemetryData.Ki_yaw = value;
    }

    // Send the updated telemetry data to the queue
    osMessageQueuePut(telemetryQueueHandle, (void *)&telemetryData, 0, 0);
}
