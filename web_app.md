
# SDN Web Application User Guide

This guide explains how to use the SDN Control Dashboard web application for managing and monitoring your Software Defined Network.

## Overview

The SDN Web Application provides a user-friendly interface for:
- Network topology management
- Flow rule configuration
- Performance monitoring
- Quality of Service (QoS) control
- Real-time network testing

## Starting the Application

1. Ensure your SDN environment is set up (see README.md)
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Start the web server:
   ```bash
   python3 main.py
   ```
4. Open your browser and go to: `http://<your-vm-ip>:5000`

## Application Interface

### Navigation

The application has six main sections accessible from the top navigation bar:

- **Dashboard** - Network overview and status
- **Topology** - Network structure visualization
- **Control Panel** - Network operations and testing
- **Monitoring** - Performance metrics and analysis
- **Flow Rules** - Traffic flow management
- **QoS** - Quality of Service configuration

## Getting Started

### Step 1: Select a Topology

1. Go to **Control Panel**
2. In the "Topology Selection" section:
   - Click the dropdown menu
   - Select a topology (e.g., `topo_final_162` or `topo_final_88`)
   - The selection will be confirmed with a success message

### Step 2: Select Flow Rules

1. In the "Flow Rule Selection" section:
   - Click the dropdown menu
   - Select a flow rule set (e.g., `flow_rule_final`)
   - Confirm the selection

### Step 3: Start the Network

1. Click the **"Start Network"** button
2. Wait for the "Network started successfully" message
3. The network status will change to "Running"

## Main Features

### Dashboard

**Purpose:** Overview of your network status

**Key Information:**
- Network running status (Running/Stopped)
- Connected device count
- Selected topology information
- Quick action buttons

**Actions Available:**
- Start/Stop network
- View current configuration
- Quick status refresh

### Topology View

**Purpose:** Visualize network structure and devices

**Features:**
- Network map showing switches, hosts, and connections
- Device list with real-time status
- Subnet information (Student, Faculty, Server)
- IP address assignments

**Device Types:**
- **Student Hosts:** h1s, h2s, ... (10.0.0.x subnet)
- **Faculty Hosts:** h1f, h2f, ... (10.0.1.x subnet)
- **Servers:** srv1, srv2, srv3 (10.0.2.x subnet)
- **Switches:** s1-s8
- **Router:** r0 (connects subnets)

### Control Panel

**Purpose:** Network operations and testing

**Network Controls:**
- **Start Network:** Initialize the Mininet network
- **Stop Network:** Shut down the network
- **Network Status:** Check current state

**Testing Tools:**
- **Ping All:** Test connectivity between all hosts
- **iPerf Test:** Measure network performance
- **Server-specific Tests:** Target individual servers

**Test Types:**
1. **Ping All Test:**
   - Tests connectivity between all network hosts
   - Shows packet loss percentage
   - Displays successful vs. dropped packets

2. **iPerf Performance Test:**
   - Measures bandwidth between hosts and servers
   - Provides latency measurements
   - Shows average, minimum, and maximum performance

### Monitoring

**Purpose:** Real-time network performance analysis

**Metrics Displayed:**
- Host counts (Student/Faculty)
- Network topology details
- Performance statistics
- Current network configuration

**Information Panels:**
- Current topology details
- Host distribution
- IP address assignments
- Network topology name

### Flow Rules

**Purpose:** Manage traffic flow policies

**Features:**
- View current ONOS flow rules
- Inject QoS (Quality of Service) rules
- Refresh flow rule table
- Flow statistics

**Actions:**
- **Refresh Flow Rules:** Update the current flow table
- **Inject QoS Rules:** Apply traffic prioritization rules
- **View Statistics:** See flow rule counts and details

### QoS (Quality of Service)

**Purpose:** Configure traffic prioritization

**QoS Configuration:**
- **Student Traffic Limits:**
  - Mail Service: 5 Mbps
  - RTMP Streaming: 25 Mbps  
  - Voice Calls: 10 Mbps

- **Faculty Traffic Limits:**
  - Mail Service: 15 Mbps
  - RTMP Streaming: 50 Mbps
  - Voice Calls: 20 Mbps

**Features:**
- Queue configuration display
- Bandwidth allocation overview
- Service type management

## Common Workflows

### Basic Network Testing

1. **Setup:**
   - Select topology and flow rules
   - Start the network

2. **Connectivity Test:**
   - Go to Control Panel
   - Click "Run Ping Test"
   - Review connectivity results

3. **Performance Test:**
   - Click "Run iPerf Test"
   - Analyze bandwidth and latency results

### QoS Configuration

1. **Apply QoS Rules:**
   - Go to Flow Rules section
   - Click "Inject QoS Rules"
   - Verify rules are applied

2. **Monitor QoS:**
   - Go to QoS section
   - Review bandwidth allocations
   - Check queue configurations

### Network Monitoring

1. **Real-time Status:**
   - Dashboard shows live network status
   - Topology view displays device states

2. **Performance Analysis:**
   - Monitoring section shows detailed metrics
   - Historical performance data

## Troubleshooting

### Common Issues

**Network Won't Start:**
- Ensure ONOS controller is running
- Check if previous network is properly stopped
- Verify topology selection

**No Devices Shown:**
- Check ONOS connection
- Refresh the device list
- Verify network is running

**Performance Tests Fail:**
- Ensure network is started
- Check host connectivity with ping test first
- Verify selected topology supports the test type

**Flow Rules Not Applied:**
- Check ONOS controller status
- Ensure proper flow rule module is selected
- Verify network is running before injecting rules

### Error Messages

- **"Network is not running":** Start the network first
- **"No topology selected":** Choose a topology in Control Panel
- **"Failed to connect to ONOS":** Check ONOS container status

## Advanced Features

### Custom Topologies

The application supports different network topologies:
- **topo_final_162:** 16 student hosts, 2 faculty hosts
- **topo_final_88:** 8 student hosts, 8 faculty hosts

### Performance Testing

**TCP Tests:**
- Multithreaded bandwidth measurement
- Latency analysis
- Per-host performance metrics

**UDP Tests:**
- Jitter measurement
- Packet loss analysis
- Real-time streaming simulation

### Flow Rule Management

- Custom flow rule injection
- Traffic prioritization
- Service-specific policies
- Real-time rule monitoring

## Tips for Best Results

1. **Always start with topology selection** before starting the network
2. **Run ping tests first** to verify basic connectivity
3. **Allow time between tests** for accurate measurements
4. **Monitor the dashboard** for real-time status updates
5. **Use QoS features** to simulate realistic network conditions

This web application provides comprehensive SDN network management capabilities through an intuitive interface, making it easy to experiment with and learn about Software Defined Networking concepts.
