/*
 * CONTROL.c
 *
 *  Created on: Feb 22, 2025
 *      Author: dweggg (revised by [Your Name])
 *
 *  Refined version: clean structure, fixed controller sign conventions,
 *  improved integrator anti-windup, safe initialization, explicit
 *  error handling, early-mode-exit for calibration, and documentation.
 */

#include "CONTROL.h"
#include "TELEMETRY.h"
#include "IMU.h"
#include "cmsis_os.h"
#include <math.h>
#include <stdio.h>

// External queue handles (set up elsewhere)
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t telemetryQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

// -----------------------------------------------------------------------------
// --- GLOBAL & STATIC STATE ---------------------------------------------------
// -----------------------------------------------------------------------------
static ImuData_t    imu = {0};
static ControlMode_t currentMode = MODE_DIRECT_INPUT;

// Controller gains (updated via telemetry in non-calibration modes)
static float Kp_roll = 1.0f, Ki_roll = 0.1f;
static float Kp_yaw  = 1.0f, Ki_yaw  = 0.1f;

// Internal integrator states and timing
static float integrator_roll = 0.0f;
static uint32_t last_tick_roll = 0;
static float integrator_yaw  = 0.0f;
static uint32_t last_tick_yaw  = 0;

// Desired setpoints
static float desired_roll   = 0.0f;
static float desired_yaw_rate = 0.0f;

static float MAX_YAW_RATE = 5.0f;
static float MIN_YAW_RATE = -5.0f;

// -----------------------------------------------------------------------------
// --- HELPER FUNCTIONS --------------------------------------------------------
// -----------------------------------------------------------------------------

/**
 * @brief Compute time step since last call, with safe first-time behavior.
 * @param last_tick_ptr Pointer to the previous tick count.
 * @return elapsed time in seconds.
 */
static float get_delta_time(uint32_t *last_tick_ptr) {
    uint32_t now = osKernelGetTickCount();           // [ms]
    float dt = 0.0f;
    if (*last_tick_ptr != 0) {
        dt = (now - *last_tick_ptr) * 1e-3f;         // convert ms->s
    }
    *last_tick_ptr = now;
    return fmaxf(dt, 0.0f);
}

/**
 * @brief Anti-windup utility: clamp and adjust integrator.
 */
static float clamp_with_integrator(float unsat, float *integrator, float Kp, float Ki,
                                   float error, float dt, float min_out, float max_out) {
    float out = fminf(fmaxf(unsat, min_out), max_out);
    // Back-calculate integrator increment (tracking anti-windup)
    float dw = (out - unsat) / (Kp > 0 ? Kp : 1.0f);
    *integrator += Ki * dt * (error + dw);
    return out;
}

// -----------------------------------------------------------------------------
// --- CONTROL MODES -----------------------------------------------------------
// -----------------------------------------------------------------------------

