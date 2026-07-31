#!/usr/bin/env python3

from ros.topic_database import TopicDatabase
from scheduler.admission_controller import AdmissionController
from routing.forwarding_engine import ForwardingEngine


db = TopicDatabase()

db.update_topic("/camera_front", "sensor_msgs/msg/Image")
db.update_topic("/camera_rear", "sensor_msgs/msg/Image")
db.update_topic("/imu", "sensor_msgs/msg/Imu")
db.update_topic("/odom", "nav_msgs/msg/Odometry")
db.update_topic("/debug", "std_msgs/msg/String")


db.set_priority("/imu", 1)
db.set_priority("/odom", 2)
db.set_priority("/camera_front", 2)
db.set_priority("/camera_rear", 3)
db.set_priority("/debug", 5)


db.set_bandwidth("/imu", 2)
db.set_bandwidth("/odom", 3)
db.set_bandwidth("/camera_front", 180)
db.set_bandwidth("/camera_rear", 220)
db.set_bandwidth("/debug", 60)


controller = AdmissionController(db)

controller.evaluate(250)

controller.print_status()

engine = ForwardingEngine(db)

engine.print_forwarding_list()
