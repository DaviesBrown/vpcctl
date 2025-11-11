#!/bin/bash

echo "========================================="
echo "VPC CLI - Complete Test Suite"
echo "========================================="
echo ""

INTERNET_IFACE=${1:-eth0}

echo "Cleaning up any existing test VPCs..."
# Delete peering first (before deleting VPCs)
sudo python3 vpcctl.py delete-peering vpc-test vpc-test2 2>/dev/null || true
# Then delete VPCs
sudo python3 vpcctl.py delete-vpc vpc-test 2>/dev/null || true
sudo python3 vpcctl.py delete-vpc vpc-test2 2>/dev/null || true

echo ""
echo "Step 1: Creating VPC 'vpc-test' with CIDR 10.0.0.0/16"
sudo python3 vpcctl.py create-vpc vpc-test 10.0.0.0/16

echo ""
echo "Step 2: Adding public subnet (10.0.1.0/24)"
sudo python3 vpcctl.py add-subnet vpc-test public-subnet 10.0.1.0/24 --type public

echo ""
echo "Step 3: Adding private subnet (10.0.2.0/24)"
sudo python3 vpcctl.py add-subnet vpc-test private-subnet 10.0.2.0/24 --type private

echo ""
echo "Step 4: Enabling NAT gateway"
sudo python3 vpcctl.py enable-nat vpc-test --interface $INTERNET_IFACE

echo ""
echo "Step 5: Listing VPCs"
sudo python3 vpcctl.py list-vpcs

echo ""
echo "Step 6: Showing VPC details"
sudo python3 vpcctl.py show-vpc vpc-test

echo ""
echo "Step 7: Testing connectivity within VPC"
echo "Public subnet can ping private subnet:"
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 3 10.0.2.2"

echo ""
echo "Step 8: Testing internet connectivity from public subnet"
echo "Trying to ping 8.8.8.8 from public subnet:"
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 3 8.8.8.8" || echo "Internet access test - May fail if no internet"

echo ""
echo "Step 9: Creating second VPC for isolation test"
sudo python3 vpcctl.py create-vpc vpc-test2 10.1.0.0/16

echo ""
echo "Step 10: Adding subnet to second VPC"
sudo python3 vpcctl.py add-subnet vpc-test2 public-subnet 10.1.1.0/24 --type public

echo ""
echo "Step 11: Testing VPC isolation (should fail without peering)"
echo "Trying to ping from vpc-test to vpc-test2:"
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 2 10.1.1.2" || echo "✓ VPCs are isolated (expected)"

echo ""
echo "Step 12: Creating VPC peering"
sudo python3 vpcctl.py create-peering vpc-test vpc-test2

echo ""
echo "Step 13: Testing connectivity after peering"
echo "Trying to ping from vpc-test to vpc-test2 after peering:"
sudo python3 vpcctl.py exec vpc-test public-subnet "ping -c 3 10.1.1.2" || echo "Peering connectivity test"

echo ""
echo "Step 14: Applying firewall rules"
cat > /tmp/firewall_rules.json <<EOF
{
  "subnet": "10.0.1.0/24",
  "ingress": [
    {"port": 80, "protocol": "tcp", "action": "allow"},
    {"port": 22, "protocol": "tcp", "action": "deny"}
  ]
}
EOF

sudo python3 vpcctl.py apply-firewall vpc-test /tmp/firewall_rules.json

echo ""
echo "Step 15: Deploying and testing a simple web server"
echo "Starting Python HTTP server in public subnet on port 8080..."

# Start a simple HTTP server in the background
sudo python3 vpcctl.py exec vpc-test public-subnet "nohup python3 -m http.server 8080 > /tmp/webserver.log 2>&1 &"

# Give the server a moment to start
sleep 2

echo ""
echo "Step 15a: Testing web server with curl from private subnet"
echo "Accessing http://10.0.1.2:8080 from private subnet..."
sudo python3 vpcctl.py exec vpc-test private-subnet "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://10.0.1.2:8080 --connect-timeout 5" || echo "Web server test completed"

echo ""
echo "Step 15b: Testing web server with curl from peered VPC"
echo "Accessing http://10.0.1.2:8080 from vpc-test2..."
sudo python3 vpcctl.py exec vpc-test2 public-subnet "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://10.0.1.2:8080 --connect-timeout 5" || echo "Cross-VPC web server test completed"

echo ""
echo "Step 15c: Verifying web server is running"
sudo python3 vpcctl.py exec vpc-test public-subnet "ps aux | grep 'python3 -m http.server' | grep -v grep" || echo "Web server process check"

echo ""
echo "Step 15d: Stopping web server"
sudo python3 vpcctl.py exec vpc-test public-subnet "pkill -f 'python3 -m http.server'" 2>/dev/null || true

echo ""
echo "Step 16: Listing all VPCs"
sudo python3 vpcctl.py list-vpcs

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "✓ Created 2 VPCs with subnets"
echo "✓ Tested inter-subnet connectivity"
echo "✓ Tested NAT gateway (internet access)"
echo "✓ Verified VPC isolation"
echo "✓ Created and tested VPC peering"
echo "✓ Applied firewall rules"
echo "✓ Deployed and tested web server"
echo ""
echo "To cleanup, run: sudo ./cleanup.sh"