static ControlData_t direct_input_control(void) {
    ControlData_t c = {0};
    c.rudder = map_radio(get_radio_ch1(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    c.trim   = map_radio(get_radio_ch3(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    c.twist  = map_radio(get_radio_ch2(), TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    c.extra  = map_radio(get_radio_ch4(), EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return c;
}

static float roll_controller(float current_roll) {
    // Error = setpoint - measurement (negative feedback)
    float error = desired_roll - current_roll;
    float dt    = get_delta_time(&last_tick_roll);
    // PI unsaturated output
    float unsat = Kp_roll * error + integrator_roll;
    // Anti-windup clamping
    float twist = clamp_with_integrator(unsat, &integrator_roll,
                                        Kp_roll, Ki_roll,
                                        error, dt,
                                        TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    // Optional integrator reset near 0 error
    if (fabsf(current_roll) < 1.0f) {
        integrator_roll = 0.0f;
    }
    return twist;
}

static float yaw_rate_controller(float current_rate) {
    float error = desired_yaw_rate - current_rate;
    float dt    = get_delta_time(&last_tick_yaw);
    float unsat = Kp_yaw * error + integrator_yaw;
    float out   = clamp_with_integrator(unsat, &integrator_yaw,
                                        Kp_yaw, Ki_yaw,
                                        error, dt,
                                        RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    return out;
}

static ControlData_t auto_control_mode1(void) {
    ControlData_t c = {0};
    c.rudder = map_radio(get_radio_ch2(), RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    c.trim   = map_radio(get_radio_ch3(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    // maintain zero roll
    desired_roll = 0.0f;
    c.twist  = roll_controller(imu.roll);
    c.extra  = 0.0f;
    return c;
}

static ControlData_t auto_control_mode2(void) {
    ControlData_t c = {0};
    // Direct yaw-rate command from channel 1
    desired_yaw_rate = map_radio(get_radio_ch1(), MIN_YAW_RATE, MAX_YAW_RATE);
    c.rudder = yaw_rate_controller(imu.gyroZ);

    c.trim   = map_radio(get_radio_ch3(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    // Twist direct mapping
    c.twist  = map_radio(get_radio_ch2(), TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    c.extra  = 0.0f;
    return c;
}

static ControlData_t auto_control_mode3(void) {
    ControlData_t c = {0};
    desired_yaw_rate = map_radio(get_radio_ch1(), MIN_YAW_RATE, MAX_YAW_RATE);
    c.rudder = yaw_rate_controller(imu.gyroZ);
    c.trim   = map_radio(get_radio_ch3(), TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    desired_roll = 0.0f;
    c.twist  = roll_controller(imu.roll);
    c.extra  = 0.0f;
    return c;
}

static ControlData_t auto_control_mode4(void) {
    // Unused/placeholder mode: all servos neutral
    ControlData_t c = {0};
    return c;
}

static ControlData_t auto_control_dispatch(ControlMode_t m) {
    switch (m) {
        case MODE_AUTO_1: return auto_control_mode1();
        case MODE_AUTO_2: return auto_control_mode2();
        case MODE_AUTO_3: return auto_control_mode3();
        case MODE_AUTO_4: return auto_control_mode4();
        default:         return (ControlData_t){0};
    }
}

// -----------------------------------------------------------------------------
// --- MAIN CONTROL TASK ------------------------------------------------------
// -----------------------------------------------------------------------------
void control(void) {
    ControlData_t ctrl = {0};
    TelemetryData_t tel = {0};
    ImuData_t imu_in    = {0};
    BaseType_t status;

    // 1) Poll telemetry (non-blocking)
    status = osMessageQueueGet(telemetryQueueHandle, &tel, NULL, 0);
    if (status == osOK) {
        // Mode transition or reset
        if (tel.mode == MODE_RESET) {
            NVIC_SystemReset();
        }
        if (tel.mode >= MODE_CALIBRATION && tel.mode <= MODE_AUTO_4) {
            currentMode = tel.mode;
        }
        // Update gains (even if staying in same mode)
        Kp_roll = tel.Kp_roll;
        Ki_roll = tel.Ki_roll;
        Kp_yaw  = tel.Kp_yaw;
        Ki_yaw  = tel.Ki_yaw;
    }

    // Calibration: apply servo angles directly and exit early
    if (currentMode == MODE_CALIBRATION) {
        set_servo_rudder(tel.rudder_servo_angle);
        set_servo_twist (tel.twist_servo_angle);
        set_servo_trim  (tel.trim_servo_angle);
        set_servo_extra (tel.extra_servo_angle);
        return;
    }

    // 2) Update IMU if available
    if (osMessageQueueGetCount(imuQueueHandle) > 0 && is_imu_initialized()) {
        if (osMessageQueueGet(imuQueueHandle, &imu_in, NULL, 0) == osOK) {
            imu = imu_in;
        }
    }

    // 3) Choose control based on mode
    if (currentMode == MODE_DIRECT_INPUT) {
        ctrl = direct_input_control();
    } else if ((currentMode >= MODE_AUTO_1 && currentMode <= MODE_AUTO_4) && is_imu_initialized()) {
        ctrl = auto_control_dispatch(currentMode);
    } else {
        // Unknown or uninitialised: neutral
        disable_all_servos();
        return;
    }

    // 4) Send to servos and telemetry
    set_rudder(ctrl.rudder);
    set_twist (ctrl.twist);
    set_trim  (ctrl.trim);
    set_extra (ctrl.extra);
    osMessageQueuePut(controlQueueHandle, &ctrl, 0, 0);
}

/**
 * @brief Simple first-order low-pass filter.
 */
float low_pass_filter(float input, float prev_output, float alpha) {
    return alpha * input + (1.0f - alpha) * prev_output;
}
