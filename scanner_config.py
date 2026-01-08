#!/usr/bin/env python3
"""
Advanced Configuration File for Automation Scanner
Customize tools, parameters, and execution settings
"""

# Tool configurations with default parameters
TOOLS_CONFIG = {
    'dns': {
        'assetfinder': {
            'enabled': True,
            'commands': [
                'assetfinder {target}',
                'assetfinder {target} | sort -u',
            ]
        },
        'dnsrecon': {
            'enabled': True,
            'commands': [
                'dnsrecon -d {target} -t std',
                'dnsrecon -d {target} -t axfr',
                'dnsrecon -d {target} -t srv',
                'dnsrecon -d {target} -t dnssec',
            ]
        },
        'host': {
            'enabled': True,
            'commands': [
                'host -t A {target}',
                'host -t AAAA {target}',
                'host -t MX {target}',
                'host -t NS {target}',
                'host -t TXT {target}',
                'host -t SOA {target}',
                'host -a {target}',
            ]
        },
        'dig': {
            'enabled': True,
            'commands': [
                'dig +short {target}',
                'dig {target} ANY',
                'dig +trace {target}',
                'dig +dnssec {target}',
            ]
        },
        'nslookup': {
            'enabled': True,
            'commands': [
                'nslookup -type=A {target}',
                'nslookup -type=MX {target}',
                'nslookup -type=NS {target}',
                'nslookup -type=TXT {target}',
            ]
        },
        'dnsenum': {
            'enabled': True,
            'commands': [
                'dnsenum {target}',
                'dnsenum --enum --brute-force {target}',
            ]
        },
    },
    'subdomains': {
        'findomain': {
            'enabled': True,
            'commands': [
                'findomain -t {target} --all',
                'findomain -t {target} --ip',
            ]
        },
        'sublister': {
            'enabled': True,
            'commands': [
                'sublister -d {target}',
                'sublister -d {target} --bruteforce',
            ]
        },
        'theharvester': {
            'enabled': True,
            'commands': [
                'theHarvester -d {target} -b google -l 100',
                'theHarvester -d {target} -b crtsh -l 100',
                'theHarvester -d {target} -b certspotter -l 100',
            ]
        },
    },
    'ssl_tls': {
        'testssl': {
            'enabled': True,
            'commands': [
                'testssl --full https://{target}',
            ]
        },
        'sslyze': {
            'enabled': True,
            'commands': [
                'sslyze {target}:443 --regular --certinfo=basic',
            ]
        },
        'sslscan': {
            'enabled': True,
            'commands': [
                'sslscan {target}:443',
                'sslscan --tls1_3 {target}:443',
            ]
        },
        'openssl': {
            'enabled': True,
            'commands': [
                'openssl s_client -connect {target}:443 -showcerts',
            ]
        },
    },
    'web': {
        'whatweb': {
            'enabled': True,
            'commands': [
                'whatweb http://{target}',
                'whatweb -v http://{target}',
            ]
        },
        'wpscan': {
            'enabled': True,
            'commands': [
                'wpscan --url http://{target}',
                'wpscan --url http://{target} --enumerate p,t,u,vp,vt',
            ]
        },
        'corsy': {
            'enabled': True,
            'commands': [
                'corsy -u http://{target}',
                'corsy -u http://{target} --check-all',
            ]
        },
    },
    'vulnerability': {
        'xsstrike': {
            'enabled': True,
            'commands': [
                'xsstrike -u http://{target} --crawl',
            ]
        },
        'dalfox': {
            'enabled': True,
            'commands': [
                'dalfox scan --url http://{target}',
            ]
        },
        'xsser': {
            'enabled': True,
            'commands': [
                'xsser -u http://{target}',
            ]
        },
        'commix': {
            'enabled': True,
            'commands': [
                'commix -u "http://{target}?id=1" --batch',
            ]
        },
    },
    'network': {
        'ping': {
            'enabled': True,
            'commands': [
                'ping -c 4 {target}',
            ]
        },
        'traceroute': {
            'enabled': True,
            'commands': [
                'traceroute -n {target}',
                'traceroute -m 30 {target}',
            ]
        },
        'whois': {
            'enabled': True,
            'commands': [
                'whois {target}',
            ]
        },
        'nmap': {
            'enabled': True,
            'commands': [
                'nmap -F {target}',
                'nmap -sV {target}',
                'nmap --script vuln {target}',
            ]
        },
    },
}

# Execution settings
EXECUTION_SETTINGS = {
    'timeout_per_command': None,  # No timeout - let tools run indefinitely
    'retry_failed': True,
    'max_retries': 2,
    'parallel_execution': False,  # Be careful with this
    'delay_between_commands': 0.5,  # seconds
    'log_level': 'INFO',  # DEBUG, INFO, WARN, ERROR
    'save_all_outputs': True,
    'generate_json_report': True,
    'generate_html_report': False,
}

# Optional: Specify wordlists for directory busting
WORDLISTS = {
    'common': '/usr/share/wordlists/dirb/common.txt',
    'big': '/usr/share/wordlists/dirb/big.txt',
    'apache': '/usr/share/wordlists/dirb/apache.txt',
}

# Custom headers for HTTP requests
CUSTOM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
}

# Proxy settings (optional)
PROXY_SETTINGS = {
    'use_proxy': False,
    'proxy_url': 'http://127.0.0.1:8080',
    'use_tor': False,
}
