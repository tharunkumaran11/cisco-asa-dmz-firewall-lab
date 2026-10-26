# Cisco ASA Firewall & DMZ Security Lab

A hands-on network security lab built in **Cisco Packet Tracer**. I designed a three-zone network (inside, DMZ, outside) around a **Cisco ASA 5505** firewall, published a web server in the DMZ, restricted outside access with a host-specific ACL, and hardened the access switches with **port security**. A small Python script summarises the tests I recorded.

![Network topology](screenshots/01-topology.png)

## Why I built this

My earlier projects are in cloud and DevOps (AWS, Kubernetes, CI/CD). I wanted to understand the network layer underneath them: how traffic is separated, who is allowed to reach what, and how a device gets blocked. The ideas here, such as network zones, allow-lists and least privilege, are the same in spirit as subnets, security groups and network ACLs in AWS.

This lab covers three ideas:

- **Segmentation:** keeping untrusted, semi-trusted and trusted networks apart
- **Least privilege:** allowing only what is needed instead of opening whole subnets
- **Layer 2 hardening:** limiting which devices can plug into a switch port

## Topology

| Device | Role |
|---|---|
| `FW-ASA` | Cisco ASA 5505 (ASA 8.4(2)), the firewall between all three zones |
| `SW-OUTSIDE` | Cisco 2960 switch on the outside network |
| `SW-INSIDE` | Cisco 2960 switch for employee devices |
| `PC-ATTACKER` | Outside test host that simulates an external user |
| `PC-EMPLOYEE1`, `PC-EMPLOYEE2` | Inside employee endpoints |
| `SRV-DMZ` | Web server in the DMZ |

## Addressing plan

| Device / interface | IP address | Gateway |
|---|---|---|
| ASA outside (Vlan2) | `203.0.113.1/24` | n/a |
| PC-ATTACKER | `203.0.113.10/24` | `203.0.113.1` |
| ASA inside (Vlan1) | `192.168.10.1/24` | n/a |
| PC-EMPLOYEE1 | `192.168.10.10/24` | `192.168.10.1` |
| PC-EMPLOYEE2 | `192.168.10.11/24` | `192.168.10.1` |
| ASA DMZ (Vlan3) | `192.168.20.1/24` | n/a |
| SRV-DMZ | `192.168.20.10/24` | `192.168.20.1` |

The `203.0.113.0/24` range is reserved for documentation and examples, so I used it as a safe simulated "internet".

## How the design works

### Firewall zones

| ASA VLAN | Zone name | Security level | Subnet |
|---|---|---:|---|
| Vlan1 | `inside` | 100 | `192.168.10.0/24` |
| Vlan3 | `dmz` | 50 | `192.168.20.0/24` |
| Vlan2 | `outside` | 0 | `203.0.113.0/24` |

The ASA uses security levels to decide what flows by default. Traffic from a higher level to a lower level (inside to DMZ or outside) is allowed. Traffic from a lower level to a higher level is denied unless an ACL permits it. That is why the outside network can't reach the employee network without any rule written for it.

### Outside access control list

```
access-list OUTSIDE-IN extended permit tcp host 203.0.113.10 host 192.168.20.10 eq www
access-list OUTSIDE-IN extended permit icmp host 203.0.113.10 host 192.168.20.10
access-group OUTSIDE-IN in interface outside
```

- Only one outside host (`203.0.113.10`) is allowed through.
- It can reach only one destination (the DMZ web server) and only over HTTP, plus ICMP for troubleshooting.
- Nothing from the outside is permitted to the employee network.

### Switch port security

Applied to the employee access ports on `SW-INSIDE` (Fa0/1, Fa0/2) and the attacker port on `SW-OUTSIDE` (Fa0/1):

```
switchport mode access
switchport port-security
switchport port-security maximum 1
switchport port-security violation restrict
switchport port-security mac-address sticky
```

## Design decisions

**Why a DMZ instead of putting the web server on the employee LAN?**
A public-facing server is the most likely thing to be attacked. In the DMZ, it sits in its own subnet with its own security level (50). The ASA 5505 on this license also requires `no forward interface Vlan1` on the DMZ interface, which stops the DMZ from starting connections to the inside network. A compromised web server therefore has no direct path into the employee network.

**Why allow one host instead of the whole outside network?**
Permitting a single source (`203.0.113.10`) to a single destination (`192.168.20.10`) on a single service (HTTP) is least privilege. Opening a subnet or using `any` would allow far more than the test needs. ICMP is permitted only for troubleshooting and could be removed in a real deployment.

**Why sticky MAC with a maximum of 1?**
Sticky learning means I don't have to type each MAC address by hand: the switch learns the first device and remembers it. A maximum of 1 means a second device plugged into the same port is not accepted.

**Why `violation restrict` instead of `shutdown`?**
`restrict` drops frames from the unknown device, counts and logs the violation, and keeps the port up. `shutdown` is stricter but disables the port completely, so one mistake or one rogue cable takes a legitimate user offline until someone resets it. I chose `restrict` to show the trade-off between security and availability.

## Test results

| Test | Result |
|---|---|
| Employee-to-employee ping (`PC-EMPLOYEE1` to `PC-EMPLOYEE2`) | Succeeded |
| Outside host pinging an employee PC (`203.0.113.10` to `192.168.10.10`) | 4 sent, 0 received, 100% loss (timed out) |
| Port security status on inside ports | Secure-up, one sticky MAC learned, zero violations at capture time |
| HTTP service on `SRV-DMZ` | Enabled |
| Outside host browsing to `http://192.168.20.10` | Worked in one test run but was inconsistent in later runs |

