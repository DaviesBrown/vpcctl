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
        self.run_command(f"ip netns delete {namespace}", check=False)
        self.logger.info(f"Deleted network namespace: {namespace}")

    def run_in_namespace(self, namespace, command, check=True):
        """
        Run a command inside a specific namespace
        Commands with shell features (pipes, redirects, &&, etc.) need shell=True
        """
        self.logger.info(f"Running in network namespace: {namespace}")

        # Check if command has shell features that require sh -c
        shell_features = ['&&', '||', '|', '>',
                          '<', '&', ';', 'nohup', '$(', '`']
        needs_shell = any(feature in command for feature in shell_features)

        try:
            if needs_shell:
                # For complex commands, use sh -c through ip netns exec
                full_command = ['ip', 'netns', 'exec',
                                namespace, 'sh', '-c', command]
                result = subprocess.run(
                    full_command,
                    check=check,
                    capture_output=True,
                    text=True
                )
                return result.stdout
            else:
                # For simple commands, use the regular method
                full_command = f"ip netns exec {namespace} {command}"
                return self.run_command(full_command, check=check)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {command}")
            self.logger.error(f"Error: {e.stderr}")
            raise

    def create_veth_pair(self, veth1, veth2):
        """
        Create a veth pair to connect namespaces
        """
        self.logger.info(f"Creating veth pair: {veth1}, {veth2}")

        # Check if veth pair already exists
        try:
            self.run_command(f"ip link show {veth1}", check=True)
            self.logger.warning(
                f"Veth pair {veth1} already exists, reusing it")
            # Make sure both ends are up
            self.run_command(f"ip link set {veth1} up", check=False)
            self.run_command(f"ip link set {veth2} up", check=False)
            return
        except:
            # Veth doesn't exist, create it
            pass

        self.run_command(f"ip link add {veth1} type veth peer name {veth2}")
        self.run_command(f"ip link set {veth1} up")
        self.run_command(f"ip link set {veth2} up")
        self.logger.info(f"Created veth pair: {veth1}, {veth2}")

    def attach_to_bridge(self, bridge_name, interface):
        """
        Attach an interface to a bridge
        """
        self.logger.info(f"Attaching {interface} to bridge {bridge_name}")
        self.run_command(f"ip link set {interface} master {bridge_name}")

    def move_to_namespace(self, interface, namespace):
        """
        Move an interface to a network namespace
        """
        self.logger.info(f"Moving {interface} to namespace {namespace}")
        self.run_command(f"ip link set {interface} netns {namespace}")

    def set_ip_address(self, namespace, interface, ip_address):
        """
        Set IP address on interface in namespace
        """
        self.logger.info(
            f"Setting IP {ip_address} on {interface} in {namespace}")
        self.run_in_namespace(
            namespace, f"ip addr add {ip_address} dev {interface}")
        self.run_in_namespace(namespace, f"ip link set {interface} up")

    def set_bridge_ip(self, bridge_name, ip_address):
        """
        Set IP address on bridge
        Bridges can have multiple IPs (one per subnet), so we use 'ip addr add'
        """
        self.logger.info(f"Setting IP {ip_address} on bridge {bridge_name}")
        # Use check=False to avoid errors if IP already exists
        self.run_command(
            f"ip addr add {ip_address} dev {bridge_name}", check=False)

    def add_default_route(self, namespace, gateway_ip):
        """
        Add default route in namespace
        """
        self.logger.info(
            f"Adding default route via {gateway_ip} in {namespace}")
        # First try to delete existing default route (if any)
        self.run_in_namespace(
            namespace, f"ip route del default", check=False)
        self.run_in_namespace(
            namespace, f"ip route add default via {gateway_ip}")

    def enable_ip_forwarding(self):
        """
        Enable IP forwarding on host
        """
        self.logger.info("Enabling IP forwarding")
        self.run_command("sysctl -w net.ipv4.ip_forward=1")

    def setup_nat(self, bridge_name, internet_interface, public_subnet_cidrs):
        """
        Setup NAT for outbound traffic from specific public subnets only
        Private subnets will not have internet access
        """
        self.logger.info(
            f"Setting up NAT for public subnets to {internet_interface}")
        self.enable_ip_forwarding()

        # Setup NAT rules for each public subnet CIDR
        for cidr in public_subnet_cidrs:
            self.logger.info(f"Setting up NAT for public subnet {cidr}")
            # NAT only traffic from this specific public subnet
            self.run_command(
                f"iptables -t nat -A POSTROUTING -s {cidr} -o {internet_interface} -j MASQUERADE"
            )
            # Allow forwarding only from this specific public subnet
            self.run_command(
                f"iptables -A FORWARD -i {bridge_name} -s {cidr} -o {internet_interface} -j ACCEPT"
            )

        # Allow ALL return traffic from internet to bridge (for established connections)
        # This is safe because it only allows RELATED,ESTABLISHED traffic
        self.run_command(
            f"iptables -A FORWARD -i {internet_interface} -o {bridge_name} -m state --state RELATED,ESTABLISHED -j ACCEPT"
        )

    def add_route(self, namespace, destination, gateway):
        """
        Add a route in namespace
        """
        self.logger.info(
            f"Adding route to {destination} via {gateway} in {namespace}")
        self.run_in_namespace(
            namespace, f"ip route add {destination} via {gateway}")

    def apply_firewall_rule(self, namespace, rule):
        """
        Apply iptables firewall rule in namespace
        """
        protocol = rule.get('protocol', 'tcp')
        port = rule.get('port')
        action = rule.get('action', 'allow').upper()

        if action == 'ALLOW':
            target = 'ACCEPT'
        elif action == 'DENY':
            target = 'DROP'
        else:
            target = action

        if port:
            rule_cmd = f"iptables -A INPUT -p {protocol} --dport {port} -j {target}"
        else:
            rule_cmd = f"iptables -A INPUT -p {protocol} -j {target}"

        self.logger.info(f"Applying firewall rule in {namespace}: {rule_cmd}")
        self.run_in_namespace(namespace, rule_cmd)

    def cleanup_nat_rules(self, bridge_name, internet_interface, public_subnet_cidrs):
        """
        Cleanup NAT rules for public subnets
        """
        self.logger.info(f"Cleaning up NAT rules for {bridge_name}")

        # Clean up rules for each public subnet
        for cidr in public_subnet_cidrs:
            self.run_command(
                f"iptables -t nat -D POSTROUTING -s {cidr} -o {internet_interface} -j MASQUERADE",
                check=False
            )
            self.run_command(
                f"iptables -D FORWARD -s {cidr} -i {bridge_name} -o {internet_interface} -j ACCEPT",
                check=False
            )
            self.run_command(
                f"iptables -D FORWARD -d {cidr} -i {internet_interface} -o {bridge_name} -m state --state RELATED,ESTABLISHED -j ACCEPT",
                check=False
            )
