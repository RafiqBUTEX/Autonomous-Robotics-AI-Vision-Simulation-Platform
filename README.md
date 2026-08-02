# Autonomous Robotics, AI, Vision & Simulation Platform

A simulated autonomous vehicle built in Gazebo/ROS2, integrating custom-trained computer vision, RGB-D 3D localization, LiDAR, SLAM-based mapping, Nav2 autonomous navigation, and a Unity-based digital twin dashboard for live monitoring and teleoperation.

## Overview

This project investigates the full perception-to-autonomy pipeline for a simulated ground vehicle:

1. Perception - dual RGB cameras (front/rear), a depth camera, and a 360 degree LiDAR
2. Object detection - a YOLOv8 model, fine-tuned on an auto-labeled synthetic dataset after the pretrained model failed to correctly classify the simulated environment's objects
3. Localization - RGB-D fusion for real-world distance estimation and 3D object localization in RViz
4. Mapping - live SLAM (slam_toolbox) using LiDAR and odometry
5. Navigation - autonomous goal-based path planning and obstacle avoidance (Nav2)
6. Digital twin - a Unity dashboard mirroring the simulated vehicle in real time, with live camera feeds, detection results, and bidirectional teleoperation, connected via ROS-TCP-Connector

## Key finding: sim-to-real domain gap

A pretrained YOLOv8n model, evaluated on the simulation's plain synthetic objects, consistently misclassified them (for example a cone identified as "stop sign", confidence under 0.4). To address this, an automated labeling pipeline was built: using each object's known world-frame position, the vehicle's live odometry, and camera intrinsics, 2D bounding boxes were computed and projected without any manual annotation. A YOLOv8 model fine-tuned on this dataset reached an mAP50 of 0.845 (cone 0.995, can 0.995, cube 0.546), correctly classifying objects the pretrained model could not.

## Repository structure

urdf/ - vehicle description
worlds/ - custom Gazebo world
src/car_perception/ - ROS2 detection and mapping package
config/ - SLAM and Nav2 parameter overrides
dataset/ - auto-labeled training data
custom_models/ - downloaded Gazebo model assets
custom_yolo.pt - fine-tuned detection model weights

## Tech stack

ROS2 Humble, Gazebo Classic, RViz, Unity3D, YOLOv8, Python, C#, ROS-TCP-Connector, slam_toolbox, Nav2, URDF
