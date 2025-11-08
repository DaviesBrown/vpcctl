:rocket: DevOps Intern Stage 4 Task → Build Your Own Virtual Private Cloud (VPC) on Linux
Linux Networking, Isolation, and Routing from First Principles
Hey Cool Keeds! :wave:
:magnifying_glass_right: Overview
In this stage, you’ll recreate the fundamentals of a VPC entirely on Linux. Using primitives like network namespaces, veth pairs, bridges, routing tables, and iptables, you’ll architect and automate a mini VPC environment that supports subnets, routing, NAT, and isolation  just like a Cloud VPC does under the hood.
You’ll then deploy simple web servers (e.g., Nginx or Python HTTP) into your “subnets” to demonstrate network isolation, routing between subnets, and controlled access across VPCs.
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
