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

/*
 * For the rudder, we use lookup arrays to map mechanical angles to servo angles.
 * (These values should now be defined in the calibrated [0, RUDDER_SERVO_RANGE] space.)
 */
static const float rudder_mech_angles[11] = {
    -35.00, -27.22, -19.44, -11.67, -3.89, 0.00, 3.89, 11.67, 19.44, 27.22, 35.00
};

// Calibrated servo angles (0 to RUDDER_SERVO_RANGE) for the corresponding mechanical angles.
static const float rudder_servo_angles[11] = {
    150.06, 136.15, 124.51, 113.64, 102.98,  97.61,  92.19,  81.04,  69.27,  56.49,  41.98
};

float mech_to_servo_rudder(float mech_angle) {
    // Handle out-of-range cases by clamping to the endpoints.
    if (mech_angle <= RUDDER_MIN_ANGLE) {
        return rudder_servo_angles[0];
    }
    if (mech_angle >= RUDDER_MAX_ANGLE) {
        return rudder_servo_angles[10];
    }

    // Find the two nearest points for interpolation.
    for (int i = 0; i < (sizeof(rudder_mech_angles)/sizeof(rudder_mech_angles[0]) - 1); i++) {
        if (mech_angle >= rudder_mech_angles[i] && mech_angle <= rudder_mech_angles[i+1]) {
            // Linear interpolation.
            float mech_range = rudder_mech_angles[i+1] - rudder_mech_angles[i];
            float servo_range_interval = rudder_servo_angles[i+1] - rudder_servo_angles[i];
            float ratio = (mech_angle - rudder_mech_angles[i]) / mech_range;
            return rudder_servo_angles[i] + (ratio * servo_range_interval);
        }
    }

    // Fallback: find the servo angle corresponding to 0° mechanical rudder.
    float zero_mech_angle = 0.0F;
    float smallest_diff = fabs(rudder_mech_angles[0] - zero_mech_angle);
    int zero_index = 0;
    for (int i = 1; i < (sizeof(rudder_mech_angles)/sizeof(rudder_mech_angles[0])); i++) {
        float current_diff = fabs(rudder_mech_angles[i] - zero_mech_angle);
        if (current_diff < smallest_diff) {
            smallest_diff = current_diff;
            zero_index = i;
        }
    }
    return rudder_servo_angles[zero_index];
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
