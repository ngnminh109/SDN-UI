# This version has the multithread iperf function (one host send multiple TCP request at a time)
# Also update run_iperf to provide more data.
# Also add the 'h1s ping h1f' function for checking the readiness of the topo.
# Modify by Khai Nguyen

# run iperf test on each server one by one. 
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import threading
import re
import time
from subprocess import check_output, call, CalledProcessError

# ONOS controller info
onos_ip = "192.168.180.130"  # Change this if needed
onos_port = 6653


def cleanup_qos():
    try:
        print("Cleaning up QoS configurations...")
        # Get all ports with QoS settings
        qos_ports = check_output(['sudo', 'ovs-vsctl', '--format=csv', '--columns=name,qos', 'list', 'Port']).decode()
        for line in qos_ports.strip().split('\n')[1:]:  # Skip CSV header
            parts = line.strip().split(',')
            if len(parts) == 2 and parts[1] != '[]':
                port_name = parts[0].strip('"')
                print(f"Removing QoS from port: {port_name}")
                call(['sudo', 'ovs-vsctl', 'remove', 'Port', port_name, 'qos', parts[1]])

        # Delete all QoS and Queue entries
        call(['sudo', 'ovs-vsctl', '--all', 'destroy', 'qos'])
        call(['sudo', 'ovs-vsctl', '--all', 'destroy', 'queue'])
        print("QoS cleanup completed.")
    except CalledProcessError as e:
        print(f"Error during QoS cleanup: {e}")


def setup_qos_on_host_ports(net):
    # Create two queues: 500 Mbps and 100 Mbps
    try:
        qos_result = check_output([
            'sudo', 'ovs-vsctl',
            '--', '--id=@q1s', 'create', 'queue', 'other-config:max-rate=5000000',  # Student - Mail Service
            '--', '--id=@q2s', 'create', 'queue', 'other-config:max-rate=25000000',  # Student - RTMP Service
            '--', '--id=@q3s', 'create', 'queue', 'other-config:max-rate=10000000',  # Student - Call Service
            '--', '--id=@q1f', 'create', 'queue', 'other-config:max-rate=15000000',  # Faculty - Mail Service
            '--', '--id=@q2f', 'create', 'queue', 'other-config:max-rate=50000000',  # Faculty - RTMP Service
            '--', '--id=@q3f', 'create', 'queue', 'other-config:max-rate=20000000',  # Faculty - Call Service
            '--', '--id=@newqos', 'create', 'qos', 'type=linux-htb',
            'other-config:max-rate=1000000000',
            'queues:1=@q1s', 'queues:2=@q2s', 'queues:3=@q3s',
            'queues:4=@q1f', 'queues:5=@q2f', 'queues:6=@q3f'
        ]).decode()

        # Extract the last UUID (QoS ID)
        qos_ids = qos_result.strip().split('\n')  # Split by newline and remove extra spaces
        qos_id = qos_ids[-1]  # Last line contains the QoS ID
        print(f"Created QoS with UUID: {qos_id}")

        # Apply QoS to all switch ports that connect to hosts
        for host in net.hosts:
            if host.name == 'r0':
                continue  # Skip router
            intf = host.defaultIntf()
            link = intf.link
            if link:
                # Determine which switch interface to apply QoS
                switch_intf = link.intf1 if link.intf2.node == host else link.intf2
                port_name = switch_intf.name
                print(f"Applying QoS to port: {port_name}")
                call(['sudo', 'ovs-vsctl', 'set', 'port', port_name, f'qos={qos_id}'])

    except CalledProcessError as e:
        print(f"Error executing OVS command: {e}")


class SimpleTopo(Topo):
    """Simple topology with 8 switches, 24 hosts, a router-like host, and 3 servers in the same subnet."""

    def build(self):
        # Switches
        switches = [self.addSwitch(f's{i + 1}', protocols='OpenFlow13') for i in range(8)]

        # Student subnet: 10.0.0.0/16
        student_hosts = [self.addHost(f'h{i + 1}s', ip=f'10.0.0.{i + 1}/24') for i in range(8)]

        # Faculty subnet: 10.0.1.0/16
        faculty_hosts = [self.addHost(f'h{i + 1}f', ip=f'10.0.1.{i + 1}/24') for i in range(8)]

        # Server subnet: 10.0.2.0/16
        server_hosts = [self.addHost(f'srv{i + 1}', ip=f'10.0.2.{i + 1}/24') for i in range(3)]

        # Add a host to act as the router
        router = self.addHost('r0')

        # Connect the router to switch 0 for the student subnet
        self.addLink(router, switches[0])

        # Connect the router to switch 1 for the faculty subnet
        self.addLink(router, switches[1])

        # Connect the router to switch 2 for the server subnet
        self.addLink(router, switches[2])

        # Connect student and faculty hosts to switches
        for i in range(8):
            self.addLink(student_hosts[i], switches[i])
            self.addLink(faculty_hosts[i], switches[i])

        # Connect server hosts to switch 2
        for server in server_hosts:
            self.addLink(server, switches[2])

        # Switch interconnections
        self.addLink(switches[0], switches[5])
        self.addLink(switches[0], switches[6])
        self.addLink(switches[1], switches[5])
        self.addLink(switches[1], switches[7])
        self.addLink(switches[2], switches[3])
        self.addLink(switches[2], switches[5])
        self.addLink(switches[2], switches[6])
        self.addLink(switches[4], switches[5])
        self.addLink(switches[4], switches[6])


