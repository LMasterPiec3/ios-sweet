#!/usr/bin/env python3
"""Add a standard Wi-Fi service (en0, AirPort, DHCP) to the iOS SCPreferences.

    tools/prep-wifi-preferences.py <mounted-ios-root>

configd only runs DHCP/routing on en0 if preferences.plist carries a network
service for it (research/wifi-sc-0145 did the same by hand on the dev phone:
en0, AirPort, IPv4 DHCP, IPv6 Automatic). Existing keys — including the
HostNames dict configd writes — are preserved; only the service and the
ServiceOrder are added. Idempotent: a service on en0 with ConfigMethod DHCP
is left untouched.
"""
import os
import plistlib
import sys
import uuid

SVC = 'A1E2D3C4-0000-4B5B-8C8C-E0E0E0E0E0E0'  # stable UUID-shaped id; SCPreferences only needs uniqueness


def load(path):
    with open(path, 'rb') as f:
        return plistlib.load(f)


def save(path, data):
    with open(path, 'wb') as f:
        plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)


def main():
    args = sys.argv[1:]
    if args and args[0] == '--file':
        # live mode: operate on a pulled preferences.plist copy directly
        path = args[1]
    else:
        root = args[0]
        path = os.path.join(root, 'private/var/preferences/SystemConfiguration/preferences.plist')
    if os.path.exists(path):
        prefs = load(path)
    else:
        prefs = {'SetByHost': {}, 'System': {'System': {}, 'Network': {}}}
    system = prefs.setdefault('System', {})
    net = system.setdefault('Network', {})
    services = net.setdefault('Services', {})

    existing = {k for k, v in services.items()
                if isinstance(v, dict) and v.get('Interface', {}).get('DeviceName') == 'en0'}
    if existing:
        print(f'Wi-Fi service already present: {sorted(existing)}')
        return

    services[SVC] = {
        'DNS': {},
        'Interface': {
            'DeviceName': 'en0',
            'Hardware': 'com.apple.AirPort.driver',
            'Type': 'IEEE80211',
            'UserDefinedName': 'Wi-Fi',
        },
        'IPv4': {'ConfigMethod': 'DHCP'},
        'IPv6': {'ConfigMethod': 'Automatic'},
        'Proxies': {
            'EnableSOCKS': 0,
            'ExceptionsList': ['*.local', '169.254/16'],
            'FTPPassive': 1,
        },
    }
    net.setdefault('Global', {}).setdefault('IPv4', {})['ServiceOrder'] = [SVC]
    system.setdefault('System', {}).setdefault('ComputerName', 'iPhone')
    system['System'].setdefault('ComputerNameEncoding', 0)
    save(path, prefs)
    print(f'Wi-Fi service added: {SVC}')


if __name__ == '__main__':
    main()
