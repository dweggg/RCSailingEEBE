import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# ---------------------------------------------------------------------
# PARAMETERS (all lengths in meters)
# ---------------------------------------------------------------------
servo_arm = -21/1000.0    # Servo arm length (negative for crossed bar configuration)
pushrod   = 200/1000.0    # Rudder pivot location (global)
rudder_arm = 30/1000.0    # Rudder arm length
delta_rudder = np.radians(-90)  # Rudder offset angle (shifts travel to ±90°)

# Servo angle limits (in degrees)
min_servo_angle = 10
max_servo_angle = 170

# Number of points in the LUT
NUM_POINTS = 10

# ---------------------------------------------------------------------
# FUNCTION: Compute Rudder Angle from Servo Angle via the Linkage
# ---------------------------------------------------------------------
def solve_theta_r(theta_s):
    """
    Given a servo angle (theta_s, in radians), compute the resulting rudder angle (theta_r, in radians)
    by solving the nonlinear equation:
    
       (servo_arm*cos(theta_s) - (pushrod + rudder_arm*cos(theta_r)))^2 +
       (servo_arm*sin(theta_s) - rudder_arm*sin(theta_r))^2 = pushrod**2
       
    The computed theta_r is then offset by delta_rudder so that the rudder travels
    with both positive and negative angles.
    """
    def f(theta_r):
        return (servo_arm * np.cos(theta_s) - (pushrod + rudder_arm * np.cos(theta_r)))**2 + \
               (servo_arm * np.sin(theta_s) - rudder_arm * np.sin(theta_r))**2 - pushrod**2

    ts = np.linspace(0, np.pi, 300)
    vals = np.abs(f(ts))
    guess = ts[np.argmin(vals)]
    sol = fsolve(f, guess)[0]
    sol_clipped = np.clip(sol, 0, np.pi)
    return sol_clipped + delta_rudder

# ---------------------------------------------------------------------
# Compute the Mapping over a Fine Grid of Servo Angles
# ---------------------------------------------------------------------
servo_angles_rad = np.linspace(np.radians(min_servo_angle), np.radians(max_servo_angle), 300)
rudder_angles_rad = np.array([solve_theta_r(theta_s) for theta_s in servo_angles_rad])

# Convert to degrees.
servo_angles_deg = np.degrees(servo_angles_rad)
rudder_angles_deg = np.degrees(rudder_angles_rad)

# For the LUT mapping (assuming monotonicity), sort by rudder angle.
sort_idx = np.argsort(rudder_angles_deg)
rudder_mech = rudder_angles_deg[sort_idx]
rudder_servo = servo_angles_deg[sort_idx]

# ---------------------------------------------------------------------
# Determine the Symmetric Rudder Limits Using Servo Endpoints
# ---------------------------------------------------------------------
r_at_min = solve_theta_r(np.radians(min_servo_angle))
r_at_max = solve_theta_r(np.radians(max_servo_angle))
orig_min = np.degrees(r_at_min)
orig_max = np.degrees(r_at_max)

# Determine the symmetric limit from the smaller absolute extreme, then floor to the nearest 5°.
abs_limit = min(abs(orig_min), abs(orig_max))
limit = 5 * np.floor(abs_limit / 5.0)
angle_min = -limit
angle_max = limit

# ---------------------------------------------------------------------
# Build the LUT (ensuring 0° is included)
# ---------------------------------------------------------------------
# Create LUT points that span from angle_min to angle_max.
sample_mech = np.linspace(angle_min, angle_max, NUM_POINTS)

# Ensure 0° is in the LUT
if 0 not in sample_mech:
    sample_mech = np.append(sample_mech, 0)

# Sort to maintain order
sample_mech = np.sort(sample_mech)

# Compute corresponding servo angles
sample_servo = np.interp(sample_mech, rudder_mech, rudder_servo)

# ---------------------------------------------------------------------
# Output the LUT as C arrays and print the symmetric limits.
# ---------------------------------------------------------------------
print("static const float rudder_mech_angles[{}] = {{".format(len(sample_mech)))
print(", ".join("{:.2f}".format(val) for val in sample_mech))
print("};\n")

print("static const float rudder_servo_angles[{}] = {{".format(len(sample_servo)))
print(", ".join("{:.2f}".format(val) for val in sample_servo))
print("};\n")

print("// Additional marker for zero rudder angle:")
print("static const float rudder_zero_servo_angle = {:.2f};\n".format(np.interp(0, rudder_mech, rudder_servo)))

print("// Symmetric rudder limits (floored to nearest 5°)")
print("static const float angle_min = {:.2f};".format(angle_min))
print("static const float angle_max = {:.2f};".format(angle_max))
print("static const float limit = {:.2f};".format(limit))

# ---------------------------------------------------------------------
# Plot the Mapping (only for rudder angles between angle_min and angle_max)
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))

# Clip the full mapping to the symmetric limits.
mask = (rudder_angles_deg >= angle_min) & (rudder_angles_deg <= angle_max)
clipped_servo_angles = servo_angles_deg[mask]
clipped_rudder_angles = rudder_angles_deg[mask]

# Plot the clipped mapping.
ax.plot(clipped_servo_angles, clipped_rudder_angles, label="Servo vs Rudder Angle", color='purple')

# Mark the computed rudder endpoints based on the servo endpoints.
ax.scatter(min_servo_angle, orig_min, color='green', zorder=5,
           label="Rudder at {}° Servo".format(min_servo_angle))
ax.scatter(max_servo_angle, orig_max, color='blue', zorder=5,
           label="Rudder at {}° Servo".format(max_servo_angle))

# Mark zero rudder angle.
ax.scatter(np.interp(0, rudder_mech, rudder_servo), 0, color='orange', zorder=5, label="Zero Rudder")
ax.text(np.interp(0, rudder_mech, rudder_servo) + 2, 0, "0°", fontsize=10, color='orange')

# Draw horizontal lines for the symmetric limits.
ax.axhline(angle_min, color='gray', linestyle='--', label="Symmetric Limits")
ax.axhline(angle_max, color='gray', linestyle='--')

# Add text labels for symmetric limits.
ax.text(servo_angles_deg[-1] - 20, angle_max + 1, f"{angle_max:.0f}°", fontsize=10, color='gray')
ax.text(servo_angles_deg[-1] - 20, angle_min - 3, f"{angle_min:.0f}°", fontsize=10, color='gray')

# Plot the sampled LUT points.
ax.scatter(sample_servo, sample_mech, color='red', zorder=5, label="LUT Points")

# Labels, title, and grid.
ax.set_xlabel("Servo Angle (°)")
ax.set_ylabel("Rudder Angle (°)")
ax.set_title("Servo vs Rudder Angle (clipped to symmetric limits, 0° included)")
ax.grid()
ax.legend()

plt.show()
