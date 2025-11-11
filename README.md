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

Deploy a complete 3-tier application (web, app, database):
```bash
sudo ./tests/demo_app.sh
```

This demonstrates:
- Web server in public subnet (port 80)
- Application server in private subnet (port 8080)
- Database server in isolated subnet (port 5432)
- Tier-to-tier connectivity (web → app → db)
- Internet access for public tier
- Security isolation between tiers

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
│   ├── demo_app.sh       # 3-tier app deployment demo
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
:dart: Objectives
By the end of this stage, you should be able to:
Create and manage virtual VPCs on a single Linux host.
Provision multiple subnets (network namespaces) connected by a Linux bridge.
Enable routing between subnets within a VPC.
Implement NAT gateway behavior for public subnets to access the internet.
Demonstrate VPC-level isolation e.g one VPC cannot reach another.
Implement optional VPC peering to allow controlled inter-VPC traffic.
Enforce firewall rules (Security Groups) at subnet or VPC level.
Automate all this with a custom CLI tool called (vpcctl) written in Bash or Python.
:hammer_and_spanner: Task Breakdown
Part 1: Core VPC Creation
Implement a CLI tool called vpcctl capable of:
Creating a new VPC with a specified CIDR range.
Adding subnets (e.g., public and private) under that VPC with unique CIDRs.
Connecting subnets to a central Linux bridge that functions as the VPC router.
Assigning IP ranges and configuring routing logic automatically.
Deleting a VPC
Each subnet should be implemented as a network namespace. Use veth pairs to connect subnets to a Linux bridge that acts as the router. Assign unique IP ranges to each subnet and configure routing tables automatically.
Part 2: Routing and NAT Gateway
Design your routing layer so packets can move between subnets within a VPC through the bridge interface.
Configure NAT behavior on the appropriate interface to simulate an internet gateway.
Validate that:
Subnets within a VPC can communicate with each other.
Public subnets have outbound internet access.
Private subnets remain internal-only unless explicitly routed through a public gateway.
Part 3: VPC Isolation & Peering
Support multiple independent VPCs with non-overlapping address ranges.
Deploy test workloads (e.g., simple web servers) inside the public subnet of each VPC to validate connectivity. Implement optional peering that should connect bridges with a veth pair and add static routes to enable cross-VPC communication.
Show that:
Workloads within the same VPC can reach each other as expected.
Workloads in different VPCs cannot communicate without an explicit peering connection.
Once peering is established, only defined subnets or CIDRs can exchange traffic across VPCs.
Part 4: Firewall & Security Groups
Implement firewall rules using  iptables inside namespaces to simulate security groups:
Implement a JSON-based policy file for subnet rules so they can be dynamically applied.
Example:
{
  "subnet": "10.0.1.0/24",
  "ingress": [
    {"port": 80, "protocol": "tcp", "action": "allow"},
    {"port": 22, "protocol": "tcp", "action": "deny"}
  ]
}
Demonstrate that traffic obeys your defined access rules for example, blocking a specific port or protocol between subnets.
Part 5: Cleanup & Automation
Provide lifecycle automation that supports clean creation, inspection, and deletion of VPCs.
On deletion, ensure that all resources like namespaces, veth pairs, bridges, and firewall rules  are properly removed.
The CLI should be idempotent, meaning multiple create/delete operations should not break or duplicate resources.
All actions should be logged or printed clearly to show what’s being configured or removed.
:clipboard: Requirements
Variable ------- Description
VPC_NAME ------- Unique name for the virtual VPC
CIDR_BLOCK ------- Base IP range (e.g. 10.0.0.0/16)
PUBLIC_SUBNET ------- Subnet that allows NAT access
PRIVATE_SUBNET ------- Subnet without internet access
INTERNET_INTERFACE ------- Host’s outbound network interface
CLI should be written in Python, or Bash.
Must rely only on Linux native networking tools (ip, iptables, bridge, etc.).
No third-party libraries for network virtualization.
Output must clearly log actions (creation, linking, IP assignment, routing).
:white_tick: Acceptance Criteria
Test ----------------- Expected Result
Create a VPC ----------------- Virtual networks are created with bridges, namespaces, and internal connectivity.
Add Subnets ----------------- Each subnet has correct CIDR assignment and communication within the VPC.
Deploy App in Public Subnet ----------------- Application is reachable from host or designated public zone.
Deploy App in Private Subnet ----------------- Application remains unreachable externally.
Multiple VPCs ----------------- VPCs are fully isolated by default.
VPC Peering ----------------- After peering, controlled communication works across VPCs.
NAT Gateway ----------------- Public subnets have outbound access; private subnets do not.
Firewall Enforcement ----------------- Rules block or allow traffic according to policy definitions.
Teardown ----------------- All VPC components (namespaces, bridges, veth, firewall rules) are removed cleanly.
:brain: Demonstration Tests (Video)
You’ll validate your design by deploying simple web servers or similar workloads inside your subnets.
Your tests should prove:
Scenario  -----------------  Expected Behavior
Communication between subnets in the same VPC -----------------  Works successfully.
Outbound access from public subnet ----------------- Works successfully.
Outbound access from private subnet ----------------- Blocked or restricted.
Communication between different VPCs ----------------- Blocked by default.
Communication after peering ----------------- Allowed where explicitly configured.
Policy enforcement ----------------- Specific connections blocked as defined.
Logging ----------------- Logs should show all your vpc activities up to cleanup.
Focus on showing behavior and outcomes rather than individual commands.
:open_file_folder: Submission Requirements
1. GitHub Repository including:
The complete vpcctl CLI implementation (Python or Bash).
Optional Makefile or automation script for quick setup.
A cleanup script to tear down all virtual networks.
2.  A published blog post that a beginner can follow through to complete the project containing:
Overview of the project.
CLI usage examples and explanations.
Architecture diagram showing VPC → bridge → subnets → gateway.
Testing and validation steps (connectivity, NAT, isolation).
Testing steps (connectivity, NAT, isolation)
A clean up step for deleting resources after creation.
3.  A screen recording of 5 mins maximum showing a full workthrough of your task requirements, tests and expected outcomes.
N/B: Screen recording should include timestamps, descriptive labels, and visible context. Avoid cropped or partial evidence.
:white_tick: Minimum for a Valid Submission
A working VPC CLI that creates subnets and routes between them
At least one app deployed and verified through ping/curl tests
Demonstrated VPC isolation (no inter-VPC communication without peering)
Verified NAT behavior for public vs private subnet
Clean teardown (no orphaned namespaces or bridges)
Logs to show all vpc activities performed.
Repository and screenshots properly submitted
