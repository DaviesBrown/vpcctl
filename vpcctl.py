#!/usr/bin/env python3

import argparse
import logging
import sys
from core.vpc import VPCManager
from core.subnets import SubnetManager
from core.peering import PeeringManager
from core.firewall import FirewallManager
from utils.network_utils import NetworkUtils


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_vpc(args):
    vpc_manager = VPCManager()
    if vpc_manager.create_vpc(args.name, args.cidr):
        print(
            f"✓ VPC '{args.name}' created successfully with CIDR {args.cidr}")
        return 0
    return 1


def delete_vpc(args):
    vpc_manager = VPCManager()
    if vpc_manager.delete_vpc(args.name):
        print(f"✓ VPC '{args.name}' deleted successfully")
        return 0
    return 1


def list_vpcs(args):
    vpc_manager = VPCManager()
    vpcs = vpc_manager.list_vpcs()
    if vpcs:
        print(f"\n{'VPC Name':<20} {'CIDR':<20} {'Subnets':<10} {'NAT':<10}")
        print("-" * 60)
        for vpc in vpcs:
            nat_status = "Enabled" if vpc['nat_enabled'] else "Disabled"
            print(
                f"{vpc['name']:<20} {vpc['cidr']:<20} {vpc['subnets']:<10} {nat_status:<10}")
    else:
        print("No VPCs found")
    return 0


def show_vpc(args):
    vpc_manager = VPCManager()
    vpc = vpc_manager.get_vpc_details(args.name)
    if vpc:
        print(f"\nVPC: {vpc['name']}")
        print(f"CIDR: {vpc['cidr']}")
        print(f"Bridge: {vpc['bridge']}")
        print(f"NAT: {'Enabled' if vpc.get('nat_enabled') else 'Disabled'}")
        print(f"\nSubnets ({len(vpc.get('subnets', []))}):")
        for subnet in vpc.get('subnets', []):
            print(
                f"  - {subnet['name']} ({subnet['cidr']}) - {subnet['type']}")
        return 0
    print(f"VPC '{args.name}' not found")
    return 1


def add_subnet(args):
    subnet_manager = SubnetManager()
    if subnet_manager.create_subnet(args.vpc, args.name, args.cidr, args.type):
        print(f"✓ Subnet '{args.name}' added to VPC '{args.vpc}'")
        return 0
    return 1


def enable_nat(args):
    vpc_manager = VPCManager()
    if vpc_manager.enable_nat_gateway(args.vpc, args.interface):
        print(f"✓ NAT gateway enabled for VPC '{args.vpc}'")
        return 0
    return 1


def create_peering(args):
    peering_manager = PeeringManager()
    if peering_manager.create_peering(args.vpc1, args.vpc2):
        print(f"✓ Peering created between '{args.vpc1}' and '{args.vpc2}'")
        return 0
    return 1


def delete_peering(args):
    peering_manager = PeeringManager()
    if peering_manager.delete_peering(args.vpc1, args.vpc2):
        print(f"✓ Peering deleted between '{args.vpc1}' and '{args.vpc2}'")
        return 0
    return 1


def apply_firewall(args):
    firewall_manager = FirewallManager()
    if firewall_manager.apply_firewall_rules(args.vpc, args.rules):
        print(f"✓ Firewall rules applied to VPC '{args.vpc}'")
        return 0
    return 1


def exec_in_subnet(args):
    network_utils = NetworkUtils()
    namespace = f"ns-{args.vpc}-{args.subnet}"
    try:
        output = network_utils.run_in_namespace(namespace, args.command)
        print(output)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='VPC Control Tool - Manage Virtual Private Clouds on Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')

    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    create_vpc_parser = subparsers.add_parser(
        'create-vpc', help='Create a new VPC')
    create_vpc_parser.add_argument('name', help='VPC name')
    create_vpc_parser.add_argument(
        'cidr', help='CIDR block (e.g., 10.0.0.0/16)')
    create_vpc_parser.set_defaults(func=create_vpc)

    delete_vpc_parser = subparsers.add_parser(
        'delete-vpc', help='Delete a VPC')
    delete_vpc_parser.add_argument('name', help='VPC name')
    delete_vpc_parser.set_defaults(func=delete_vpc)

    list_vpcs_parser = subparsers.add_parser('list-vpcs', help='List all VPCs')
    list_vpcs_parser.set_defaults(func=list_vpcs)

    show_vpc_parser = subparsers.add_parser(
        'show-vpc', help='Show VPC details')
    show_vpc_parser.add_argument('name', help='VPC name')
    show_vpc_parser.set_defaults(func=show_vpc)

    add_subnet_parser = subparsers.add_parser(
        'add-subnet', help='Add a subnet to VPC')
    add_subnet_parser.add_argument('vpc', help='VPC name')
    add_subnet_parser.add_argument('name', help='Subnet name')
    add_subnet_parser.add_argument(
        'cidr', help='Subnet CIDR (e.g., 10.0.1.0/24)')
    add_subnet_parser.add_argument(
        '--type', choices=['public', 'private'], default='private', help='Subnet type')
    add_subnet_parser.set_defaults(func=add_subnet)

    enable_nat_parser = subparsers.add_parser(
        'enable-nat', help='Enable NAT gateway for VPC')
    enable_nat_parser.add_argument('vpc', help='VPC name')
    enable_nat_parser.add_argument(
        '--interface', default='eth0', help='Internet interface (default: eth0)')
    enable_nat_parser.set_defaults(func=enable_nat)

    create_peering_parser = subparsers.add_parser(
        'create-peering', help='Create VPC peering')
    create_peering_parser.add_argument('vpc1', help='First VPC name')
    create_peering_parser.add_argument('vpc2', help='Second VPC name')
    create_peering_parser.set_defaults(func=create_peering)

    delete_peering_parser = subparsers.add_parser(
        'delete-peering', help='Delete VPC peering')
    delete_peering_parser.add_argument('vpc1', help='First VPC name')
    delete_peering_parser.add_argument('vpc2', help='Second VPC name')
    delete_peering_parser.set_defaults(func=delete_peering)

    apply_firewall_parser = subparsers.add_parser(
        'apply-firewall', help='Apply firewall rules')
    apply_firewall_parser.add_argument('vpc', help='VPC name')
    apply_firewall_parser.add_argument(
        'rules', help='Path to firewall rules JSON file')
    apply_firewall_parser.set_defaults(func=apply_firewall)

    exec_parser = subparsers.add_parser(
        'exec', help='Execute command in subnet namespace')
    exec_parser.add_argument('vpc', help='VPC name')
    exec_parser.add_argument('subnet', help='Subnet name')
    exec_parser.add_argument('command', help='Command to execute')
    exec_parser.set_defaults(func=exec_in_subnet)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging(args.verbose)

    try:
        return args.func(args)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
