#!/usr/bin/env python3

import logging
import json
import ipaddress
from pathlib import Path
from utils.network_utils import NetworkUtils


class SubnetManager:

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

    def _save_vpc_config(self, vpc_name, config):
        config_file = self.config_dir/f"{vpc_name}.json"
        with open(config_file, 'w') as f:
            json.dump(config, fp=f, indent=2)

    def _get_gateway_ip(self, subnet_cidr):
        network = ipaddress.ip_network(subnet_cidr)
        return str(list(network.hosts())[0])

    def _get_subnet_ip(self, subnet_cidr):
        network = ipaddress.ip_network(subnet_cidr)
        return str(list(network.hosts())[1])

    def create_subnet(self, vpc_name, subnet_name, subnet_cidr, subnet_type="private"):
        vpc_config = self._get_vpc_config(vpc_name)
        if not vpc_config:
            self.logger.error(f"VPC {vpc_name} does not exist")
            return False

        for subnet in vpc_config.get("subnets", []):
            if subnet["name"] == subnet_name:
                self.logger.warning(
                    f"Subnet {subnet_name} already exists in VPC {vpc_name}")
                return False

        self.logger.info(f"Creating subnet {subnet_name} in VPC {vpc_name}")
        namespace = f"ns-{vpc_name}-{subnet_name}"

        import hashlib
        unique_id = hashlib.md5(
            f"{vpc_name}-{subnet_name}".encode()).hexdigest()[:4]
        veth_ns = f"v{unique_id}n"
        veth_br = f"v{unique_id}b"

        self.network_utils.create_network(namespace)
        self.network_utils.create_veth_pair(veth_ns, veth_br)
        self.network_utils.attach_to_bridge(vpc_config["bridge"], veth_br)
        self.network_utils.move_to_namespace(veth_ns, namespace)

        gateway_ip = self._get_gateway_ip(subnet_cidr)
        subnet_ip = self._get_subnet_ip(subnet_cidr)

        self.network_utils.set_ip_address(
            namespace, veth_ns, f"{subnet_ip}/{subnet_cidr.split('/')[1]}")

        self.network_utils.set_bridge_ip(
            vpc_config["bridge"], f"{gateway_ip}/{subnet_cidr.split('/')[1]}")

        # IP forwarding is now handled at VPC level when NAT is enabled
        # self.network_utils.enable_ip_forwarding()  # REMOVE THIS LINE

        self.network_utils.add_default_route(namespace, gateway_ip)
        self.network_utils.run_in_namespace(namespace, "ip link set lo up")

        subnet_config = {
            "name": subnet_name,
            "cidr": subnet_cidr,
            "type": subnet_type,
            "namespace": namespace,
            "veth_ns": veth_ns,
            "veth_br": veth_br,
            "gateway": gateway_ip,
            "ip": subnet_ip
        }

        vpc_config["subnets"].append(subnet_config)
        self._save_vpc_config(vpc_name, vpc_config)
        self.logger.info(f"Subnet {subnet_name} created successfully")
        return True
