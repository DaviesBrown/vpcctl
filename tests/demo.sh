#!/bin/bash

echo "VPC CLI - Quick Demo"
echo "===================="
echo ""

echo "1. Create VPC"
sudo python3 vpcctl.py create-vpc demo-vpc 172.16.0.0/16

echo ""
echo "2. Add public subnet"
sudo python3 vpcctl.py add-subnet demo-vpc web 172.16.1.0/24 --type public

echo ""
echo "3. Add private subnet"
sudo python3 vpcctl.py add-subnet demo-vpc db 172.16.2.0/24 --type private

echo ""
echo "4. Enable NAT"
sudo python3 vpcctl.py enable-nat demo-vpc --interface eth0

echo ""
echo "5. Show VPC details"
sudo python3 vpcctl.py show-vpc demo-vpc

echo ""
echo "6. Test ping between subnets"
echo "Testing connectivity from web subnet (172.16.1.2) to db subnet (172.16.2.2)..."
sudo python3 vpcctl.py exec demo-vpc web "ping -c 3 172.16.2.2" 2>&1 | grep -E "(transmitted|icmp_seq=|rtt min)" || sudo python3 vpcctl.py exec demo-vpc web "ping -c 3 172.16.2.2"

echo ""
echo "Demo complete! To cleanup: sudo python3 vpcctl.py delete-vpc demo-vpc"
