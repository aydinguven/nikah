#!/bin/bash

# Allow port 8080
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT

# Save iptables rules
sudo netfilter-persistent save
sudo netfilter-persistent reload

# Install netfilter-persistent if not already installed
if ! command -v netfilter-persistent &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y iptables-persistent
fi

# Verify the rule was added
sudo iptables -L | grep 8080
