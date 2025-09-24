#!/bin/bash

# Script to increase inotify limits for Streamlit deployment
# Run this script with sudo privileges on your Linux server

echo "Current inotify limits:"
echo "max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
echo "max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"

# Increase the limits
echo "Increasing inotify limits..."
echo 1024 > /proc/sys/fs/inotify/max_user_instances
echo 524288 > /proc/sys/fs/inotify/max_user_watches

echo "New inotify limits:"
echo "max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
echo "max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"

echo "Inotify limits updated successfully!"
