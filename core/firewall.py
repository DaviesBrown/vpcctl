#!/usr/bin/env python3

import logging
import json
from pathlib import Path
from utils.network_utils import NetworkUtils


class FirewallManager:

    def __init__(self):
        self.network_utils = NetworkUtils()
        self.logger = logging.getLogger('vpcctl')
        self.config_dir = Path("/tmp/vpc_config")

    def _get_vpc_config(self, vpc_name):
        config_file = self.config_dir/f"{vpc_name}.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return None

    def apply_firewall_rules(self, vpc_name, rules_file):
        self.logger.info(
            f"Applying firewall rules from {rules_file} to VPC {vpc_name}")

        vpc_config = self._get_vpc_config(vpc_name)
        if not vpc_config:
            self.logger.error(f"VPC {vpc_name} does not exist")
            return False

        with open(rules_file) as f:
            rules_config = json.load(f)

        subnet_cidr = rules_config.get("subnet")
        target_subnet = None

        for subnet in vpc_config.get("subnets", []):
            if subnet["cidr"] == subnet_cidr:
                target_subnet = subnet
                break

        if not target_subnet:
            self.logger.error(
                f"Subnet {subnet_cidr} not found in VPC {vpc_name}")
            return False

        namespace = target_subnet["namespace"]

        for rule in rules_config.get("ingress", []):
            self.network_utils.apply_firewall_rule(namespace, rule)

        self.logger.info(f"Firewall rules applied to subnet {subnet_cidr}")
        return True

    def apply_subnet_rules(self, vpc_name, subnet_name, rules):
        self.logger.info(
            f"Applying firewall rules to subnet {subnet_name} in VPC {vpc_name}")

        vpc_config = self._get_vpc_config(vpc_name)
        if not vpc_config:
            self.logger.error(f"VPC {vpc_name} does not exist")
            return False

        target_subnet = None
        for subnet in vpc_config.get("subnets", []):
            if subnet["name"] == subnet_name:
                target_subnet = subnet
                break

        if not target_subnet:
            self.logger.error(
                f"Subnet {subnet_name} not found in VPC {vpc_name}")
            return False

        namespace = target_subnet["namespace"]

        for rule in rules:
            self.network_utils.apply_firewall_rule(namespace, rule)

        self.logger.info(f"Firewall rules applied to subnet {subnet_name}")
        return True
