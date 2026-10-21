# Network Security and Monitoring Lab — Cisco Packet Tracer

A Cisco Packet Tracer lab demonstrating network segmentation with an ASA 5505 firewall, a DMZ web server, inside employee endpoints, an outside test host, and switch port security.

> **Interview accuracy note:** This repository documents the configured design and the evidence captured during the lab. Packet Tracer tests can be inconsistent, so claims below distinguish configured controls from observed test results. Do not claim that an ACL hit counter proves a packet was blocked unless the counter visibly increments during that exact test.

## Project goals

- Separate the outside, inside, and DMZ networks.
- Publish a web service in the DMZ rather than placing it directly on the employee LAN.
- Apply an outside-in ACL that permits the specified outside host to access the DMZ web server over HTTP and permits ICMP to that server for lab testing.
- Use switch port security with sticky MAC learning and a maximum of one MAC address on selected access ports.
- Validate employee-to-employee connectivity and demonstrate an outside-to-inside attempt that times out.

## Topology

![Packet Tracer topology](screenshots/01-topology.png)

Devices:
- `FW-ASA` — Cisco ASA 5505, ASA 8.4(2)
- `SW-OUTSIDE` — Cisco 2960 access switch
- `SW-INSIDE` — Cisco 2960 access switch
- `PC-ATTACKER` — outside test host
- `PC-EMPLOYEE1`, `PC-EMPLOYEE2` — inside endpoints
- `SRV-DMZ` — DMZ web server

## Addressing plan

| Device / interface | Address | Default gateway / role |
|---|---:|---|
| ASA outside (Vlan2) | `203.0.113.1/24` | Outside gateway |
| PC-ATTACKER | `203.0.113.10/24` | `203.0.113.1` |
| ASA inside (Vlan1) | `192.168.10.1/24` | Inside gateway |
| PC-EMPLOYEE1 | `192.168.10.10/24` | `192.168.10.1` |
| PC-EMPLOYEE2 | `192.168.10.11/24` | `192.168.10.1` |
| ASA DMZ (Vlan3) | `192.168.20.1/24` | DMZ gateway |
| SRV-DMZ | `192.168.20.10/24` | `192.168.20.1` |

The `203.0.113.0/24` range is reserved for documentation/examples and is used here as a simulated outside network.

## Security design

### ASA interface zones

| ASA VLAN | Nameif | Security level | Subnet |
|---|---|---:|---|
| Vlan1 | `inside` | 100 | `192.168.10.0/24` |
| Vlan2 | `outside` | 0 | `203.0.113.0/24` |
| Vlan3 | `dmz` | 50 | `192.168.20.0/24` |

The saved configuration includes `no forward interface Vlan1` under Vlan3. This is an ASA 5505/Packet Tracer-specific forwarding restriction in this lab and should be discussed honestly if asked; it can affect traffic between the DMZ and inside network.

### Outside access control list

The configured ACL rules are:

```text
access-list OUTSIDE-IN extended permit tcp host 203.0.113.10 host 192.168.20.10 eq www
access-list OUTSIDE-IN extended permit icmp host 203.0.113.10 host 192.168.20.10
access-group OUTSIDE-IN in interface outside
```

Meaning:
- Permit TCP HTTP (destination port 80) from `203.0.113.10` to `192.168.20.10`.
- Permit ICMP from that same outside host to the DMZ server for lab testing.
- Apply the ACL inbound on the outside interface.
- Other outside-initiated traffic is not explicitly permitted by these ACL entries and is subject to the ASA's inbound ACL behavior.

**Important:** The HTTP and ICMP permits are narrow host-to-host rules, not unrestricted access to the DMZ or inside LAN. A screenshot showing an ACL line with `hitcnt=0` means that screenshot does **not** prove that rule matched traffic at that moment.

### Switch port security

Selected access ports use:
- `switchport mode access`
- `switchport port-security`
- `switchport port-security maximum 1`
- `switchport port-security violation restrict`
- `switchport port-security mac-address sticky`

Sticky MAC learning binds the port to the first learned endpoint MAC address. `restrict` drops frames from a violating MAC and increments the violation counter without shutting the port down. The screenshots show secure-up status, one learned sticky MAC, and zero violations at the time of capture.

## Evidence and validation

The `screenshots/` folder contains selected original Packet Tracer screenshots. Screenshots are included as evidence, not edited or altered.

