#!/usr/bin/env python3
"""
Network utilities - Low level linux networking interface
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