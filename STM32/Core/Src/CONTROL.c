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
#include "tim.h"
#include "cmsis_os.h"

/*------------------------------------------------*/
/*          USER CONFIGURABLE DEFINES             */
/*------------------------------------------------*/

/* Output channel assignments */
#define RUDDER_CHANNEL    TIM_CHANNEL_1
#define TRIM_CHANNEL      TIM_CHANNEL_2
#define TWIST_CHANNEL     TIM_CHANNEL_3
#define EXTRA_CHANNEL     TIM_CHANNEL_4   // For a fourth channel if needed

/* Mechanical limits (in degrees) for radio mapping */
#define RUDDER_MECH_MIN    10.0F
#define RUDDER_MECH_MAX    170.0F

#define TRIM_MECH_MIN      10.0F
#define TRIM_MECH_MAX      170.0F

#define TWIST_MECH_MIN     10.0F
#define TWIST_MECH_MAX     170.0F

#define EXTRA_MECH_MIN     10.0F
#define EXTRA_MECH_MAX     170.0F

/* Servo conversion limits (the conversion function from mechanical to servo angle)
   These allow you to “tweak” the servo angle mapping independent of the mechanical range */
#define RUDDER_SERVO_MIN_ANGLE    10.0F
#define RUDDER_SERVO_MAX_ANGLE    170.0F

#define TRIM_SERVO_MIN_ANGLE      10.0F
#define TRIM_SERVO_MAX_ANGLE      170.0F

#define TWIST_SERVO_MIN_ANGLE     10.0F
#define TWIST_SERVO_MAX_ANGLE     170.0F

#define EXTRA_SERVO_MIN_ANGLE     10.0F
#define EXTRA_SERVO_MAX_ANGLE     170.0F

/* Servo pulse parameters (in milliseconds) */
#define SERVO_PULSE_MIN_MS   0.6F
#define SERVO_PULSE_MAX_MS   2.4F

/* Timer conversion parameters */
#define TIMER_PERIOD         59999.0F
#define TIMER_FREQ           20.0F  // in ms

/* Global static variables (available to all functions) */
static ImuData_t imu;
static RadioData_t radioDataReceived;
static ControlData_t controlDataSent;
static ControlMode_t currentMode = MODE_DIRECT_INPUT;

/* External queue handles */
extern osMessageQueueId_t radioQueueHandle;
extern osMessageQueueId_t telemetryQueueHandle;
extern osMessageQueueId_t imuQueueHandle;
extern osMessageQueueId_t controlQueueHandle;

/* Forward declarations for radio input helpers */
static float get_radio_ch1(void);
static float get_radio_ch2(void);
static float get_radio_ch3(void);
static float get_radio_ch4(void);

