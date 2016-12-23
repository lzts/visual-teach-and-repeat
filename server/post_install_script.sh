#!/bin/sh

USERNAME=robmob
HOSTNAME="$1"
IP="$2"


if [ "$(whoami)" != "root" ]; then
    echo "This script must be run as root."
    exit 1
fi

if [ "$1" = "--help"]; then
    echo "usage: post_install_script.sh HOSTNAME IP"
    exit 0
fi

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "usage: post_install_script.sh HOSTNAME IP"
    exit 1
fi


# ROS INSTALL

echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list

apt-key adv --keyserver hkp://ha.pool.sks-keyservers.net --recv-key 0xB01FA116

apt-get update

apt-get install -y --force-yes \
        htop \
        nload \
        openssh-server \
        python-twisted \
        ros-indigo-compressed-depth-image-transport \
        ros-indigo-compressed-image-transport \
        ros-indigo-freenect-launch \
        ros-indigo-hokuyo-node \
        ros-indigo-image-transport-plugins \
        ros-indigo-kobuki-core \
        ros-indigo-kobuki-node \
        ros-indigo-robot-upstart \
        ros-indigo-ros-base \
        ros-indigo-rosbridge-suite \
        vim \
        wget

rosdep init
su -c "rosdep update" $USERNAME

su -c "echo \"source /opt/ros/indigo/setup.bash\" >> /home/$USERNAME/.bashrc" $USERNAME
source /opt/ros/indigo/setup.bash


# UDEV rules for the kobuki and the hokuyo.

echo "SUBSYSTEMS==\"tty\", KERNEL==\"ttyACM[0-9]*\", ACTION==\"add\", MODE=\"0666\", GROUP=\"dialout\"" > /etc/udev/rules.d/99-hokuyo.rules


# Configure robot_upstart

curl -sSf https://raw.githubusercontent.com/davidlandry93/glo4001/master/server/robmob.launch > /opt/ros/indigo/share/kobuki_node/launch/robmob.launch
