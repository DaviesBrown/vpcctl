#!/usr/bin/env python3

import logging
import json
from pathlib import Path
from utils.network_utils import NetworkUtils


class PeeringManager:

    def __init__(self):
        self.network_utils = NetworkUtils()
        self.logger = logging.getLogger('vpcctl')
        self.config_dir = Path("/tmp/vpc_config")
        self.peering_dir = Path("/tmp/vpc_peering")
        self.peering_dir.mkdir(exist_ok=True)

    def _get_vpc_config(self, vpc_name):
        config_file = self.config_dir/f"{vpc_name}.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return None

    def _save_peering_config(self, peering_id, config):
        config_file = self.peering_dir/f"{peering_id}.json"
        with open(config_file, 'w') as f:
            json.dump(config, fp=f, indent=2)

    def _peering_exists(self, vpc1, vpc2):
        peering_id1 = f"{vpc1}-{vpc2}"
        peering_id2 = f"{vpc2}-{vpc1}"
        return (self.peering_dir/f"{peering_id1}.json").exists() or \
               (self.peering_dir/f"{peering_id2}.json").exists()

    def create_peering(self, vpc1_name, vpc2_name):
        self.logger.info(
            f"Creating peering between {vpc1_name} and {vpc2_name}")

        if self._peering_exists(vpc1_name, vpc2_name):
            self.logger.warning(
                f"Peering already exists between {vpc1_name} and {vpc2_name}")
            return False

        vpc1_config = self._get_vpc_config(vpc1_name)
        vpc2_config = self._get_vpc_config(vpc2_name)

        if not vpc1_config or not vpc2_config:
            self.logger.error("One or both VPCs do not exist")
            return False

        veth1 = f"peer-{vpc1_name}"
        veth2 = f"peer-{vpc2_name}"

        self.network_utils.create_veth_pair(veth1, veth2)
        self.network_utils.attach_to_bridge(vpc1_config["bridge"], veth1)
        self.network_utils.attach_to_bridge(vpc2_config["bridge"], veth2)

        for subnet in vpc2_config.get("subnets", []):
            gateway_ip = vpc1_config.get("subnets", [{}])[0].get(
                "gateway") if vpc1_config.get("subnets") else None
            if gateway_ip:
                try:
                    self.network_utils.run_command(
                        f"ip route add {subnet['cidr']} via {gateway_ip} dev {vpc1_config['bridge']}",
                        check=False
                    )
                except:
                    pass

        for subnet in vpc1_config.get("subnets", []):
            gateway_ip = vpc2_config.get("subnets", [{}])[0].get(
                "gateway") if vpc2_config.get("subnets") else None
            if gateway_ip:
                try:
                    self.network_utils.run_command(
                        f"ip route add {subnet['cidr']} via {gateway_ip} dev {vpc2_config['bridge']}",
                        check=False
                    )
                except:
                    pass

        peering_id = f"{vpc1_name}-{vpc2_name}"
        peering_config = {
            "vpc1": vpc1_name,
            "vpc2": vpc2_name,
            "veth1": veth1,
            "veth2": veth2
        }

        self._save_peering_config(peering_id, peering_config)
        self.logger.info(
            f"Peering created between {vpc1_name} and {vpc2_name}")
        return True

    def delete_peering(self, vpc1_name, vpc2_name):
        self.logger.info(
            f"Deleting peering between {vpc1_name} and {vpc2_name}")

        peering_id1 = f"{vpc1_name}-{vpc2_name}"
        peering_id2 = f"{vpc2_name}-{vpc1_name}"

        config_file = None
        if (self.peering_dir/f"{peering_id1}.json").exists():
            config_file = self.peering_dir/f"{peering_id1}.json"
        elif (self.peering_dir/f"{peering_id2}.json").exists():
            config_file = self.peering_dir/f"{peering_id2}.json"

        if not config_file:
            self.logger.warning("Peering does not exist")
            return False

        config_file.unlink()
        self.logger.info(
            f"Peering deleted between {vpc1_name} and {vpc2_name}")
        return True
