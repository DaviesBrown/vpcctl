#!/usr/bin/env python3
"""
VPC Manager - Handles VPC lifecycle (create, delete, manage)
A VPC is like a virtual datacenter with its own network
"""

import json
import logging
from pathlib import Path
from utils.network_utils import NetworkUtils


class VPCManager:
    """
    Manages Virtual Private Cloud
    """

    def __init__(self):
        self.network_utils = NetworkUtils()
        self.config_dir = Path("/tmp/vpc_config")
        self.logger = logging.getLogger('vpcctl')
        self.config_dir.mkdir(exist_ok=True)