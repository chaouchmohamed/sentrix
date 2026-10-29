#!/usr/bin/env bash
set -euo pipefail
# Block egress from the honeynet subnet, but allow replies to inbound (playbook Step D).
SUBNET=172.28.0.0/24
sudo iptables -I DOCKER-USER -s "$SUBNET" -d "$SUBNET" -j DROP
sudo iptables -I DOCKER-USER -s "$SUBNET" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
echo "[firewall] egress from $SUBNET blocked (replies allowed)."
