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

    def create_network(self):
        """"""