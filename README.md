# com.ov.ros2 — Orbit ROS2 Bridge Extension

Isaac Sim extension that bridges the Orbit Framework's `OrbitService` to ROS2 Jazzy via DDS topics.

## Requirements

- Ubuntu 24.04 (Might work on Ubuntu 22.04 [not tested yet])
- Isaac Sim 5.1
- ROS2 Jazzy
- Docker
- `com.ov.core` extension

## Setup

### 1. Clone and build the ROS2 workspace
```bash
git clone https://github.com/sangregoriokimpo/IsaacSim-5.1-ROS2_workspace.git
cd IsaacSim-5.1-ROS2_workspace
./build_ros.sh -d jazzy -v 24.04
```

> Note: The build script uses Docker to compile the workspace against Python 3.11 as required by Isaac Sim 5.1. This may take 10-15 minutes on the first run.

### 2. Register the extension in Isaac Sim

- Open Isaac Sim
- Go to **Window → Extensions → (gear icon) → Extension Search Paths**
- Add the path to the `exts` folder of this repository

### 3. Launch Isaac Sim with the workspace sourced

Source the built workspace before launching Isaac Sim so the extension can find `orbit_interfaces`:
```bash
source ~/IsaacSim-5.1-ROS2_workspace/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
~/isaacsim/isaac-sim.sh
```

> This must be done every session, or add the source line to your `~/.bashrc` to make it permanent.

### 4. Enable extensions in order

In the Isaac Sim Extension Manager, enable in this order:

1. `isaacsim.ros2.bridge`
2. `com.ov.core`
3. `com.ov.ros2`

## Topics

| Topic | Type | Direction |
|---|---|---|
| `/orbit/thrust_cmd` | `orbit_interfaces/ThrustCmd` | Subscribe |
| `/orbit/state` | `orbit_interfaces/OrbitState` | Publish |

## Verify

Open a new terminal and run:
```bash
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-5.1-ROS2_workspace/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
ros2 topic list
```

You should see `/orbit/thrust_cmd` and `/orbit/state`.

Send a test thrust command:
```bash
ros2 topic pub /orbit/thrust_cmd orbit_interfaces/msg/ThrustCmd \
  "{body_id: '/World/Cube', throttle: 0.5, gimbal_pitch: 0.0, gimbal_yaw: 0.0}"
```

## Notes

- `rclpy.init()` and `rclpy.shutdown()` are managed by `isaacsim.ros2.bridge` — do not call them manually.
- The workspace must be sourced in the same terminal used to launch Isaac Sim so that `AMENT_PREFIX_PATH` is set correctly.
- `ThrustVectorModel` is auto-created on the first `ThrustCmd` received for a body using default parameters (`max_thrust=10N`, `mass=5kg`, `max_gimbal=15deg`). These can be adjusted in `extension.py`.