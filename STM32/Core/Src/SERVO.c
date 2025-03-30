/*
 * SERVO.c
 *
 *  Created on: Mar 30, 2025
 *      Author: dweggg
 */

#include "SERVO.h"
#include "tim.h"  // Hardware-specific timer header (adjust as needed)
#include <math.h>

// Define servo pulse parameters.
#define SERVO_PULSE_MIN_MS   0.6F
#define SERVO_PULSE_MAX_MS   2.4F
#define TIMER_PERIOD         59999.0F
#define TIMER_FREQ           20.0F  // in ms

// Helper: linearly map x from [in_min, in_max] to [out_min, out_max].
static float map(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Helper: saturate value between min and max.
static float saturate(float x, float min, float max) {
    if (x < min)
        return min;
    if (x > max)
        return max;
    return x;
}

uint32_t servo_angle_to_pulse(float servo_angle, float servo_min_angle, float servo_max_angle) {
    float pulse_ms = map(servo_angle, servo_min_angle, servo_max_angle, SERVO_PULSE_MIN_MS, SERVO_PULSE_MAX_MS);
    float compare_val = pulse_ms * TIMER_PERIOD / TIMER_FREQ;
    return (uint32_t) compare_val;
}

/*
 * Each conversion function takes a mechanical angle as input,
 * saturates it within its mechanical limits, then maps it to the servo range.
 */

static const float rudder_mech_angles[11] = {
-35.00, -27.22, -19.44, -11.67, -3.89, 0.00, 3.89, 11.67, 19.44, 27.22, 35.00
};

static const float rudder_servo_angles[11] = {
160.06, 146.15, 134.51, 123.64, 112.98, 107.61, 102.19, 91.04, 79.27, 66.49, 51.98
};

float mech_to_servo_rudder(float mech_angle) {
    // Handle out-of-range cases by clamping to min/max
    if (mech_angle <= RUDDER_MIN_ANGLE) {
        return rudder_servo_angles[0];
    }
    if (mech_angle >= RUDDER_MAX_ANGLE) {
        return rudder_servo_angles[10];
    }
    
    // Find the two nearest points for interpolation
    for (int i = 0; i < (sizeof(rudder_mech_angles)/sizeof(rudder_mech_angles[0]) - 1); i++) {
        if (mech_angle >= rudder_mech_angles[i] && mech_angle <= rudder_mech_angles[i+1]) {
            // Linear interpolation
            float mech_range = rudder_mech_angles[i+1] - rudder_mech_angles[i];
            float servo_range = rudder_servo_angles[i+1] - rudder_servo_angles[i];
            float ratio = (mech_angle - rudder_mech_angles[i]) / mech_range;
            return rudder_servo_angles[i] + (ratio * servo_range);
        }
    }
    
    // Fallback: Find and return the servo angle corresponding to 0° mechanical rudder
    float zero_mech_angle = 0.0F;
    float smallest_diff = fabs(rudder_mech_angles[0] - zero_mech_angle);
    int zero_index = 0;
    
    for (int i = 1; i < sizeof(rudder_mech_angles)/sizeof(rudder_mech_angles[0]); i++) {
        float current_diff = fabs(rudder_mech_angles[i] - zero_mech_angle);
        if (current_diff < smallest_diff) {
            smallest_diff = current_diff;
            zero_index = i;
        }
    }
    
    return rudder_servo_angles[zero_index];  // Servo angle for closest to 0° rudder
}

float mech_to_servo_trim(float mech_angle) {
    float sat_angle = saturate(mech_angle, TRIM_MIN_ANGLE, TRIM_MAX_ANGLE);
    return map(sat_angle, TRIM_MIN_ANGLE, TRIM_MAX_ANGLE, TRIM_SERVO_MIN_ANGLE, TRIM_SERVO_MAX_ANGLE);
}

float mech_to_servo_twist(float mech_angle) {
    float sat_angle = saturate(mech_angle, TWIST_MIN_ANGLE, TWIST_MAX_ANGLE);
    return map(sat_angle, TWIST_MIN_ANGLE, TWIST_MAX_ANGLE, TWIST_SERVO_MIN_ANGLE, TWIST_SERVO_MAX_ANGLE);
}

float mech_to_servo_extra(float mech_angle) {
    float sat_angle = saturate(mech_angle, EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE);
    return map(sat_angle, EXTRA_MIN_ANGLE, EXTRA_MAX_ANGLE, EXTRA_SERVO_MIN_ANGLE, EXTRA_SERVO_MAX_ANGLE);
}

/*
 * Servo command functions: each one gets a desired mechanical angle,
 * converts it to a servo angle (with saturation), then sets the servo output.
 */
void set_servo_rudder(float mech_angle) {
    float servo_angle = mech_to_servo_rudder(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, RUDDER_SERVO_MIN_ANGLE, RUDDER_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, RUDDER_CHANNEL, pulse);
}

void set_servo_trim(float mech_angle) {
    float servo_angle = mech_to_servo_trim(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TRIM_SERVO_MIN_ANGLE, TRIM_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, TRIM_CHANNEL, pulse);
}

void set_servo_twist(float mech_angle) {
    float servo_angle = mech_to_servo_twist(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, TWIST_SERVO_MIN_ANGLE, TWIST_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, TWIST_CHANNEL, pulse);
}

void set_servo_extra(float mech_angle) {
    float servo_angle = mech_to_servo_extra(mech_angle);
    uint32_t pulse = servo_angle_to_pulse(servo_angle, EXTRA_SERVO_MIN_ANGLE, EXTRA_SERVO_MAX_ANGLE);
    __HAL_TIM_SET_COMPARE(&htim4, EXTRA_CHANNEL, pulse);
}
