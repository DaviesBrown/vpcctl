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
        return config_file.exists()

    def _add_vpc_isolation_rules(self, bridge_name):
        """
        Add iptables rules to isolate this VPC from other VPC bridges
        Block forwarding between different VPC bridges by default
        """
        # Get list of existing VPC bridges to block traffic to/from them
        existing_vpcs = self.list_vpcs()

        for vpc in existing_vpcs:
            other_bridge = vpc.get("bridge", f"br-{vpc['name']}")
            if other_bridge != bridge_name:
                # Block forwarding from this VPC to other VPCs
                self.network_utils.run_command(
                    f"iptables -I FORWARD -i {bridge_name} -o {other_bridge} -j DROP",
                    check=False
                )
                # Block forwarding from other VPCs to this VPC
                self.network_utils.run_command(
                    f"iptables -I FORWARD -i {other_bridge} -o {bridge_name} -j DROP",
                    check=False
                )
                self.logger.info(
                    f"Added isolation rules between {bridge_name} and {other_bridge}")

    def _remove_vpc_isolation_rules(self, bridge_name):
        """
        Remove iptables isolation rules for this VPC
        """
        # Remove rules blocking this bridge from/to other VPC bridges
        # We use -D to delete rules, with check=False to ignore if rule doesn't exist
        existing_vpcs = self.list_vpcs()

        for vpc in existing_vpcs:
            other_bridge = vpc.get("bridge", f"br-{vpc['name']}")
            if other_bridge != bridge_name:
                # Remove block from this VPC to other VPCs
                self.network_utils.run_command(
                    f"iptables -D FORWARD -i {bridge_name} -o {other_bridge} -j DROP",
                    check=False
                )
                # Remove block from other VPCs to this VPC
                self.network_utils.run_command(
                    f"iptables -D FORWARD -i {other_bridge} -o {bridge_name} -j DROP",
                    check=False
                )
                self.logger.debug(
                    f"Removed isolation rules between {bridge_name} and {other_bridge}")

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

        # Add isolation rules: block forwarding between this VPC and other VPCs
        # This ensures VPC isolation - traffic can only flow within the VPC
        # unless explicitly enabled via peering
        self._add_vpc_isolation_rules(bridge_name)

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

    def _load_vpc_config(self, vpc_name):
        """
        Loads the VPC config from json file
        """
        config_file = self.config_dir/f"{vpc_name}.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return None

    def delete_vpc(self, vpc_name):
        """
        Delete a VPC and cleanup all its resources
        """
        self.logger.info(f"Deleting VPC: {vpc_name}")
        if not self._vpc_exists(vpc_name):
            self.logger.warning(f"VPC {vpc_name} does not exist")
            return False

        vpc_config = self._load_vpc_config(vpc_name)
        bridge_name = vpc_config["bridge"]

        # Remove isolation rules for this VPC
        self._remove_vpc_isolation_rules(bridge_name)

        if vpc_config.get("nat_enabled"):
            internet_iface = vpc_config.get("internet_interface")
            public_subnet_cidrs = vpc_config.get("public_subnet_cidrs", [])
            if internet_iface and public_subnet_cidrs:
                self.network_utils.cleanup_nat_rules(
                    vpc_config["bridge"], internet_iface, public_subnet_cidrs)

        for subnet in vpc_config["subnets"]:
            subnet_name = subnet["name"]
            namespace = f"ns-{vpc_name}-{subnet_name}"
            self.network_utils.delete_network(namespace)

        bridge_name = vpc_config["bridge"]
        self.network_utils.delete_bridge(bridge_name)

        config_file = self.config_dir/f"{vpc_name}.json"
        config_file.unlink()
        self.logger.info(f"VPC {vpc_name} deleted successfully")
        return True

    def enable_nat_gateway(self, vpc_name, internet_interface):
        """
        Enable NAT gateway for VPC to allow public subnet internet access
        """
        self.logger.info(f"Enabling NAT gateway for VPC: {vpc_name}")
        vpc_config = self._load_vpc_config(vpc_name)
        if not vpc_config:
            self.logger.error(f"VPC {vpc_name} does not exist")
            return False

        bridge_name = vpc_config["bridge"]
        self.network_utils.enable_ip_forwarding()

        public_subnets = [s for s in vpc_config.get(
            "subnets", []) if s.get("type") == "public"]
        if not public_subnets:
            self.logger.warning(f"No public subnets found in VPC {vpc_name}")
            return False

        # Extract CIDRs of public subnets
        public_subnet_cidrs = [s["cidr"] for s in public_subnets]

        # Setup NAT only for public subnets
        self.network_utils.setup_nat(
            bridge_name, internet_interface, public_subnet_cidrs)
        self.logger.info(
            f"NAT enabled for public subnets: {', '.join(public_subnet_cidrs)}")

        vpc_config["nat_enabled"] = True
        vpc_config["internet_interface"] = internet_interface
        # Save for cleanup
        vpc_config["public_subnet_cidrs"] = public_subnet_cidrs
        self._save_vpc_config(vpc_name, vpc_config)
        self.logger.info(f"NAT gateway enabled for VPC {vpc_name}")
        return True

    def list_vpcs(self):
        """
        List all VPCs
        """
        vpcs = []
        for config_file in self.config_dir.glob("*.json"):
            with open(config_file) as f:
                vpc_config = json.load(f)
                vpcs.append({
                    "name": vpc_config["name"],
                    "cidr": vpc_config["cidr"],
                    "subnets": len(vpc_config.get("subnets", [])),
                    "nat_enabled": vpc_config.get("nat_enabled", False)
                })
        return vpcs

    def get_vpc_details(self, vpc_name):
        """
        Get detailed info about a VPC
        """
        return self._load_vpc_config(vpc_name)
