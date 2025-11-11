# VPC CLI - Virtual Private Cloud Manager for Linux

A powerful CLI tool to create and manage Virtual Private Clouds (VPCs) on Linux using native networking primitives like network namespaces, veth pairs, bridges, and iptables.

## Architecture

```
VPC (Bridge) → Connects Multiple Subnets
│
├── Subnet 1 (Namespace) → veth pair → Bridge
├── Subnet 2 (Namespace) → veth pair → Bridge
└── NAT Gateway → Internet Access for Public Subnets
```

Each VPC is implemented as a Linux bridge, and each subnet is a network namespace connected via veth pairs.

## Requirements

- Linux OS with root access (or WSL2 on Windows)
- Python 3.6+
- iproute2 (`ip` command)
- iptables

**WSL2 Note**: This tool works on WSL2. You may see ICMP redirect messages during ping tests - these are normal and don't affect functionality.

Check requirements:
```bash
sudo python3 tests/check_requirements.py
```

## Installation

```bash
git clone <your-repo-url>
cd vpc-cli
chmod +x vpcctl.py cleanup.sh tests/*.sh
```

## Usage

### Create a VPC

```bash
sudo python3 vpcctl.py create-vpc <vpc-name> <cidr-block>
```

Example:
```bash
sudo python3 vpcctl.py create-vpc prod-vpc 10.0.0.0/16
```

### Add Subnets

```bash
sudo python3 vpcctl.py add-subnet <vpc-name> <subnet-name> <subnet-cidr> [--type public|private]
```

Examples:
```bash
sudo python3 vpcctl.py add-subnet prod-vpc web-subnet 10.0.1.0/24 --type public
sudo python3 vpcctl.py add-subnet prod-vpc db-subnet 10.0.2.0/24 --type private
```

### Enable NAT Gateway

```bash
sudo python3 vpcctl.py enable-nat <vpc-name> [--interface eth0]
```

Example:
```bash
sudo python3 vpcctl.py enable-nat prod-vpc --interface eth0
```

### List VPCs

```bash
sudo python3 vpcctl.py list-vpcs
```

### Show VPC Details

```bash
sudo python3 vpcctl.py show-vpc <vpc-name>
```

### VPC Peering

```bash
sudo python3 vpcctl.py create-peering <vpc1-name> <vpc2-name>
sudo python3 vpcctl.py delete-peering <vpc1-name> <vpc2-name>
```

### Apply Firewall Rules

Create a firewall rules JSON file:
```json
{
  "subnet": "10.0.1.0/24",
  "ingress": [
    {"port": 80, "protocol": "tcp", "action": "allow"},
    {"port": 443, "protocol": "tcp", "action": "allow"},
    {"port": 22, "protocol": "tcp", "action": "deny"}
  ]
}
```

Apply rules:
```bash
sudo python3 vpcctl.py apply-firewall <vpc-name> <rules-file.json>
```

### Execute Commands in Subnet

```bash
sudo python3 vpcctl.py exec <vpc-name> <subnet-name> "<command>"
```

Examples:
```bash
sudo python3 vpcctl.py exec prod-vpc web-subnet "ip addr"
sudo python3 vpcctl.py exec prod-vpc web-subnet "ping -c 3 8.8.8.8"
sudo python3 vpcctl.py exec prod-vpc web-subnet "python3 -m http.server 8080"
```

### Delete VPC

```bash
sudo python3 vpcctl.py delete-vpc <vpc-name>
```

## Quick Demo

Run the quick demo:
```bash
sudo ./tests/demo.sh
```

## Application Deployment Demo

Deploy a web server in a VPC:
```bash
sudo ./tests/demo_app.sh
```

This demonstrates:
- Web server deployment (Python HTTP server on port 8080)
- Ping and curl tests to verify the server
- Internet access via NAT gateway
- Complete VPC networking setup

## Complete Test Suite

Run comprehensive tests:
```bash
sudo ./tests/test_vpc.sh
```

This will test:
- VPC creation
- Subnet creation (public and private)
- NAT gateway
- Inter-subnet communication
- VPC isolation
- VPC peering
- Firewall rules
- Web server deployment and curl tests
- Internet connectivity

## Cleanup

Clean up all VPCs and resources:
```bash
sudo ./cleanup.sh
```

## Project Structure

```
vpc-cli/
├── vpcctl.py              # Main CLI entry point
├── core/
│   ├── vpc.py            # VPC management
│   ├── subnets.py        # Subnet management
│   ├── peering.py        # VPC peering
│   └── firewall.py       # Firewall rules
├── utils/
│   └── network_utils.py  # Low-level networking
├── tests/
│   ├── test_vpc.sh       # Comprehensive tests
│   ├── demo.sh           # Quick demo
│   ├── demo_app.sh       # Web server deployment demo
│   └── check_requirements.py
├── config/
│   └── firewall_rules.json
├── cleanup.sh
└── README.md
```

## How It Works

### VPC Creation
1. Creates a Linux bridge (acts as VPC router)
2. Brings up the bridge interface
3. Saves VPC configuration to `/tmp/vpc_config/`

### Subnet Creation
1. Creates a network namespace (isolated network)
2. Creates a veth pair (virtual ethernet cable)
3. Connects one end to the bridge
4. Moves other end into the namespace
5. Assigns IP addresses
6. Sets up routing

### NAT Gateway
1. Enables IP forwarding on host
2. Adds MASQUERADE rule for outbound traffic
3. Adds FORWARD rules for bi-directional traffic

### VPC Peering
1. Creates veth pair between VPC bridges
2. Adds static routes for cross-VPC communication
3. Enables selective inter-VPC connectivity

### Firewall Rules
1. Applies iptables rules within namespaces
2. Controls ingress/egress traffic
3. Port and protocol-based filtering

## Testing Scenarios

### Test 1: Inter-Subnet Communication
```bash
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 3 10.0.2.2"
```

### Test 2: Internet Access
```bash
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 3 8.8.8.8"
sudo python3 vpcctl.py exec vpc-test private-subnet "ping -c 3 8.8.8.8"
```

### Test 3: VPC Isolation
```bash
sudo python3 vpcctl.py create-vpc vpc1 10.0.0.0/16
sudo python3 vpcctl.py create-vpc vpc2 10.1.0.0/16
sudo python3 vpcctl.py exec vpc1 subnet1 "ping -c 3 10.1.1.2"
```

### Test 4: VPC Peering
```bash
sudo python3 vpcctl.py create-peering vpc1 vpc2
sudo python3 vpcctl.py exec vpc1 subnet1 "ping -c 3 10.1.1.2"
```

## Troubleshooting

### Check if VPC exists
```bash
sudo python3 vpcctl.py list-vpcs
```

### Check bridge status
```bash
ip link show | grep br-
```

### Check namespaces
```bash
ip netns list
```

### Check routes in namespace
```bash
sudo ip netns exec ns-<vpc>-<subnet> ip route
```

### Check iptables rules
```bash
sudo iptables -t nat -L -n -v
sudo iptables -L FORWARD -n -v
```

### View logs
```bash
sudo python3 vpcctl.py -v <command>
```
