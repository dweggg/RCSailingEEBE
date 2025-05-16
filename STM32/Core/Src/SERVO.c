/*
 * SERVO.c
 *
 *  Created on: Mar 30, 2025
 *      Author: dweggg
 */

#include "SERVO.h"
#include "tim.h"
#include <math.h>


// Define servo pulse parameters.
#define SERVO_PULSE_MIN_MS    0.6F
#define SERVO_PULSE_MAX_MS    2.4F

#define TRIM_PULSE_MIN_MS     0.85F
#define TRIM_PULSE_MAX_MS     2.05F

#define TIMER_PERIOD          59999.0F
#define TIMER_FREQ            20.0F  // in ms

// Helper: saturate value between min and max.
static float saturate(float x, float min, float max) {
    if (x < min)
        return min;
    if (x > max)
        return max;
    return x;
}

// Helper: linearly map x from [in_min, in_max] to [out_min, out_max].
static float map(float x, float in_min, float in_max, float out_min, float out_max) {
	x = saturate(x, in_min, in_max);
	float out;
	out =  (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
	out = saturate(out, out_min, out_max);
	return out;
}

// Now the conversion function maps a servo angle (in degrees, from 0 to servo_range)
// to the PWM pulse width.
uint32_t servo_angle_to_pulse(float servo_angle, float servo_range) {
    float pulse_ms = map(servo_angle, 0.0F, servo_range, SERVO_PULSE_MIN_MS, SERVO_PULSE_MAX_MS); // min angle is 0
    float compare_val = pulse_ms * TIMER_PERIOD / TIMER_FREQ;
    return (uint32_t) compare_val;
}

uint32_t servo_angle_to_pulse_trim(float servo_angle, float servo_range) {
    float pulse_ms = map(servo_angle, 0.0F, 2160.0F, TRIM_PULSE_MIN_MS, TRIM_PULSE_MAX_MS); // min angle is 0
    float compare_val = pulse_ms * TIMER_PERIOD / TIMER_FREQ;
    return (uint32_t) compare_val;
}

float mech_to_servo_rudder(float mech_angle) {
    float sat_angle = saturate(mech_angle, RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE);
    return map(sat_angle, RUDDER_MIN_ANGLE, RUDDER_MAX_ANGLE, 0.0F, RUDDER_SERVO_RANGE);

}

/*
 * For trim, twist, and extra, assume the mechanical angle must be mapped linearly into the calibrated
 * servo range [0, servo_range]. The mechanical limits (TRIM_MIN_ANGLE etc.) remain defined elsewhere.
 */
float mech_to_servo_trim(float mech_angle) {
    float sat_angle = saturate(mech_angle, TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    return map(sat_angle, TRIM_MIN_ANGLE, TRIM_MAX_ANGLE, 0.0F, TRIM_SERVO_RANGE);
}

float mech_to_servo_twist(float mech_angle) {
    float sat_angle = saturate(mech_angle, TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    return map(sat_angle, TWIST_MIN_ANGLE, TWIST_MAX_ANGLE, 0.0F, TWIST_SERVO_RANGE);
}

float mech_to_servo_extra(float mech_angle) {
    float sat_angle = saturate(mech_angle, EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return map(sat_angle, EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE, 0.0F, EXTRA_SERVO_RANGE);
}

/*
 * Servo command functions: each one gets a desired mechanical angle,
 * converts it to a calibrated servo angle (in [0, servo_range]), and then sets the servo output.
 */
void set_rudder(float mech_angle) {
    float servo_angle = mech_to_servo_rudder(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, RUDDER_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, RUDDER_CHANNEL, pulse);
}

void set_trim(float mech_angle) {
    float servo_angle = mech_to_servo_trim(mech_angle);
    uint32_t pulse = servo_angle_to_pulse_trim(servo_angle, TRIM_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, TRIM_CHANNEL, pulse);
}

void set_twist(float mech_angle) {
    float servo_angle = mech_to_servo_twist(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TWIST_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, TWIST_CHANNEL, pulse);
}

void set_extra(float mech_angle) {
    float servo_angle = mech_to_servo_extra(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, EXTRA_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, EXTRA_CHANNEL, pulse);
}

void set_servo_rudder(float servo_angle) {
    uint32_t pulse = servo_angle_to_pulse(servo_angle, RUDDER_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, RUDDER_CHANNEL, pulse);
}

void set_servo_trim(float servo_angle) {
    uint32_t pulse = servo_angle_to_pulse_trim(servo_angle, TRIM_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, TRIM_CHANNEL, pulse);
}

void set_servo_twist(float servo_angle) {
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TWIST_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, TWIST_CHANNEL, pulse);
}

void set_servo_extra(float servo_angle) {
    uint32_t pulse = servo_angle_to_pulse(servo_angle, EXTRA_SERVO_RANGE);
    __HAL_TIM_SET_COMPARE(&htim4, EXTRA_CHANNEL, pulse);
}


void disable_all_servos(void) {
    // Set compare values to 0 to stop PWM on all servo channels, making them freewheel.
    __HAL_TIM_SET_COMPARE(&htim4, RUDDER_CHANNEL, 0);
    __HAL_TIM_SET_COMPARE(&htim4, TRIM_CHANNEL, 0);
    __HAL_TIM_SET_COMPARE(&htim4, TWIST_CHANNEL, 0);
    __HAL_TIM_SET_COMPARE(&htim4, EXTRA_CHANNEL, 0);
}
