# Firewall and Switch Monitoring Plan

## Purpose
This folder adds a lightweight, evidence-based monitoring workflow to the Cisco ASA DMZ firewall lab. It records observations collected manually from Cisco Packet Tracer and analyses the recorded CSV data.

> Scope: this is a manual monitoring and reporting workflow. The Python script does not connect to Packet Tracer or collect live ASA/switch telemetry.

## 1. ASA ACL counters
After running a traffic test, open the ASA CLI and try:

```text
enable
show access-list
```

Record the ACL rule, hit count, test traffic, and observation time. On ASA software, `show access-list` displays ACL entries and hit counters; command support can vary in Packet Tracer's simplified ASA implementation.

For this lab, the outside ACL is intended to permit HTTP from outside host `203.0.113.10` to DMZ server `192.168.20.10` and ICMP from that host to that server. Only mark a rule verified if the observed test and counters support that conclusion.

## 2. Switch port-security status
On the relevant switch CLI, use commands supported by your Packet Tracer switch, for example:

```text
show port-security
show port-security interface fa0/1
```

Record port status, maximum secure MAC addresses, learned/sticky addresses, and violation count. Use the actual interface and command output from your lab.

## 3. Controlled test procedure
1. Record baseline ACL counters and port-security violation counts.
2. Run one known test (for example, an allowed HTTP test or blocked outside-to-inside ping).
3. Record the actual result—not just the expected result.
4. Re-check counters and port-security status.
5. If results contradict expectations, mark the test `INVESTIGATE` and capture a screenshot.

## Event classifications
- `PASS`: actual outcome matches expected outcome and evidence was observed.
- `INVESTIGATE`: actual outcome differs from expected, evidence is missing, or counters did not change as expected.
- `ALERT`: a port-security violation was observed, or a test suggests traffic may have bypassed the intended policy. Confirm the result before reporting an incident.

Save genuine screenshots under `screenshots/`, e.g. `2026-10-26_acl-counter-after-http.png`. Do not create or edit screenshots to imply results that were not observed.