| Evidence | What it supports | What it does not prove by itself |
|---|---|---|
| `01-topology.png` | Device layout and zone design | That every path works |
| `02-asa-interface-status.png` | ASA Ethernet/VLAN interface status at capture time | End-to-end application reachability |
| `03-asa-configuration.png` | Visible ASA interface and ACL configuration | ACL rule hit or packet drop unless the counter/log demonstrates it |
| `04-attacker-blocked-from-inside.png` | An outside host's ping attempt to `192.168.10.10` timed out | The exact drop reason; a timeout can have multiple causes |
| `05-inside-switch-port-security.png` | Port-security status for inside access ports | Protection against every possible attack |
| `06-attacker-ping-test.png` | The outside-to-inside test result captured in the command prompt | That an ACL counter incremented during the test |
| `07-dmz-http-service.png` | HTTP service is enabled on the DMZ server | Successful access from every client/zone |
| `08-topology-validation.png` | Additional Packet Tracer topology/test context | A complete security audit |
| `09-http-browser-test.png` | Browser evidence captured during testing | Consistent HTTP success unless the page is visibly loaded in that screenshot |

### Observed results to discuss

- Employee-to-employee ping succeeded in the captured test.
- The outside host's ping attempt to employee host `192.168.10.10` timed out in the captured test.
- Switch port security was enabled on the shown access ports; one sticky MAC was learned and the violation counter was zero at capture time.
- The DMZ server's HTTP service was enabled.
- HTTP access was observed working during one test, but subsequent tests were inconsistent. Therefore, the repository does **not** claim repeatable HTTP reachability or use the zero ACL hit counter as proof of a successful ACL match.

If you want to make a stronger claim during a live interview, reproduce the test in Packet Tracer and capture `show access-list` immediately before and after the traffic. A rising hit counter is stronger evidence that the matching ACL rule processed the traffic. For a failed outside-to-inside test, capture the failed ping and, where supported by Packet Tracer, the relevant ACL/counter evidence.

## Reproduction walkthrough

1. Open `project-3.pkt` in Cisco Packet Tracer. The `.pkt` file is not included in this package because it was not uploaded as a file attachment; add your saved Packet Tracer project file to the repository before publishing if you want reviewers to open the simulation.
2. Confirm the IP addresses and default gateways against the table above.
3. On `SRV-DMZ`, open **Services → HTTP** and confirm HTTP is On.
4. On `FW-ASA`, inspect:
   ```text
   show interface ip brief
   show running-config
   show access-list
   ```
5. On `SW-OUTSIDE` and `SW-INSIDE`, inspect:
   ```text
   show port-security
   show port-security address
   show running-config
   ```
6. From `PC-EMPLOYEE1`, run `ping 192.168.10.11` to demonstrate the recorded inside endpoint connectivity.
7. From `PC-ATTACKER`, run `ping 192.168.10.10` and record the result. A timeout is the observed outcome in the included evidence, but it is not sufficient by itself to attribute the drop to one specific control.
8. From `PC-ATTACKER`, open the browser and try `http://192.168.20.10`. Record the actual result from the current run; do not infer success from a previous run.
9. Run `show access-list` before and after a test and compare hit counters. Only report a rule match if the relevant counter increases.

## Interview demonstration script (about 2 minutes)

1. **Introduce the problem:** “This lab demonstrates basic network segmentation and access control in Packet Tracer. I separated employee endpoints, an outside test host, and a DMZ web server.”
2. **Show the topology:** Point out the ASA and the three logical zones: inside, outside, and DMZ.
3. **Explain least privilege:** “The outside ACL is written as a host-specific permit for HTTP to the DMZ server, with ICMP added for troubleshooting. It is not a general permit to the employee subnet.”
4. **Show the firewall configuration:** Explain the interface names/security levels and the inbound ACL. Mention that a zero hit counter is not evidence of a rule match.
5. **Show port security:** Explain sticky MAC, maximum one MAC, and restrict mode on access ports.
6. **Show the tests:** Employee-to-employee ping succeeded; the captured attacker-to-inside ping timed out. Explain that a timeout is an observed result, while the exact drop cause should be confirmed with counters/logs.
7. **Close with limitations:** “This is a learning simulation, not a production deployment. I would repeat the end-to-end tests and collect before/after counters to prove each policy path consistently.”

## Repository structure

```text
network-security-monitoring-lab/
├── README.md
├── .gitignore
├── configs/
│   ├── asa-acl.txt
│   ├── asa-interface-summary.txt
│   ├── outside-switch-port-security.txt
│   └── inside-switch-port-security.txt
├── docs/
│   ├── addressing-plan.md
│   └── interview-questions.md
└── screenshots/
    └── selected Packet Tracer evidence
```

## Scope and limitations

This is a Packet Tracer learning project. It demonstrates configuration concepts and selected observed tests; it is not a claim of exhaustive security testing, production hardening, or guaranteed repeatable reachability. The Packet Tracer `.pkt` file should be added by the author if it is to be distributed with this repository.
