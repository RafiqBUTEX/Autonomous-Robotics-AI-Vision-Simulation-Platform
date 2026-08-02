from setuptools import find_packages, setup

package_name = 'car_perception'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rafiq',
    maintainer_email='rafiq.butex1438@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'frame_grabber = car_perception.frame_grabber:main',
            'yolo_detector = car_perception.yolo_detector:main',
            'simple_teleop = car_perception.simple_teleop:main',
            'yolo_distance = car_perception.yolo_distance:main',
            'yolo_3d_markers = car_perception.yolo_3d_markers:main',
            'yolo_detector_rear = car_perception.yolo_detector_rear:main',
                'dataset_collector = car_perception.dataset_collector:main',
        ],
    },
)
