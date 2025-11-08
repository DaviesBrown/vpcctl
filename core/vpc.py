#!/usr/bin/env python3
"""
VPC Manager - Handles VPC lifecycle (create, delete, manage)
A VPC is like a virtual datacenter with its own network
"""

import json
import logging
from datetime import datetime
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

    def _save_vpc_config(self, vpc_name, config):
        """
        Save VPC config to a json file
        """
        config_file = self.config_dir/f"{vpc_name}.json"
        with open(config_file, 'w') as f:
            json.dump(config, fp=f, indent=2)

    def _vpc_exists(self, vpc_name):
        """
        Check if a VPC already exists
        """
        config_file = self.config_dir/f"{vpc_name}.json"

    def create_vpc(self, vpc_name, cidr_block):
        """
        Create an new VPC with a bridge as the central router
        - vpc_name: Name of datacenter
        - cidr_block: The IP range for this datacenter (e.g. 10.0.0.0/16)
        - bridge: the main router that connects everything
        """
        self.logger.info(f"Creating VPC: {vpc_name} with CIDR: {cidr_block}")
        if self._vpc_exists(vpc_name):
            self.logger.warning(f"VPC {vpc_name} already exists")
            return False
        
        bridge_name = f"br-{vpc_name}"
        self.network_utils.create_bridge(bridge_name=bridge_name)
        vpc_config = {
            "name": vpc_name,
            "cidr": cidr_block,
            "bridge": bridge_name,
            "subnets": [],
            "created_at": datetime.now().isoformat()
        }

        self._save_vpc_config(vpc_name, vpc_config)
        self.logger.info(f"VPC {vpc_name} created successfully")
        return True
    
