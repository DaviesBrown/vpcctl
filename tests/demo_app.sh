#!/bin/bash

echo "========================================="
echo "VPC CLI - Application Deployment Demo"
echo "========================================="
echo ""
echo "This demo deploys a 3-tier web application:"
echo "  - Web Server (public subnet)"
echo "  - App Server (private subnet)"
echo "  - Database (private subnet)"
echo ""

INTERNET_IFACE=${1:-eth0}

# Cleanup first
echo "Cleaning up any existing demo resources..."
sudo python3 vpcctl.py delete-peering demo-vpc demo-vpc 2>/dev/null || true
sudo python3 vpcctl.py delete-vpc demo-vpc 2>/dev/null || true

echo ""
echo "=== Step 1: Creating Production VPC ==="
sudo python3 vpcctl.py create-vpc demo-vpc 172.16.0.0/16

echo ""
echo "=== Step 2: Creating Subnets ==="
echo "Creating public subnet for web tier..."
sudo python3 vpcctl.py add-subnet demo-vpc web 172.16.1.0/24 --type public

echo "Creating private subnet for app tier..."
sudo python3 vpcctl.py add-subnet demo-vpc app 172.16.2.0/24 --type private

echo "Creating private subnet for database tier..."
sudo python3 vpcctl.py add-subnet demo-vpc db 172.16.3.0/24 --type private

echo ""
echo "=== Step 3: Enabling Internet Access ==="
sudo python3 vpcctl.py enable-nat demo-vpc --interface $INTERNET_IFACE

echo ""
echo "=== Step 4: Applying Security Rules ==="
cat > /tmp/demo_web_firewall.json <<EOF
{
  "subnet": "172.16.1.0/24",
  "ingress": [
    {"port": 80, "protocol": "tcp", "action": "allow"},
    {"port": 443, "protocol": "tcp", "action": "allow"},
    {"port": 22, "protocol": "tcp", "action": "deny"}
  ]
}
EOF

sudo python3 vpcctl.py apply-firewall demo-vpc /tmp/demo_web_firewall.json

echo ""
echo "=== Step 5: Deploying Web Server ==="
echo "Starting Nginx-like web server on port 80..."

# Create a simple HTML page
sudo python3 vpcctl.py exec demo-vpc web "cat > /tmp/index.html <<'HTML'
<!DOCTYPE html>
<html>
<head><title>VPC Demo App</title></head>
<body>
  <h1>Welcome to VPC CLI Demo!</h1>
  <p>This web server is running in subnet 172.16.1.0/24</p>
  <p>Server IP: 172.16.1.2</p>
</body>
</html>
HTML"

# Start web server
sudo python3 vpcctl.py exec demo-vpc web "cd /tmp && nohup python3 -m http.server 80 > /tmp/web.log 2>&1 &"

sleep 2

echo ""
echo "=== Step 6: Deploying App Server ==="
echo "Starting application server on port 8080..."

# Create a simple API response
sudo python3 vpcctl.py exec demo-vpc app "cat > /tmp/api.html <<'HTML'
{
  \"status\": \"ok\",
  \"message\": \"App server running\",
  \"ip\": \"172.16.2.2\",
  \"tier\": \"application\"
}
HTML"

sudo python3 vpcctl.py exec demo-vpc app "cd /tmp && nohup python3 -m http.server 8080 > /tmp/app.log 2>&1 &"

sleep 2

echo ""
echo "=== Step 7: Deploying Database Server ==="
echo "Starting mock database server on port 5432..."

# Create a simple DB response
sudo python3 vpcctl.py exec demo-vpc db "cat > /tmp/db.html <<'HTML'
{
  \"status\": \"connected\",
  \"database\": \"production\",
  \"ip\": \"172.16.3.2\"
}
HTML"

sudo python3 vpcctl.py exec demo-vpc db "cd /tmp && nohup python3 -m http.server 5432 > /tmp/db.log 2>&1 &"

sleep 2

echo ""
echo "========================================="
echo "Deployment Complete! Testing..."
echo "========================================="
echo ""

echo "=== Test 1: Web Server (Public) ==="
echo "Testing web server at 172.16.1.2:80..."
sudo python3 vpcctl.py exec demo-vpc web "curl -s http://172.16.1.2:80 | head -5"

echo ""
echo "=== Test 2: App Server from Web Tier ==="
echo "Web tier accessing app tier (172.16.2.2:8080)..."
sudo python3 vpcctl.py exec demo-vpc web "curl -s http://172.16.2.2:8080/api.html"

echo ""
echo "=== Test 3: Database from App Tier ==="
echo "App tier accessing database tier (172.16.3.2:5432)..."
sudo python3 vpcctl.py exec demo-vpc app "curl -s http://172.16.3.2:5432/db.html"

echo ""
echo "=== Test 4: Database Isolation ==="
echo "Verifying web tier CANNOT directly access database (should work due to routing, but in production would be blocked by firewall)..."
sudo python3 vpcctl.py exec demo-vpc web "curl -s -m 3 http://172.16.3.2:5432/db.html 2>&1 | head -3"

echo ""
echo "=== Test 5: Internet Access from Web Tier ==="
echo "Testing internet connectivity..."
sudo python3 vpcctl.py exec demo-vpc web "ping -c 2 8.8.8.8" || echo "Internet test - may fail without internet"

echo ""
echo "=== Test 6: Process Verification ==="
echo "Verifying all servers are running..."
echo ""
echo "Web server processes:"
sudo python3 vpcctl.py exec demo-vpc web "ps aux | grep 'python3 -m http.server' | grep -v grep | wc -l"

echo "App server processes:"
sudo python3 vpcctl.py exec demo-vpc app "ps aux | grep 'python3 -m http.server' | grep -v grep | wc -l"

echo "Database server processes:"
sudo python3 vpcctl.py exec demo-vpc db "ps aux | grep 'python3 -m http.server' | grep -v grep | wc -l"

echo ""
echo "========================================="
echo "Architecture Diagram"
echo "========================================="
cat <<'DIAGRAM'

                    🌐 INTERNET
                         ↓
                   [NAT Gateway]
                         ↓
    ┌────────────────────────────────────────┐
    │         VPC: 172.16.0.0/16             │
    │                                        │
    │  ┌──────────────────────────────────┐  │
    │  │ Web Subnet: 172.16.1.0/24        │  │
    │  │ 📱 Web Server (172.16.1.2:80)    │  │
    │  │    - Public facing               │  │
    │  │    - Ports 80, 443 open          │  │
    │  └──────────┬───────────────────────┘  │
    │             ↓                          │
    │  ┌──────────────────────────────────┐  │
    │  │ App Subnet: 172.16.2.0/24        │  │
    │  │ ⚙️  App Server (172.16.2.2:8080) │  │
    │  │    - Private                     │  │
    │  │    - Only web tier can access    │  │
    │  └──────────┬───────────────────────┘  │
    │             ↓                          │
    │  ┌──────────────────────────────────┐  │
    │  │ DB Subnet: 172.16.3.0/24         │  │
    │  │ 🗄️  Database (172.16.3.2:5432)   │  │
    │  │    - Most isolated               │  │
    │  │    - Only app tier can access    │  │
    │  └──────────────────────────────────┘  │
    │                                        │
    └────────────────────────────────────────┘

DIAGRAM

echo ""
echo "========================================="
echo "Demo Complete!"
echo "========================================="
echo ""
echo "To cleanup and stop all servers, run:"
echo "  sudo ./cleanup.sh"
echo ""
echo "To view VPC details:"
echo "  sudo python3 vpcctl.py show-vpc demo-vpc"
echo ""
