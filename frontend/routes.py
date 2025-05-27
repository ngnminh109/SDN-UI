import subprocess
import json
import os
import requests
from requests.auth import HTTPBasicAuth
from flask import render_template, jsonify, request
from app import app
# Import from backend directory
import sys
import os
sys.path.append('../backend')  # Add backend directory to Python path
import topo_cam6
import flow_rule

# Global network instance
net = None

# ONOS configuration - can be overridden by environment variables
ONOS_IP = os.getenv("ONOS_IP", "192.168.180.130")
ONOS_PORT = os.getenv("ONOS_PORT", "8181")
ONOS_USERNAME = os.getenv("ONOS_USERNAME", "onos")
ONOS_PASSWORD = os.getenv("ONOS_PASSWORD", "rocks")

@app.route("/")
def dashboard():
    """Main dashboard view"""
    return render_template("dashboard.html")

@app.route("/topology")
def topology():
    """Network topology view"""
    return render_template("topology.html")

@app.route("/control")
def control_panel():
    """Network control panel"""
    return render_template("control_panel.html")

@app.route("/monitoring")
def monitoring():
    """Network monitoring view"""
    return render_template("monitoring.html")

@app.route("/flows")
def flow_rules():
    """Flow rules management"""
    return render_template("flow_rules.html")

@app.route("/qos")
def qos():
    """QoS configuration view"""
    return render_template("qos.html")

# API Endpoints
@app.route("/api/start", methods=["POST"])
def start_network():
    """Start the Mininet network"""
    global net
    try:
        if net is not None:
            return jsonify({"status": "error", "message": "Network is already running"}), 400
        
        net = topo_cam6.run()
        return jsonify({"status": "success", "message": "Network started successfully"})
    except Exception as e:
        app.logger.error(f"Error starting network: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to start network: {str(e)}"}), 500

@app.route("/api/stop", methods=["POST"])
def stop_network():
    """Stop the Mininet network"""
    global net
    try:
        if net is None:
            return jsonify({"status": "error", "message": "Network is not running"}), 400
        
        net.stop()
        net = None
        return jsonify({"status": "success", "message": "Network stopped successfully"})
    except Exception as e:
        app.logger.error(f"Error stopping network: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to stop network: {str(e)}"}), 500

@app.route("/api/status")
def network_status():
    """Get network status"""
    global net
    is_running = net is not None
    
    # Get device information from ONOS
    devices = []
    try:
        if is_running:
            devices = get_onos_devices()
    except Exception as e:
        app.logger.error(f"Error getting ONOS devices: {str(e)}")
    
    return jsonify({
        "status": "success",
        "network_running": is_running,
        "devices": devices,
        "device_count": len(devices)
    })

@app.route("/api/pingall")
def ping_all():
    """Run ping test between all hosts"""
    global net
    try:
        if net is None:
            return jsonify({"status": "error", "message": "Network is not running"}), 400
        
        # Run ping test from h1s to h1f
        topo_cam6.ping_h1s_to_h1f(net)
        return jsonify({"status": "success", "message": "Ping test completed successfully"})
    except Exception as e:
        app.logger.error(f"Error running ping test: {str(e)}")
        return jsonify({"status": "error", "message": f"Ping test failed: {str(e)}"}), 500

@app.route("/api/iperf")
def run_iperf():
    """Run iPerf performance test"""
    global net
    try:
        if net is None:
            return jsonify({"status": "error", "message": "Network is not running"}), 400
        
        # Run iPerf test
        topo_cam6.run_iperf_multithreaded_tcp(net)
        return jsonify({"status": "success", "message": "iPerf test completed successfully"})
    except Exception as e:
        app.logger.error(f"Error running iPerf test: {str(e)}")
        return jsonify({"status": "error", "message": f"iPerf test failed: {str(e)}"}), 500

@app.route("/api/inject_flows", methods=["POST"])
def inject_flows():
    """Inject QoS flow rules into ONOS"""
    try:
        # Run the flow rule injection script
        result = subprocess.run(['python3', 'flow_rule.py'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "message": "Flow rules injected successfully",
                "output": result.stdout
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to inject flow rules",
                "error": result.stderr
            }), 500
    except Exception as e:
        app.logger.error(f"Error injecting flows: {str(e)}")
        return jsonify({"status": "error", "message": f"Flow injection failed: {str(e)}"}), 500

@app.route("/api/flows")
def get_flows():
    """Get current flow rules from ONOS"""
    try:
        url = f"http://{ONOS_IP}:{ONOS_PORT}/onos/v1/flows"
        response = requests.get(url, auth=HTTPBasicAuth(ONOS_USERNAME, ONOS_PASSWORD))
        
        if response.status_code == 200:
            flows_data = response.json()
            return jsonify({"status": "success", "flows": flows_data.get("flows", [])})
        else:
            return jsonify({"status": "error", "message": "Failed to retrieve flows"}), 500
    except Exception as e:
        app.logger.error(f"Error getting flows: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to get flows: {str(e)}"}), 500

@app.route("/api/devices")
def get_devices():
    """Get device information from ONOS"""
    try:
        devices = get_onos_devices()
        return jsonify({"status": "success", "devices": devices})
    except Exception as e:
        app.logger.error(f"Error getting devices: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to get devices: {str(e)}"}), 500

@app.route("/api/qos")
def get_qos_info():
    """Get QoS configuration information"""
    try:
        # Get queue information from OVS
        result = subprocess.run(['sudo', 'ovs-vsctl', 'list', 'queue'], capture_output=True, text=True)
        
        qos_info = {
            "queues": [],
            "bandwidth_limits": {
                "student_mail": "5 Mbps",
                "student_rtmp": "25 Mbps", 
                "student_call": "10 Mbps",
                "faculty_mail": "15 Mbps",
                "faculty_rtmp": "50 Mbps",
                "faculty_call": "20 Mbps"
            }
        }
        
        if result.returncode == 0:
            qos_info["ovs_output"] = result.stdout
        
        return jsonify({"status": "success", "qos": qos_info})
    except Exception as e:
        app.logger.error(f"Error getting QoS info: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to get QoS info: {str(e)}"}), 500

def get_onos_devices():
    """Helper function to get device information from ONOS"""
    try:
        url = f"http://{ONOS_IP}:{ONOS_PORT}/onos/v1/devices"
        response = requests.get(url, auth=HTTPBasicAuth(ONOS_USERNAME, ONOS_PASSWORD))
        
        if response.status_code == 200:
            devices_data = response.json()
            return devices_data.get("devices", [])
        else:
            app.logger.error(f"Failed to get devices from ONOS: {response.status_code}")
            return []
    except Exception as e:
        app.logger.error(f"Error connecting to ONOS: {str(e)}")
        return []
