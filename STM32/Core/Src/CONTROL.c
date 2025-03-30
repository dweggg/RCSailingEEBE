/*
 * CONTROL.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg (revised by [Your Name])
 *
 * This file now uses defined mechanical limits for each control surface.
 * Radio inputs are first mapped (0–1) to a mechanical angle (using user‐defined min/max),
 * then each set_xxx() function converts that mechanical angle to a servo angle (via a
 * dedicated conversion function), and finally to a pulse.
 *
 * All channel assignments and limit definitions are #defined for easy customization.
 */

#include "CONTROL.h"
#include "TELEMETRY.h"
#include "IMU.h"
#include "cmsis_os.h"

// External queue handles (set up in your RTOS initialization code).
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t telemetryQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

/* Global static variables */
static ImuData_t imu;
static ControlMode_t currentMode = MODE_DIRECT_INPUT;

// --- DIRECT INPUT CONTROL ---
// Simply maps normalized radio inputs to mechanical angles.
static ControlData_t direct_input_control(void) {
    ControlData_t control;
    control.rudder = map_radio_to_mech(get_radio_ch1(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    control.trim   = map_radio_to_mech(get_radio_ch2(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    control.twist  = map_radio_to_mech(get_radio_ch3(), TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    control.extra  = map_radio_to_mech(get_radio_ch4(), EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return control;
}

// --- AUTO CONTROL MODE 1 ---
// Example auto-control: rudder is computed from an average of two channels,
// twist is calculated using a simple PI controller, and trim is taken from one channel.
static float Kp = 1.0F, Ki = 0.1F, Kaw = 0.1F, Ts = 0.01F;
static float integrator_state = 0.0F;

static float roll_controller(float current_roll) {
    const float desired_roll = 0.0F;
    float error = desired_roll - current_roll;
    float unsaturated = Kp * error + integrator_state;
    float twist = unsaturated;
    if (twist > TWIST_MAX_ANGLE) {
        twist = TWIST_MAX_ANGLE;
    } else if (twist < TWIST_MIN_ANGLE) {
        twist = TWIST_MIN_ANGLE;
    }
    integrator_state += Ki * Ts * (error + (twist - unsaturated) * Kaw);
    return twist;
}

static ControlData_t auto_control_mode1(void) {
    ControlData_t control;

    // Rudder servo is controlled directly with radio channel 2.
    control.rudder = map_radio_to_mech(get_radio_ch2(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);

    // Twist servo is automatically controller depending on the roll.
    control.twist = roll_controller(imu.roll);

    // Trim servo is controlled directly with radio channel 1.
    control.trim = map_radio_to_mech(get_radio_ch1(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);

    // Extra channel (if used) from channel 4.
    // control.extra = map_radio_to_mech(get_radio_ch4(), EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return control;
}

// Stub functions for other auto control modes
static ControlData_t auto_control_mode2(void) {
    ControlData_t control = {0};

    return control;
}
static ControlData_t auto_control_mode3(void) {
    ControlData_t control = {0};

    return control;
}
static ControlData_t auto_control_mode4(void) {
    ControlData_t control = {0};

    return control;
}

// Dispatch function for automatic control modes.
static ControlData_t auto_control(ControlMode_t mode) {
    switch (mode) {
        case MODE_AUTO_1:
            return auto_control_mode1();
        case MODE_AUTO_2:
            return auto_control_mode2();
        case MODE_AUTO_3:
            return auto_control_mode3();
        case MODE_AUTO_4:
            return auto_control_mode4();
        default: {
            ControlData_t safe = {0};
            return safe;
        }
    }
}

// --- MAIN CONTROL TASK ---
// This task is meant to run under an RTOS. It receives data from queues,
// updates the current mode, processes inputs, and sends servo commands.
void control(void) {
    ControlData_t controlData = {0};

    TelemetryData_t newTelemetryData;
    ImuData_t newImuData;

    /* Update control mode from telemetry queue (non-blocking) */
    if (osMessageQueueGet(telemetryQueueHandle, &newTelemetryData, NULL, 0) == osOK) {
        currentMode = newTelemetryData.mode;
    }

    /* Update IMU data (non-blocking) */
    if (osMessageQueueGetCount(imuQueueHandle) > 0 && is_imu_initialized()) {
        if (osMessageQueueGet(imuQueueHandle, &newImuData, NULL, 0) == osOK) {
            imu = newImuData;
        }
    }

    if (currentMode == MODE_CALIBRATION) {
        update_radio_calibration();
    }

    // Dispatch control based on current mode.
    if (currentMode == MODE_DIRECT_INPUT) {
        controlData = direct_input_control();
    } else if (currentMode == MODE_AUTO_1 || currentMode == MODE_AUTO_2 ||
               currentMode == MODE_AUTO_3 || currentMode == MODE_AUTO_4) {
        controlData = auto_control(currentMode);
    } else {
        // Calibration or unknown mode: no control command issued.
        controlData.rudder = 0.0F;
        controlData.twist  = 0.0F;
        controlData.trim   = 0.0F;
        controlData.extra  = 0.0F;
    }

    // Send the control outputs to the servos.
    set_servo_rudder(controlData.rudder);
    set_servo_twist(controlData.twist);
    set_servo_trim(controlData.trim);
    set_servo_extra(controlData.extra);
    osMessageQueuePut(controlQueueHandle, &controlData, 0, 0);
    // Optionally, send controlData to a queue for logging/monitoring.
    // osMessageQueuePut(controlQueueHandle, &controlData, 0, 0);

    // Delay to control the task’s update rate (e.g., 10 ms).
}