def run():
    c0 = RemoteController('c0', ip=onos_ip, port=onos_port)

    net = Mininet(topo=SimpleTopo(),
                  controller=c0,
                  switch=OVSSwitch)

    net.start()

    # Configure the router (host r0) interfaces
    router = net.get('r0')
    router.setIP('10.0.0.250/24', intf='r0-eth0')  # Student subnet
    router.setIP('10.0.1.250/24', intf='r0-eth1')  # Faculty subnet
    router.setIP('10.0.2.250/24', intf='r0-eth2')  # Server subnet

    router.cmd('sysctl -w net.ipv4.ip_forward=1')  # Enable IP forwarding

    # Set default routes on student and faculty hosts
    for i in range(8):
        student_host = net.get(f'h{i + 1}s')
        student_host.cmd('ip route add default via 10.0.0.250')

        faculty_host = net.get(f'h{i + 1}f')
        faculty_host.cmd('ip route add default via 10.0.1.250')

    # Set default routes on server hosts
    for i in range(3):
        server_host = net.get(f'srv{i + 1}')
        server_host.cmd('ip route add default via 10.0.2.250')

    for switch in net.switches:
        switch.cmd('sudo ovs-vsctl set Bridge {} stp_enable=true'.format(switch.name))

    setup_qos_on_host_ports(net)

    print("\nNetwork is up.\n")
    return net


def ping_h1s_to_h1f(net):
    h1s = net.get('h1s')
    h1f = net.get('h1f')
    print(f"\n*** Pinging from {h1s.name} to {h1f.name} with 5 packets")
    result = h1s.cmd(f'ping -c 5 {h1f.IP()}')
    print(result)


def parse_bandwidth(output):
    """Extract Mbps value from iperf output."""
    match = re.search(r'(\d+\.\d+|\d+)\s+Mbits/sec', output)
    return float(match.group(1)) if match else 0.0


# TCP iperf output parser
def parse_iperf_output_tcp(output):
    duration_match = re.search(r'(\d+\.\d+)-\s*(\d+\.\d+)\s+sec', output)
    bandwidth_match = re.search(r'(\d+\.\d+|\d+)\s+Mbits/sec', output)
    transferred_match = re.search(r'(\d+\.\d+|\d+)\s+MBytes', output)

    return {
        "duration_sec": float(duration_match.group(2)) - float(duration_match.group(1)) if duration_match else 0.0,
        "bandwidth_mbps": float(bandwidth_match.group(1)) if bandwidth_match else 0.0,
        "transferred_mbytes": float(transferred_match.group(1)) if transferred_match else 0.0,
    }


# UDP iperf output parser (includes packet loss)
def parse_iperf_output_udp(output):
    duration_match = re.search(r'(\d+\.\d+)-\s*(\d+\.\d+)\s+sec', output)
    bandwidth_match = re.search(r'(\d+\.\d+|\d+)\s+Mbits/sec', output)
    transferred_match = re.search(r'(\d+\.\d+|\d+)\s+MBytes', output)
    loss_match = re.search(r'(\d+)/(\d+)\s+\((\d+)%\)', output)  # packet loss pattern

    return {
        "duration_sec": float(duration_match.group(2)) - float(duration_match.group(1)) if duration_match else 0.0,
        "bandwidth_mbps": float(bandwidth_match.group(1)) if bandwidth_match else 0.0,
        "transferred_mbytes": float(transferred_match.group(1)) if transferred_match else 0.0,
        "lost_packets": int(loss_match.group(1)) if loss_match else 0,
        "total_packets": int(loss_match.group(2)) if loss_match else 0,
        "loss_percent": float(loss_match.group(3)) if loss_match else 0.0,
    }


def run_iperf_tcp(net):
    servers = [net.get(f'srv{i + 1}') for i in range(3)]
    student_hosts = [net.get(f'h{i + 1}s') for i in range(8)]
    faculty_hosts = [net.get(f'h{i + 1}f') for i in range(8)]
    all_hosts = student_hosts + faculty_hosts

    for server in servers:
        server_name = server.name
        info(f'\n*** Starting iperf TCP server on {server_name}\n')
        server.cmd('killall -9 iperf')
        server.cmd('iperf -s &')
        time.sleep(1)

        for host in all_hosts:
            group = 'student' if host.name.endswith('s') else 'faculty'
            info(f'*** {host.name} testing TCP connection to {server_name} ({server.IP()})\n')
            output = host.cmd(f'iperf -c {server.IP()} -t 2')
            result = parse_iperf_output_tcp(output)
            print(f'{host.name} -> {server_name} [TCP]: {result["bandwidth_mbps"]:.2f} Mbps, '
                  f'{result["transferred_mbytes"]:.2f} MB in {result["duration_sec"]:.2f} sec')

        server.cmd('killall -9 iperf')
        info(f'*** Stopped iperf TCP server on {server_name}\n')


