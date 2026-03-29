import sys
from pathlib import Path
import os
import math
import omni.ext
import omni.kit.app

from com.ov.core.service import get_orbit_service
from com.ov.core.thrust_model import ThrustVectorModel

'''
CHANGE THIS FILE PATH FOR WHATEVER PROJECT YOU WANT TO APPLY THIS TO

THIS HAS BEEN SET FOR THE SSTI / VIX MUTO PROJECT AT SIERRA LOBO INC
'''

for prefix in os.environ.get("AMENT_PREFIX_PATH", "").split(":"):
    site = Path(prefix) / "lib/python3.11/site-packages"
    if site.exists() and str(site) not in sys.path:
        sys.path.insert(0, str(site))

class OrbitROS2Extension(omni.ext.IExt):

    THRUST_MAX_N      = 10.0
    THRUST_MASS_KG    = 5.0
    THRUST_GIMBAL_RAD = math.radians(15.0)

    def on_startup(self, ext_id: str):
        import rclpy
        self._rclpy = rclpy
        self._svc   = get_orbit_service()

        # rclpy.init(args=None)
        # self._node = self._build_node()
        self._node = self._build_node()

        self._update_sub = (
            omni.kit.app.get_app()
            .get_update_event_stream()
            .create_subscription_to_pop(self._spin)
        )
        print("[OrbitROS2] started")

    def on_shutdown(self):
        if self._update_sub:
            self._update_sub.unsubscribe()
            self._update_sub = None
        self._node.destroy_node()
        # self._rclpy.shutdown()
        print("[OrbitROS2] shutdown")

    def _spin(self, _e):
        self._rclpy.spin_once(self._node, timeout_sec=0.0)

    def _build_node(self):
        from rclpy.node import Node
        from orbit_interfaces.msg import ThrustCmd, OrbitState
        svc      = self._svc
        defaults = (self.THRUST_MAX_N, self.THRUST_MASS_KG, self.THRUST_GIMBAL_RAD)

        class _Bridge(Node):
            def __init__(self):
                super().__init__("orbit_ros2_bridge")
                self.create_subscription(
                    ThrustCmd, "/orbit/thrust_cmd", self._on_cmd, 10
                )
                self._pub = self.create_publisher(OrbitState, "/orbit/state", 10)
                self.create_timer(1.0 / 30.0, self._publish)

            def _on_cmd(self, msg: ThrustCmd):
                body = svc.get_body(msg.body_id)
                if body is None:
                    return
                if body.thrust_model is None:
                    max_n, mass, gimbal = defaults
                    body.thrust_model = ThrustVectorModel(
                        max_thrust_N=max_n,
                        mass_kg=mass,
                        max_gimbal_rad=gimbal,
                    )
                svc.set_thrust_cmd(
                    msg.body_id,
                    float(msg.throttle),
                    float(msg.gimbal_pitch),
                    float(msg.gimbal_yaw),
                )

            def _publish(self):
                for path in svc.list_bodies():
                    body = svc.get_body(path)
                    if not body:
                        continue
                    s = OrbitState()
                    s.header.stamp = self.get_clock().now().to_msg()
                    s.header.frame_id = "world"
                    s.body_id = path
                    s.position.x, s.position.y, s.position.z = body.r
                    s.velocity.x, s.velocity.y, s.velocity.z = body.v
                    w, x, y, z = body.attitude_quat
                    s.attitude.w = w
                    s.attitude.x = x
                    s.attitude.y = y
                    s.attitude.z = z
                    self._pub.publish(s)

        return _Bridge()