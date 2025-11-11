#!/bin/bash

echo "========================================="
echo "VPC CLI - Cleanup Script"
echo "========================================="
echo ""

echo "Cleaning up all VPC peering connections..."
if [ -d "/tmp/vpc_peering" ]; then
    for peering_file in /tmp/vpc_peering/*.json; do
        if [ -f "$peering_file" ]; then
            # Extract VPC names from filename (format: vpc1-vpc2.json)
            basename=$(basename "$peering_file" .json)
            vpc1=$(echo "$basename" | cut -d'-' -f1)
            vpc2=$(echo "$basename" | cut -d'-' -f2-)
            echo "Deleting peering: $vpc1 <-> $vpc2"
            sudo python3 vpcctl.py delete-peering "$vpc1" "$vpc2" 2>/dev/null || true
        fi
    done
else
    echo "No peering directory found"
fi

echo ""
echo "Deleting test VPCs..."
sudo python3 vpcctl.py delete-vpc vpc-test 2>/dev/null || echo "VPC vpc-test not found"

echo ""
echo "Deleting VPC 'vpc-test2'..."
sudo python3 vpcctl.py delete-vpc vpc-test2 2>/dev/null || echo "VPC vpc-test2 not found"

echo ""
echo "Deleting demo VPC..."
sudo python3 vpcctl.py delete-vpc demo-vpc 2>/dev/null || echo "VPC demo-vpc not found"

echo ""
echo "Cleaning up config directories..."
sudo rm -rf /tmp/vpc_config
sudo rm -rf /tmp/vpc_peering
sudo rm -f /tmp/firewall_rules.json

echo ""
echo "Cleaning up any orphaned namespaces..."
for ns in $(sudo ip netns list 2>/dev/null | awk '{print $1}'); do
    if [[ "$ns" == ns-vpc-* ]] || [[ "$ns" == ns-demo-* ]]; then
        echo "Deleting namespace: $ns"
        sudo ip netns delete "$ns" 2>/dev/null || true
    fi
done

echo ""
echo "Cleaning up orphaned veth interfaces..."
for iface in $(ip link show | grep -E "peer-vpc-|veth-|v-|vb-" | awk -F: '{print $2}' | awk '{print $1}'); do
    sudo ip link delete "$iface" 2>/dev/null || true
done

echo ""
echo "Cleaning up orphaned bridges..."
for br in $(ip link show | grep "br-vpc-\|br-demo-" | awk -F: '{print $2}' | awk '{print $1}'); do
    sudo ip link set "$br" down 2>/dev/null || true
    sudo ip link delete "$br" 2>/dev/null || true
done

echo ""
echo "Flushing iptables NAT rules..."
sudo iptables -t nat -F 2>/dev/null || true
sudo iptables -F FORWARD 2>/dev/null || true

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
