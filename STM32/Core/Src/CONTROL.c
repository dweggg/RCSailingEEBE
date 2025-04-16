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
#include <math.h>

// External queue handles (set up in your RTOS initialization code).
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t telemetryQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

/* Global static variables */
static ImuData_t imu;
static ControlMode_t currentMode = MODE_DIRECT_INPUT;

/* --- CONTROLLER GAINS --- */
// Renamed PI gains for roll control.
static float Kp_roll = 1.0F, Ki_roll = 0.1F;
// New PI gains reserved for yaw rate control.
static float Kp_yaw = 1.0F, Ki_yaw = 0.1F;

// --- DIRECT INPUT CONTROL ---
// Simply maps normalized radio inputs to mechanical angles.
static ControlData_t direct_input_control(void) {
    ControlData_t control;
    control.rudder = map_radio(get_radio_ch1(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    control.trim   = map_radio(get_radio_ch2(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    control.twist  = map_radio(get_radio_ch3(), TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    control.extra  = map_radio(get_radio_ch4(), EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return control;
}

// --- AUTO CONTROL MODE 1 ---
// Example auto-control: rudder is computed from an average of two channels,
// twist is calculated using a PI controller based on roll, and trim is taken directly.
// Yaw rate control is not yet implemented but its framework is prepared.

static float integrator_state_roll = 0.0F;
static uint32_t previous_tick_roll = 0;  // store the tick count from the previous call

static float roll_controller(float current_roll) {
    const float desired_roll = 0.0F;  // Target roll is zero in this example.

    // Get the current tick count (assuming ticks are in milliseconds).
    uint32_t current_tick = osKernelGetTickCount();

    // Calculate elapsed time (Ts) in seconds.
    float Ts = (previous_tick_roll == 0) ? 0.01F : ((current_tick - previous_tick_roll) / 1000.0F);
    previous_tick_roll = current_tick;

    // Compute error and the preliminary (unsaturated) twist value.
    float error = current_roll - desired_roll;
    float unsaturated = Kp_roll * error + integrator_state_roll;
    float twist = unsaturated;

    // Saturate the twist command.
    if (twist > TWIST_MAX_ANGLE) {
        twist = TWIST_MAX_ANGLE;
    } else if (twist < TWIST_MIN_ANGLE) {
        twist = TWIST_MIN_ANGLE;
    }

    // Update the integrator state using dynamic Ts.
    integrator_state_roll += Ki_roll * Ts * (error + (twist - unsaturated)/Kp_roll);

    // Optionally reset integrator when roll is near zero.
    if (fabs(current_roll) < 5.0F) {
        integrator_state_roll = 0.0F;
    }

    return twist;
}

// Stub for yaw rate controller. The control structure is similar to the roll_controller.
// This is a placeholder for future implementation of yaw rate control.
static float integrator_state_yaw = 0.0F;
static uint32_t previous_tick_yaw = 0;
float desired_yaw_rate = 0.0F;

#define MAX_YAW_RATE 1000.0f
#define MIN_YAW_RATE -1000.0f

static float yaw_rate_controller(float current_yaw_rate, float desired_yaw_rate) {
    uint32_t current_tick = osKernelGetTickCount();

    float Ts = (previous_tick_yaw == 0) ? 0.01F : ((current_tick - previous_tick_yaw) / 1000.0F);
    previous_tick_yaw = current_tick;

    float error = current_yaw_rate - desired_yaw_rate;
    float unsaturated = Kp_yaw * error + integrator_state_yaw;
    float control_output = unsaturated;

    // (Add saturation limits if necessary for yaw rate).
    // For example:
    if (control_output > RUDDER_MAX_ANGLE) { control_output = RUDDER_MAX_ANGLE; }
    else if (control_output < RUDDER_MIN_ANGLE) { control_output = RUDDER_MIN_ANGLE; }

    integrator_state_yaw += Ki_yaw * Ts * (error + (control_output - unsaturated)/Kp_yaw);

    return control_output;
}

static ControlData_t auto_control_mode1(void) {
    ControlData_t control;

    // Rudder servo is controlled directly with radio channel 1.
    control.rudder = map_radio(get_radio_ch1(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);

    // Trim servo is controlled directly with radio channel 2.
    control.trim = map_radio(get_radio_ch2(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);

    // Twist servo is automatically controlled based on the roll.
    control.twist = roll_controller(fabs(imu.roll));

    // For auto mode 1, extra channel is not used; if needed, extend for yaw rate later.
    control.extra = 0.0F;

    return control;
}

// Stub functions for other auto control modes.
static ControlData_t auto_control_mode2(void) {
    ControlData_t control;
    // Rudder servo is controlled directly with radio channel 1.
    desired_yaw_rate = map_radio(get_radio_ch1(), MIN_YAW_RATE, MAX_YAW_RATE);

    control.rudder = yaw_rate_controller(imu.gyroZ, desired_yaw_rate);

    // Trim servo is controlled directly with radio channel 2.
    control.trim = map_radio(get_radio_ch2(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);

    // Twist servo is automatically controlled based on the roll.
    control.twist = map_radio(get_radio_ch3(), TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);

    // For auto mode 1, extra channel is not used;
    control.extra = 0.0F;

    return control;
}

static ControlData_t auto_control_mode3(void) {
    ControlData_t control;
    // Rudder servo is controlled directly with radio channel 1.
    desired_yaw_rate = map_radio(get_radio_ch1(), MIN_YAW_RATE, MAX_YAW_RATE);

    control.rudder = yaw_rate_controller(imu.gyroZ, desired_yaw_rate);

    // Trim servo is controlled directly with radio channel 2.
    control.trim = map_radio(get_radio_ch2(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);

    // Twist servo is automatically controlled based on the roll.
    control.twist = roll_controller(fabs(imu.roll));

    // For auto mode 1, extra channel is not used;
    control.extra = 0.0F;

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
    int32_t msgStatus;

    /* Update control mode and calibration data from telemetry queue (non-blocking) */
    msgStatus = osMessageQueueGet(telemetryQueueHandle, &newTelemetryData, NULL, 0);
    if (msgStatus == osOK) {
        // Update current mode if within expected range.
        if (newTelemetryData.mode >= MODE_CALIBRATION && newTelemetryData.mode <= MODE_AUTO_4) {
            currentMode = newTelemetryData.mode;
        }
        if (newTelemetryData.mode == MODE_RESET) {
            NVIC_SystemReset();
        }

        // In calibration mode, override servo settings and controller gains.
        if (currentMode == MODE_CALIBRATION) {
            controlData.rudder = newTelemetryData.rudder_servo_angle;
            controlData.trim   = newTelemetryData.trim_servo_angle;
            controlData.twist  = newTelemetryData.twist_servo_angle;
            controlData.extra  = newTelemetryData.extra_servo_angle;

        }
    }

    /* Update IMU data (non-blocking) */
    if (osMessageQueueGetCount(imuQueueHandle) > 0 && is_imu_initialized()) {
        if (osMessageQueueGet(imuQueueHandle, &newImuData, NULL, 0) == osOK) {
            imu = newImuData;
        }
    }

    // If not in calibration mode, choose the control strategy.
    if (currentMode != MODE_CALIBRATION) {
        if (currentMode == MODE_DIRECT_INPUT) {
            controlData = direct_input_control();
        } else if ((currentMode == MODE_AUTO_1 || currentMode == MODE_AUTO_2 ||
                    currentMode == MODE_AUTO_3 || currentMode == MODE_AUTO_4) &&
                   is_imu_initialized()) {
            controlData = auto_control(currentMode);
            // Update controller gains using telemetry values.
            Kp_roll     = newTelemetryData.Kp_roll;
            Ki_roll     = newTelemetryData.Ki_roll;
            Kp_yaw 		= newTelemetryData.Kp_yaw;
            Ki_yaw		= newTelemetryData.Ki_yaw;

        } else {
            // Unknown mode: freewheel the servos
        	disable_all_servos();
        }
    }

    // Send the control outputs to the servos.
    set_servo_rudder(controlData.rudder);
    set_servo_twist(controlData.twist);
    set_servo_trim(controlData.trim);
    set_servo_extra(controlData.extra);

    // Send control data to the queue for logging/monitoring.
    osMessageQueuePut(controlQueueHandle, &controlData, 0, 0);

    // Delay to control the task’s update rate (e.g., 10 ms).
}

float low_pass_filter(float input, float prev_output, float alpha) {
    return alpha * input + (1.0F - alpha) * prev_output;
}
