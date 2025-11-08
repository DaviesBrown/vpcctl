#!/usr/bin/env python3
"""
Subnet Manager - Handles subnet creation within VPCs
Subnets are isolated network segments within a VPC
"""

import logging
from utils.network_utils import NetworkUtils

class SubnetManager:
    """
    Manages subnets within VPCs
    """

    def __init__(self):
        self.network_utils = NetworkUtils
        self.logger = logging.getLogger('vpcctl')
        