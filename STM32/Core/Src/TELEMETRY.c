/*
 * TELEMETRY.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg (refactored)
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
AdcData_t     adcDataReceived;
ImuData_t     imuDataReceived;
RadioData_t   radioDataReceived;
ControlData_t controlDataReceived;

// DMA RX circular buffer
#define RX_BUFFER_SIZE 32
static char uartRxBuffer[RX_BUFFER_SIZE] = {0};

#define TX_BUFFER_SIZE 32
static char uartTxBuffer[TX_BUFFER_SIZE];  // TX buffer

#define TEMP_BUFFER_SIZE 64
static char tempBuffer[TEMP_BUFFER_SIZE];
static uint16_t tempIndex = 0;
static uint16_t last_read_index = 0;

// Prescalers
#define ADC_PRESCALER      5
#define IMU_PRESCALER      1
#define RADIO_PRESCALER    2
#define CONTROL_PRESCALER  2
#define CPU_PRESCALER      5

TelemetryData_t telemetryData = {
    .mode = MODE_DIRECT_INPUT,
    .rudder_servo_angle = 0.0f,
    .trim_servo_angle   = 0.0f,
    .twist_servo_angle  = 0.0f,
    .extra_servo_angle  = 0.0f,

    .Kp_roll = 1.0f,
    .Ki_roll = 0.1f,
    .Kp_yaw  = 1.0f,
    .Ki_yaw  = 1.0f
};

static int telemetry_initialized = 0;
static char statsBuffer[512];

static void telemetry_transmit(const char *key, float value) {
    snprintf(uartTxBuffer, sizeof(uartTxBuffer), "%s:%.2f\r\n", key, value);
    HAL_UART_Transmit(&huart1, (uint8_t *)uartTxBuffer, strlen(uartTxBuffer), 10);
}

static void telemetry_start_rx_dma(void) {
    HAL_UART_Receive_DMA(&huart1, (uint8_t *)uartRxBuffer, RX_BUFFER_SIZE);
}

void telemetry(void) {
    if (!telemetry_initialized) {
        telemetry_start_rx_dma();
        telemetry_initialized = 1;
    }

    // Heartbeat
    HAL_UART_Transmit(&huart1, (uint8_t *)"OK\r\n", 4, HAL_MAX_DELAY);

    // Prescaler counters
    static int adc_count = 0, imu_count = 0, radio_count = 0;
    static int control_count = 0, cpu_count = 0;

    // ADC group
    if (++adc_count >= ADC_PRESCALER) {
        adc_count = 0;
        if (osMessageQueueGetCount(adcQueueHandle) > 0) {
            osMessageQueueGet(adcQueueHandle, &adcDataReceived, NULL, osWaitForever);
            telemetry_transmit("DIR", adcDataReceived.windDirection);
            telemetry_transmit("BAT", adcDataReceived.batteryVoltage);
            telemetry_transmit("EX1", adcDataReceived.extra1);
            telemetry_transmit("EX2", adcDataReceived.extra2);
        }
    }

    // IMU group
    if (++imu_count >= IMU_PRESCALER) {
        imu_count = 0;
        if (osMessageQueueGetCount(imuQueueHandle) > 0) {
            osMessageQueueGet(imuQueueHandle, &imuDataReceived, NULL, osWaitForever);
            telemetry_transmit("ROL", imuDataReceived.roll);
            telemetry_transmit("PIT", imuDataReceived.pitch);
            telemetry_transmit("YAW", imuDataReceived.yaw);
            telemetry_transmit("ACX", imuDataReceived.accelX);
            telemetry_transmit("ACY", imuDataReceived.accelY);
            telemetry_transmit("ACZ", imuDataReceived.accelZ);
			telemetry_transmit("GYX", imuDataReceived.gyroX);
			telemetry_transmit("GYY", imuDataReceived.gyroY);
			telemetry_transmit("GYZ", imuDataReceived.gyroZ);
//            telemetry_transmit("MGX", imuDataReceived.magX);
//            telemetry_transmit("MGY", imuDataReceived.magY);
//            telemetry_transmit("MGZ", imuDataReceived.magZ);
            telemetry_transmit("SPE", imuDataReceived.speed);
        }
    }

    // Radio group
    if (++radio_count >= RADIO_PRESCALER) {
        radio_count = 0;
        if (osMessageQueueGetCount(radioQueueHandle) > 0) {
            osMessageQueueGet(radioQueueHandle, &radioDataReceived, NULL, osWaitForever);
            telemetry_transmit("RW1", (float)radioDataReceived.ch1);
            telemetry_transmit("RW2", (float)radioDataReceived.ch2);
            telemetry_transmit("RW3", (float)radioDataReceived.ch3);
            telemetry_transmit("RW4", (float)radioDataReceived.ch4);
        }
    }

    // Control group
    if (++control_count >= CONTROL_PRESCALER) {
        control_count = 0;
        if (osMessageQueueGetCount(controlQueueHandle) > 0) {
            osMessageQueueGet(controlQueueHandle, &controlDataReceived, NULL, osWaitForever);
            telemetry_transmit("RUD", controlDataReceived.rudder);
            telemetry_transmit("TWI", controlDataReceived.twist);
            telemetry_transmit("TRI", controlDataReceived.trim);
//            telemetry_transmit("CEX", controlDataReceived.extra);
        }
    }

    // CPU usage
    if (++cpu_count >= CPU_PRESCALER) {
        cpu_count = 0;
        vTaskGetRunTimeStats(statsBuffer);
        char *idleEntry = strstr(statsBuffer, "IDLE");
        if (idleEntry) {
            unsigned long idleTime = 0, totalTime = 0;
            sscanf(idleEntry, "IDLE %lu", &idleTime);
            char *line = strtok(statsBuffer, "\n");
            while (line) {
                unsigned long t = 0;
                sscanf(line, "%*s %lu", &t);
                totalTime += t;
                line = strtok(NULL, "\n");
            }
            if (totalTime > 0) {
                float cpuUsage = 100.0f - ((idleTime * 100.0f) / totalTime);
                telemetry_transmit("CPU", cpuUsage);
            }
        }
    }

    // --- Single-pass parsing of incoming commands ---
    {
        uint16_t dma_remaining = __HAL_DMA_GET_COUNTER(huart1.hdmarx);
        uint16_t current_index = RX_BUFFER_SIZE - dma_remaining;
        while (last_read_index != current_index) {
            char ch = uartRxBuffer[last_read_index];
            last_read_index = (last_read_index + 1) % RX_BUFFER_SIZE;
            if (tempIndex < TEMP_BUFFER_SIZE - 1) {
                tempBuffer[tempIndex++] = ch;
            } else {
                tempIndex = 0;  // overflow guard
            }

            if (tempIndex >= 2 &&
                tempBuffer[tempIndex - 2] == '\r' &&
                tempBuffer[tempIndex - 1] == '\n') {

                tempBuffer[tempIndex - 2] = '\0';  // chop CRLF
                char *sep = strchr(tempBuffer, ':');
                if (sep) {
                    *sep = '\0';
                    float val = atof(sep + 1);
                    if (strcmp(tempBuffer, "MOD") == 0) {
                        telemetryData.mode = (ControlMode_t)(int)val;
                    } else if (strcmp(tempBuffer, "SRU") == 0) {
                        telemetryData.rudder_servo_angle = val;
                    } else if (strcmp(tempBuffer, "STR") == 0) {
                        telemetryData.trim_servo_angle = val;
                    } else if (strcmp(tempBuffer, "STW") == 0) {
                        telemetryData.twist_servo_angle = val;
                    } else if (strcmp(tempBuffer, "SEX") == 0) {
                        telemetryData.extra_servo_angle = val;
                    } else if (strcmp(tempBuffer, "KPR") == 0) {
                        telemetryData.Kp_roll = val;
                    } else if (strcmp(tempBuffer, "KIR") == 0) {
                        telemetryData.Ki_roll = val;
                    } else if (strcmp(tempBuffer, "KPY") == 0) {
                        telemetryData.Kp_yaw = val;
                    } else if (strcmp(tempBuffer, "KIY") == 0) {
                        telemetryData.Ki_yaw = val;
                    }
                }
                tempIndex = 0;
            }
        }
    }

    // Push the updated telemetry struct once
    osMessageQueuePut(telemetryQueueHandle, &telemetryData, 0, 0);
}