def run_iperf_multithreaded_tcp(net, num_requests=3):
    servers = [net.get(f'srv{i + 1}') for i in range(3)]
    student_hosts = [net.get(f'h{i + 1}s') for i in range(8)]
    faculty_hosts = [net.get(f'h{i + 1}f') for i in range(8)]

    all_hosts = student_hosts + faculty_hosts
    bandwidth_data = {
        'student': {srv.name: [] for srv in servers},
        'faculty': {srv.name: [] for srv in servers}
    }

    for server in servers:
        server_name = server.name
        info(f'\n*** Starting TCP iperf server on {server_name}\n')
        server.cmd('killall -9 iperf')
        server.cmd('iperf -s &')
        time.sleep(1)  # wait for server ready

        def client_test(host, server_ip, group, srv_name):
            for i in range(num_requests):
                info(f'*** {host.name} TCP request {i + 1} to {srv_name}\n')
                output = host.cmd(f'iperf -c {server_ip} -t 2')
                bw = parse_bandwidth(output)
                bandwidth_data[group][srv_name].append(bw)
                print(f'{host.name} -> {srv_name} [Request {i + 1}]: {bw:.2f} Mbits/sec')

        threads = []
        for host in all_hosts:
            group = 'student' if host.name.endswith('s') else 'faculty'
            t = threading.Thread(target=client_test, args=(host, server.IP(), group, server_name))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        server.cmd('killall -9 iperf')
        info(f'*** Stopped TCP iperf server on {server_name}\n')

    # Average bandwidth output
    print("\n=== Average TCP Bandwidth (Mbits/sec) ===")
    for group in ['student', 'faculty']:
        for server in servers:
            bw_list = bandwidth_data[group][server.name]
            if bw_list:
                avg_bw = sum(bw_list) / len(bw_list)
                print(f'{group.title()} to {server.name}: {avg_bw:.2f} Mbits/sec')
            else:
                print(f'{group.title()} to {server.name}: No data')


def run_iperf_multithreaded_udp(net, num_requests=3):
    servers = [net.get(f'srv{i + 1}') for i in range(3)]
    student_hosts = [net.get(f'h{i + 1}s') for i in range(8)]
    faculty_hosts = [net.get(f'h{i + 1}f') for i in range(8)]

    all_hosts = student_hosts + faculty_hosts
    bandwidth_data = {
        'student': {srv.name: [] for srv in servers},
        'faculty': {srv.name: [] for srv in servers}
    }

    for server in servers:
        server_name = server.name
        info(f'\n*** Starting UDP iperf server on {server_name}\n')
        server.cmd('killall -9 iperf')
        # UDP server mode (-u)
        server.cmd('iperf -s -u &')
        time.sleep(1)  # wait for server ready

        def client_test(host, server_ip, group, srv_name):
            for i in range(num_requests):
                info(f'*** {host.name} UDP request {i + 1} to {srv_name}\n')
                # Adding -u for UDP client, -b 10M sets bandwidth (can adjust)
                output = host.cmd(f'iperf -c {server_ip} -u -t 2 -b 10M')
                bw = parse_bandwidth(output)
                bandwidth_data[group][srv_name].append(bw)
                print(f'{host.name} -> {srv_name} [Request {i + 1}]: {bw:.2f} Mbits/sec')

        threads = []
        for host in all_hosts:
            group = 'student' if host.name.endswith('s') else 'faculty'
            t = threading.Thread(target=client_test, args=(host, server.IP(), group, server_name))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        server.cmd('killall -9 iperf')
        info(f'*** Stopped UDP iperf server on {server_name}\n')

    # Average bandwidth output
    print("\n=== Average UDP Bandwidth (Mbits/sec) ===")
    for group in ['student', 'faculty']:
        for server in servers:
            bw_list = bandwidth_data[group][server.name]
            if bw_list:
                avg_bw = sum(bw_list) / len(bw_list)
                print(f'{group.title()} to {server.name}: {avg_bw:.2f} Mbits/sec')
            else:
                print(f'{group.title()} to {server.name}: No data')


def ping_all(net):
    """Run ping test between all hosts"""
    print("\n*** Running ping tests ***")
    result = net.pingAll()
    return result


def stop_network(net):
    """Stop the network and clean up"""
    if net:
        print("\n*** Stopping network ***")
        net.stop()
        cleanup_qos()
        print("*** Network stopped ***")


if __name__ == '__main__':
    setLogLevel('info')
    net = run()
    try:
        # Test the network
        ping_h1s_to_h1f(net)
        
        # Run iPerf tests
        run_iperf_multithreaded_tcp(net)
        
        # Start CLI for manual testing
        CLI(net)
    finally:
        stop_network(net)
