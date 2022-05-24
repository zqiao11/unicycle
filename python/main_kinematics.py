# MAIN

import numpy as np

from kinematics.pid_kinematics import PID
from kinematics.dnn_kinematics import DNN
from kinematics.inverse_kinematics import Inverse
from kinematics.unicycle_kinematics import Unicycle
from utils.save_data import save_data_kinematics
from utils.show import show_plots, show_animation

# Parameters

collect_data = False  # True - collect data, False - test performance
controller = 2  # 0 - random, 1 - PID, 2 - DNN, 3 - inverse
online_learning = True  # For DNN (controller = 2): True - enable online learning, False - disable online learning
trajectory = 1  # 0 - random points, 1 - circular, 2 - 8-shaped, 3 - set-point, 4 - square-wave
uncertainty = 1  # internal uncertainty: 0 - no uncertainty, 1 - all parameters double, -1 - all parameters half;
# default = 1
disturbance = -2  # external disturbance: 0 - no disturbance, >0 - positive disturbance, <0 - negative disturbance
# default = -2
noise = 0  # measurement noise standard deviation: 0 - no noise, >0 - white noise
# default = 0.01

animation = False  # True - enable online animation, False - disable online animation

k_end = 10000
dt = 0.001

if collect_data:
    controller = 0
    online_learning = False
    trajectory = 0
    uncertainty = 0
    disturbance = 0
    noise = 0
    k_end = 1000000

# Initial pose

x_init = 0
y_init = 0
yaw_init = 0

# Initialise arrays

pose = np.zeros((k_end + 1, 3))
pose[0, :] = [x_init, y_init, yaw_init]
pose_real = np.zeros((k_end + 1, 3))
pose_real[0, :] = [x_init, y_init, yaw_init]
command = np.zeros((k_end + 1, 2))
command_random = np.zeros((k_end + 1, 2))
command_pid = np.zeros((k_end + 1, 2))
command_dnn = np.zeros((k_end + 1, 2))
command_inverse = np.zeros((k_end + 1, 2))
t = np.linspace(0, dt * k_end, num=(k_end + 1))

# Generate trajectory

if trajectory == 0:  # random points (for collecting training data)
    reference = np.random.randn(k_end + 1, 3)
if trajectory == 1:  # circular
    reference = np.column_stack([2 * np.cos(2 * t), -2 * np.sin(2 * t), np.zeros((k_end + 1, 1))])
if trajectory == 2:  # 8-shaped
    reference = np.column_stack([
        4 / (3 - np.cos(2 * t)) * np.cos(t),
        4 / (3 - np.cos(2 * t)) * np.sin(-2 * t) / np.sqrt(2),
        np.zeros((k_end + 1, 1))])
if trajectory == 3:  # set-point
    reference = np.column_stack([2 * np.ones((k_end + 1, 1)), -2 * np.ones((k_end + 1, 1)), np.zeros((k_end + 1, 1))])
if trajectory == 4:  # square-wave
    d = np.fix(t)
    d = d % 4
    b1 = np.fix(d / 2)
    b0 = d - 2 * b1
    reference = np.column_stack([b1, b0, np.zeros((k_end + 1, 1))])

unicycle = Unicycle(dt, [x_init, y_init, yaw_init])

pid = PID(dt)
dnn = DNN(dt, 'dnn_kinematics_32x32')
inverse = Inverse(unicycle)

# Main loop

for k in range(1, k_end - 1):

    # Unicycle control
    if collect_data:
        command_random[k, :] = np.random.uniform(-10, 10, 2)
    else:
        command_pid[k, :] = pid.control(pose[k, :], reference[k, :])
        command_dnn[k, :] = dnn.control(pose[k, :], reference[k + 1, :])
        if online_learning and k > 0:
            dnn.learn(pose[k, :], pose[k - 1, :], command[k - 1, :])
        command_inverse[k, :] = inverse.control(pose[k, :], reference[k + 1, :])

    if controller == 0:
        command[k, :] = command_random[k, :]
    else:
        if controller == 1:
            command[k, :] = command_pid[k, :]
        else:
            if controller == 2:
                command[k, :] = command_dnn[k, :]
            else:
                if controller == 3:
                    command[k, :] = command_inverse[k, :]

    # Simulate unicycle
    if k < k_end / 2:
        pose[k + 1, :], pose_real[k + 1, :] = unicycle.simulate(command[k, :], 0, 0, noise)
    else:
        pose[k + 1, :], pose_real[k + 1, :] = unicycle.simulate(command[k, :], uncertainty, disturbance, noise)

    # Animation
    if animation:
        show_animation(pose[:k + 1], reference[:k + 1])

# Save results

if collect_data:
    save_data_kinematics(t, reference, pose, command, 'unicycle_kinematics_random')

# Plot results

if not collect_data:
    show_plots(t, pose_real, reference, command, command_dnn, command_inverse)
