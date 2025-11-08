#!/usr/bin/env python3
"""
Network utilities - Low level linux networking interface
This is where we run the ip, iptables and bridge commands
"""

import subprocess
import shlex
import logging


class NetworkUtils:
    """
    Handles all the direct linux networking commands
    """
    
    def __init__(self):
        self.logger = logging.getLogger('vpcctl')
    
    def run_command(self, command, check=True):
        """
        Run a shell command and handle errors
        """
        self.logger.debug(f"Running command: {command}")
        try:
            split_commands = shlex.split(command)
            result = subprocess.run(
                split_commands,
                check=check,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {command}")
            self.logger.error(f"Error: {e.stderr}")
            raise

    def create_bridge(self, bridge_name):
        """
        Create a linux bridge - (Router Implementation)
        """
        self.logger.info(f"Creating bridge: {bridge_name}")
        self.run_command(f"ip link add {bridge_name} type bridge")
        self.run_command(f"ip link set {bridge_name} up")
        self.logger.info(f"Bridge {bridge_name} create and activated")

    def delete_bridge(self, bridge_name):
        """
        Deletes a linux bridge
        """
        self.logger.info(f"Deleting bridge: {bridge_name}")
        self.run_command(f"ip link set {bridge_name} down", check=False)
        self.run_command(f"ip link delete {bridge_name}", check=False)
        self.logger.info(f"Bridge {bridge_name} deleted successfully")

    def create_network(self, namespace):
        """
        Create a network namespace - (Subnet Implementation)
        """
        self.logger.info(f"Creating network namespace: {namespace}")
        self.run_command(f"ip netns add {namespace}")
        self.logger.info(f"Created network namespace: {namespace}")

    def delete_network(self, namespace):
        """
        Delete a network namespace
        """
        self.logger.info(f"Deleting network namespace: {namespace}")
        self.run_command(f"ip netns delete {namespace}")
        self.logger.info(f"Deleted network namespace: {namespace}")

    def run_in_namespace(self, namespace, command):
        """
        Run a command inside a specific namespace
        """
        self.logger.info(f"Running in network namespace: {namespace}")
        full_command = f"ip netns exec {namespace} {command}"
        return self.run_command(full_command)