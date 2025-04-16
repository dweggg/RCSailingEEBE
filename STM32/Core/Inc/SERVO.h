/*
 * SERVO.h
 *
 *  Created on: Mar 30, 2025
 *      Author: dweggg
 */

#ifndef SERVO_H_
#define SERVO_H_

#include <stdint.h>

// Define hardware-specific timer channel assignments (adjust as needed).
#define RUDDER_CHANNEL    TIM_CHANNEL_1
#define TRIM_CHANNEL      TIM_CHANNEL_2
#define TWIST_CHANNEL     TIM_CHANNEL_3
#define EXTRA_CHANNEL     TIM_CHANNEL_4

// Mechanical limits (in degrees) for each control surface.
#define RUDDER_MIN_ANGLE    -35.0F
#define RUDDER_MAX_ANGLE    35.0F

#define TRIM_MIN_ANGLE      -180.0F
#define TRIM_MAX_ANGLE      180.0F

#define TWIST_MIN_ANGLE     0.0F
#define TWIST_MAX_ANGLE     45.0F

#define EXTRA_MIN_ANGLE     0.0F
#define EXTRA_MAX_ANGLE     180.0F

// Servo conversion limits (defines how the mechanical angle maps to servo angle).
#define RUDDER_SERVO_RANGE    180.0F
#define TRIM_SERVO_RANGE      1800.0F
#define TWIST_SERVO_RANGE     180.0F
#define EXTRA_SERVO_RANGE     180.0F

// Functions that actually command the servo outputs.
void set_servo_rudder(float mech_angle);
void set_servo_trim(float mech_angle);
void set_servo_twist(float mech_angle);
void set_servo_extra(float mech_angle);

void disable_all_servos(void);

#endif /* SERVO_H_ */
