#!/bin/bash
set -euxo pipefail

dnf install -y iptables-services

cat > /etc/sysctl.d/99-nat.conf <<EOF
net.ipv4.ip_forward=1
EOF

sysctl --system

IFACE=$(ip route show default | awk '{print $5}')

iptables -t nat -A POSTROUTING -o "$IFACE" -j MASQUERADE
iptables -A FORWARD -s 10.0.0.0/16 -o "$IFACE" -j ACCEPT
iptables -A FORWARD -d 10.0.0.0/16 -i "$IFACE" \
  -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -P FORWARD DROP

systemctl enable --now iptables
service iptables save