Two things I want to be clear about:

- **A timeout doesn't prove which control blocked the packet.** The ASA denies lower-to-higher traffic by default, so the ping would time out even without my ACL. Confirming that the firewall dropped it needs ACL hit counters before and after the test, and my current ACL has no explicit deny line that would produce one. That is the first item in my next steps.
- **The DMZ HTTP result is inconsistent.** Packet Tracer's ASA simulation can behave unpredictably, so I am recording what I observed instead of claiming it is repeatable.

## Test log and analysis script

The `monitoring/` folder holds a record of the tests I ran and a small Python script that summarises it.

- `monitoring-log.csv`: one row per test, with the device, source, destination, expected result and the result I observed in Packet Tracer.
- `analyse_monitoring.py`: reads the CSV, labels each test `PASS` or `INVESTIGATE`, and prints a summary.

```
cd monitoring
python analyse_monitoring.py
```

Current output:

```
[PASS] Inside-PC-connectivity
  Path: 192.168.10.10 -> 192.168.10.11
  Expected: PING_SUCCESS | Actual: PING_SUCCESS

[INVESTIGATE] Outside-to-inside-ping
  Path: 203.0.113.10 -> 192.168.10.10
  Expected: PING_BLOCKED | Actual: PING_TIMEOUT
  Note: Ping timed out as expected; verify ASA ACL counters before attributing the block to the firewall.

Summary:
  PASS: 1
  INVESTIGATE: 1
```

The script only analyses results I typed in. It doesn't capture live traffic and can't show which device caused a failure. It marks the blocked-ping test `INVESTIGATE` on purpose, for the reason in the previous section.

## Screenshots

| File | Shows |
|---|---|
| [`01-topology.png`](screenshots/01-topology.png) | Network layout and zones |
| [`02-asa-interface-status.png`](screenshots/02-asa-interface-status.png) | ASA interface status |
| [`03-asa-configuration.png`](screenshots/03-asa-configuration.png) | ASA interface and ACL configuration |
| [`04-attacker-blocked-from-inside.png`](screenshots/04-attacker-blocked-from-inside.png) | Outside host's ping to the inside network timing out |
| [`05-inside-switch-port-security.png`](screenshots/05-inside-switch-port-security.png) | Port-security status on the inside switch |
| [`06-attacker-ping-test.png`](screenshots/06-attacker-ping-test.png) | Attacker ping test in the command prompt |
| [`07-dmz-http-service.png`](screenshots/07-dmz-http-service.png) | HTTP service enabled on the DMZ server |
| [`08-topology-validation.png`](screenshots/08-topology-validation.png) | Additional topology and test context |
| [`09-http-browser-test.png`](screenshots/09-http-browser-test.png) | Browser test against the DMZ server |

## How to reproduce

The Packet Tracer project file is not included. The addressing plan, configs and screenshots in this repo contain everything needed to rebuild the lab.

1. Rebuild the topology in Cisco Packet Tracer using the diagram in `screenshots/01-topology.png` (one ASA 5505, two 2960 switches, two employee PCs, one attacker PC and one server).
2. Check the IP addresses and gateways against the addressing plan above.
3. On `SRV-DMZ`, go to **Services > HTTP** and make sure HTTP is on.
4. On `FW-ASA`, apply the configs from `configs/` and run:
   ```
   show interface ip brief
   show running-config
   show access-list
   ```
5. On both switches, apply the port-security configs and run:
   ```
   show port-security
   show port-security address
   ```
6. From `PC-EMPLOYEE1`, run `ping 192.168.10.11`.
7. From `PC-ATTACKER`, run `ping 192.168.10.10` (expect a timeout), then open `http://192.168.20.10` in the browser.
8. Run `show access-list` before and after step 7 and compare the hit counters.
9. Record each result as a row in `monitoring/monitoring-log.csv` and run `python analyse_monitoring.py` from the `monitoring/` folder.

## Repository structure

```
.
├── README.md
├── configs/
│   ├── asa-acl.txt
│   ├── asa-interface-summary.txt
│   ├── inside-switch-port-security.txt
│   └── outside-switch-port-security.txt
├── monitoring/
│   ├── analyse_monitoring.py
│   └── monitoring-log.csv
└── screenshots/
```

## Limitations and next steps

This is a learning lab in a simulator, not a production design. It uses a single firewall and one permitted outside host. There is no live monitoring: the ASA doesn't send logs anywhere, and the analysis script reads results I recorded by hand.

What I plan to improve next:

- Add an explicit `deny ip any any` line to the ACL so blocked traffic produces a hit counter, then confirm the blocked ping with it
- Repeat the HTTP test several times and record every run in the CSV
- Add a column to the CSV that records whether ACL counters were checked, so a confirmed block can be marked `PASS`
- Send ASA logs to a syslog server so denied traffic is visible

## Skills demonstrated

Network segmentation · Cisco ASA firewall configuration · Access control lists · DMZ design · Switch port security · Network troubleshooting · Basic Python scripting · Technical documentation

## Author

**Tharun Kumaran M**
[LinkedIn](https://www.linkedin.com/in/tharunkumaran11) · [GitHub](https://github.com/tharunkumaran11)
