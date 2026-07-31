#!/usr/bin/env python3

import rclpy

from ros.topic_capture import TopicCapture


def main():

    rclpy.init()

    node = TopicCapture()

    topics = node.discover_topics()

    print()

    print("Application Topics")

    print("------------------")

    for topic in topics:

        print(

            f"{topic['name']:30s} {topic['type']}"

        )

    print()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":

    main()
