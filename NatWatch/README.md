# Overview
NATWatch is a lightweight Python automation tool designed to detect and alert on unexpected changes to the NAT table on a Linux system. 

It generates a diff against the last known state. If any rules are added or removed, the script sends a Discord webhook alert with a human-readable summary and a diff. 

## Why This Matters
NAT rules can be silently modified by attackers, and these changes go unnoticed because NAT rules have no built-in audit log and they persist until reboot. NATWatch solves this by giving NAT a detection pipeline. 

## How It Works
1. Captures NAT rules using `iptables-save -t nat` 
2. Filters out comments/noise.
3. Loads previous snapshot from a JSON file.
4. Compares: 
* Added rules
* Removed rules
* Full unified diff
5. Sends alert through a Discord webhook.
6. Saves new state for future comparisons. 