/* Simple linear mapping helper function */
static float map_float(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

/*
 * New mapping functions: convert normalized radio value (0.0 to 1.0) to a mechanical angle.
 * This lets you define the full range of motion in mechanical degrees.
 */
static float map_radio_to_mech_rudder(float radio_val) {
    return ((radio_val * (RUDDER_MECH_MAX - RUDDER_MECH_MIN)) + RUDDER_MECH_MIN);
}

static float map_radio_to_mech_trim(float radio_val) {
    return ((radio_val * (TRIM_MECH_MAX - TRIM_MECH_MIN)) + TRIM_MECH_MIN);
}

static float map_radio_to_mech_twist(float radio_val) {
    return ((radio_val * (TWIST_MECH_MAX - TWIST_MECH_MIN)) + TWIST_MECH_MIN);
}

// meh we'll use it maybe
static float map_radio_to_mech_extra(float radio_val) {
    return ((radio_val * (EXTRA_MECH_MAX - EXTRA_MECH_MIN)) + EXTRA_MECH_MIN);
}

/*
 * Conversion functions: convert a mechanical angle to a servo angle.
 * You can tweak these functions (or even make them non-linear) so that each control
 * surface can have its own mapping from mechanical to servo “angle.”
 */
static float mech_to_servo_rudder(float mech_angle) {
    return map_float(mech_angle, RUDDER_MECH_MIN, RUDDER_MECH_MAX, RUDDER_SERVO_MIN_ANGLE, RUDDER_SERVO_MAX_ANGLE);
}

static float mech_to_servo_trim(float mech_angle) {
    return map_float(mech_angle, TRIM_MECH_MIN, TRIM_MECH_MAX, TRIM_SERVO_MIN_ANGLE, TRIM_SERVO_MAX_ANGLE);
}

static float mech_to_servo_twist(float mech_angle) {
    return map_float(mech_angle, TWIST_MECH_MIN, TWIST_MECH_MAX, TWIST_SERVO_MIN_ANGLE, TWIST_SERVO_MAX_ANGLE);
}

static float mech_to_servo_extra(float mech_angle) {
    return map_float(mech_angle, EXTRA_MECH_MIN, EXTRA_MECH_MAX, EXTRA_SERVO_MIN_ANGLE, EXTRA_SERVO_MAX_ANGLE);
}

/*
 * Common helper: convert a servo angle to a pulse value.
 * The conversion uses the defined pulse range and timer parameters.
 */
static uint32_t servo_angle_to_pulse(float servo_angle, float servo_min_angle, float servo_max_angle) {
    float pulse_ms = map_float(servo_angle, servo_min_angle, servo_max_angle, SERVO_PULSE_MIN_MS, SERVO_PULSE_MAX_MS);
    float compare_val = pulse_ms * TIMER_PERIOD / TIMER_FREQ;
    return (uint32_t) compare_val;
}

/*------------------------------------------------*/
/* Servo Command Wrappers for Automatic Control   */
/* (Each function now accepts a mechanical angle.)  */
/*------------------------------------------------*/
static void set_rudder(float mech_angle) {
    float servo_angle = mech_to_servo_rudder(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, RUDDER_SERVO_MIN_ANGLE, RUDDER_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, RUDDER_CHANNEL, pulse);
}

static void set_trim(float mech_angle) {
    float servo_angle = mech_to_servo_trim(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TRIM_SERVO_MIN_ANGLE, TRIM_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, TRIM_CHANNEL, pulse);
}

static void set_twist(float mech_angle) {
    float servo_angle = mech_to_servo_twist(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TWIST_SERVO_MIN_ANGLE, TWIST_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, TWIST_CHANNEL, pulse);
}

static void set_extra(float mech_angle) {
    float servo_angle = mech_to_servo_extra(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, EXTRA_SERVO_MIN_ANGLE, EXTRA_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, EXTRA_CHANNEL, pulse);
}



/*------------------------------------------------*/
/*                 Roll Control                   */
/*------------------------------------------------*/

float Kp = 1.0F;    // Proportional gain
float Ki = 0.1F;    // Integral gain
float Kaw = 0.1F;   // Anti-windup gain (1/Kp)
float Ts = 0.01F;   // Sampling time in seconds



// Simple PI controller with anti-windup
float roll_control(void) {
    // Desired roll angle (setpoint)
    const float desired_roll_angle = 0.0F;

    // Calculate error between desired and current roll
    float roll_error = desired_roll_angle - imu.roll;

    // Static integrator state persists between calls
    static float integrator_state = 0.0F;

    // Compute unsaturated twist output using current error and integrator
    float unsaturated_twist = Kp * roll_error + integrator_state;

    // Apply saturation limits to prevent excessive twist
    float twist_output = unsaturated_twist;
    if (unsaturated_twist > TWIST_MECH_MAX) {
        twist_output = TWIST_MECH_MAX;
    } else if (unsaturated_twist < TWIST_MECH_MIN) {
        twist_output = TWIST_MECH_MIN;
    }

    // Anti-windup integration update using Euler integration:
    // New integrator state = old state + Ki*Ts*(error + (sat - unsat)*Kaw)
    integrator_state += Ki * Ts * (roll_error + (twist_output - unsaturated_twist) * Kaw);

    // Return the saturated twist angle output
    return twist_output;
}

/*------------------------------------------------*/
/*       COOL STUFF - CONTROL                */
/*------------------------------------------------*/



/*------------------------------------------------*/
/* Direct Input Mode: Map radio directly to mechanical angles */
/* and then command each servo via the conversion chain         */
/*------------------------------------------------*/
static void handleDirectInputMode(void) {
    controlDataSent.rudder = map_radio_to_mech_rudder(get_radio_ch1());
    controlDataSent.trim   = map_radio_to_mech_trim(get_radio_ch2());
    controlDataSent.twist  = map_radio_to_mech_twist(get_radio_ch3());
    /* Now send the control command to the control queue */
    osMessageQueuePut(controlQueueHandle, &controlDataSent, 0, 0);
}


/* Auto Control Mode 1 */
static void autoControlMode1(void) {
    /* For the rudder, average radio channels 2 and 4 then map to mechanical angle */
    controlDataSent.rudder = map_radio_to_mech_rudder((get_radio_ch2() + get_radio_ch4()) * 0.5F);

    /* Calculate twist using a roll controller */
    controlDataSent.twist = roll_control();

    /* For trim, map radio channel 1 directly */
    controlDataSent.trim = map_radio_to_mech_trim(get_radio_ch1());

    /* Send the calculated control angles to the control queue */
    osMessageQueuePut(controlQueueHandle, &controlDataSent, 0, 0);
}

/* Auto Control Mode 2 */
static void autoControlMode2(void) {
    // Insert alternative control strategy here
}

/* Auto Control Mode 3 */
static void autoControlMode3(void) {
    // Insert alternative control strategy here
}

/* Auto Control Mode 4 */
static void autoControlMode4(void) {
    // Insert alternative control strategy here
}

/* Dispatcher for automatic control modes */
static void handleAutoControlMode(ControlMode_t mode) {
    switch (mode) {
        case MODE_AUTO_1:
            autoControlMode1();
            break;
        case MODE_AUTO_2:
            autoControlMode2();
            break;
        case MODE_AUTO_3:
            autoControlMode3();
            break;
        case MODE_AUTO_4:
            autoControlMode4();
            break;
        default:
            // Unknown mode: do nothing (or implement safe behavior)
            break;
    }
}

/*-----------------------------------------*/
/* MAIN CONTROL FUNCTION (High-level flow) */
/*-----------------------------------------*/

/* Forward declarations for calibration and direct input routines */
static void handleCalibrationMode(void);
static void handleDirectInputMode(void);

void control(void) {
    TelemetryData_t receivedTelemetryData;
    RadioData_t newRadioData;
    ImuData_t newImuData;

    /* Update control mode from telemetry queue (non-blocking) */
    if (osMessageQueueGet(telemetryQueueHandle, &receivedTelemetryData, NULL, 0) == osOK) {
        currentMode = receivedTelemetryData.mode;
    }

    /* Update radio data (non-blocking) */
    if (osMessageQueueGet(radioQueueHandle, &newRadioData, NULL, 0) == osOK) {
        radioDataReceived = newRadioData;
    }

    /* Update IMU data (non-blocking) */
    if (osMessageQueueGetCount(imuQueueHandle) > 0 && is_imu_initialized()) {
        if (osMessageQueueGet(imuQueueHandle, &newImuData, NULL, 0) == osOK) {
            imu = newImuData;
        }
    }

    /* Dispatch based on current control mode */
    switch (currentMode) {
        case MODE_CALIBRATION:
            handleCalibrationMode();
            break;
        case MODE_DIRECT_INPUT:
            handleDirectInputMode();
            break;
        case MODE_AUTO_1:
        case MODE_AUTO_2:
        case MODE_AUTO_3:
        case MODE_AUTO_4:
            handleAutoControlMode(currentMode);
            break;
        default:
            // Unknown mode: implement safe behavior if needed
            break;
    }

    set_rudder(controlDataSent.rudder);
    set_twist(controlDataSent.twist);
    set_trim(controlDataSent.trim);
    set_extra(controlDataSent.extra);
}

/*------------------------------------------------*/
/*  BORING STUFF BELOW: CALIBRATION & MAPPING     */
/*------------------------------------------------*/

/* Global structure to store calibration boundaries for each radio channel */
typedef struct {
    uint32_t ch1_min;
    uint32_t ch1_max;
    uint32_t ch2_min;
    uint32_t ch2_max;
    uint32_t ch3_min;
    uint32_t ch3_max;
    uint32_t ch4_min;
    uint32_t ch4_max;
} RadioMapping_t;

/* Initialize boundaries to extreme values */
static RadioMapping_t mappingBoundaries = {
    .ch1_min = 0xFFFFFFFF, .ch1_max = 0,
    .ch2_min = 0xFFFFFFFF, .ch2_max = 0,
    .ch3_min = 0xFFFFFFFF, .ch3_max = 0,
    .ch4_min = 0xFFFFFFFF, .ch4_max = 0
};

#define MIN_VALID_PULSE_US 100  // Only consider pulse widths >100 µs as valid

/*------------------------------------------------*/
/*  Radio Input Helpers (calibrated and normalized) */
/*------------------------------------------------*/
static float get_radio_ch1(void) {
    if (mappingBoundaries.ch1_max <= mappingBoundaries.ch1_min)
        return 0.0F;
    return (float)(radioDataReceived.ch1 - mappingBoundaries.ch1_min) /
           (float)(mappingBoundaries.ch1_max - mappingBoundaries.ch1_min);
}
static float get_radio_ch2(void) {
    if (mappingBoundaries.ch2_max <= mappingBoundaries.ch2_min)
        return 0.0F;
    return (float)(radioDataReceived.ch2 - mappingBoundaries.ch2_min) /
           (float)(mappingBoundaries.ch2_max - mappingBoundaries.ch2_min);
}
static float get_radio_ch3(void) {
    if (mappingBoundaries.ch3_max <= mappingBoundaries.ch3_min)
        return 0.0F;
    return (float)(radioDataReceived.ch3 - mappingBoundaries.ch3_min) /
           (float)(mappingBoundaries.ch3_max - mappingBoundaries.ch3_min);
}
static float get_radio_ch4(void) {
    if (mappingBoundaries.ch4_max <= mappingBoundaries.ch4_min)
        return 0.0F;
    return (float)(radioDataReceived.ch4 - mappingBoundaries.ch4_min) /
           (float)(mappingBoundaries.ch4_max - mappingBoundaries.ch4_min);
}

/*------------------------------------------------*/
/* Calibration Mode: Update channel boundaries    */
/*------------------------------------------------*/
static void handleCalibrationMode(void) {
    if (radioDataReceived.ch1 < mappingBoundaries.ch1_min && radioDataReceived.ch1 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch1_min = radioDataReceived.ch1;
    if (radioDataReceived.ch1 > mappingBoundaries.ch1_max)
        mappingBoundaries.ch1_max = radioDataReceived.ch1;

    if (radioDataReceived.ch2 < mappingBoundaries.ch2_min && radioDataReceived.ch2 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch2_min = radioDataReceived.ch2;
    if (radioDataReceived.ch2 > mappingBoundaries.ch2_max)
        mappingBoundaries.ch2_max = radioDataReceived.ch2;

    if (radioDataReceived.ch3 < mappingBoundaries.ch3_min && radioDataReceived.ch3 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch3_min = radioDataReceived.ch3;
    if (radioDataReceived.ch3 > mappingBoundaries.ch3_max)
        mappingBoundaries.ch3_max = radioDataReceived.ch3;

    if (radioDataReceived.ch4 < mappingBoundaries.ch4_min && radioDataReceived.ch4 > MIN_VALID_PULSE_US)
        mappingBoundaries.ch4_min = radioDataReceived.ch4;
    if (radioDataReceived.ch4 > mappingBoundaries.ch4_max)
        mappingBoundaries.ch4_max = radioDataReceived.ch4;
}
