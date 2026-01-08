#!/usr/bin/env python3
"""
Custom Tool Installer Module
Allows users to add new tools to the scanner with interactive setup
"""

import subprocess
import json
import sys
from pathlib import Path


class CustomToolInstaller:
    """Interactive tool installer for adding custom security tools"""
    
    INSTALL_METHODS = {
        'pip': {
            'name': 'Python Package (pip)',
            'cmd_template': 'pip install {package}',
            'verify_cmd': '{tool} --version'
        },
        'apt': {
            'name': 'Ubuntu/Debian Package (apt)',
            'cmd_template': 'sudo apt-get install -y {package}',
            'verify_cmd': 'which {tool}'
        },
        'git': {
            'name': 'Git Clone & Setup',
            'cmd_template': 'git clone {url} && cd {folder} && python setup.py install',
            'verify_cmd': '{tool} --version'
        },
        'manual': {
            'name': 'Manual/Custom Setup',
            'cmd_template': 'Instructions will be saved for manual execution',
            'verify_cmd': '{tool} --version'
        },
        'brew': {
            'name': 'Homebrew (macOS)',
            'cmd_template': 'brew install {package}',
            'verify_cmd': 'which {tool}'
        }
    }
    
    def __init__(self, tool_manager):
        self.tool_manager = tool_manager
        self.config_file = Path('custom_tools.json')
        self.custom_tools = self._load_custom_tools()
    
    def _load_custom_tools(self) -> dict:
        """Load custom tools configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_custom_tools(self):
        """Save custom tools configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.custom_tools, f, indent=2)
    
    def interactive_add_tool(self):
        """Interactive prompt to add a new tool"""
        print("\n" + "="*70)
        print("CUSTOM TOOL INSTALLER")
        print("="*70)
        
        # Get tool name
        tool_name = input("\nEnter tool name (e.g., 'nikto', 'zap'): ").strip().lower()
        if not tool_name:
            print("[ERROR] Tool name cannot be empty")
            return False
        
        if tool_name in self.tool_manager.tool_database:
            print(f"[ERROR] Tool '{tool_name}' already exists in database")
            return False
        
        # Get tool category
        print("\nAvailable categories:")
        categories = ['DNS', 'Network', 'SSL/TLS', 'Web', 'Directory', 'Vulnerabilities', 'Other']
        for i, cat in enumerate(categories, 1):
            print(f"  [{i}] {cat}")
        
        cat_choice = input("Select category (1-7, default=7): ").strip() or "7"
        try:
            category = categories[int(cat_choice) - 1]
        except:
            category = 'Other'
        
        # Get description
        description = input("Enter tool description: ").strip() or f"Custom tool: {tool_name}"
        
        # Get installation method
        print("\nInstallation methods:")
        methods_list = list(self.INSTALL_METHODS.keys())
        for i, method in enumerate(methods_list, 1):
            print(f"  [{i}] {self.INSTALL_METHODS[method]['name']}")
        
        method_choice = input(f"Select method (1-{len(methods_list)}): ").strip()
        try:
            install_method = methods_list[int(method_choice) - 1]
        except:
            print("[ERROR] Invalid choice")
            return False
        
        # Get method-specific info
        tool_config = {
            'apt': None,
            'pip': None,
            'brew': None,
            'go': None,
            'category': category,
            'description': description,
            'custom': True,
            'install_method': install_method
        }
        
        if install_method == 'pip':
            package = input("Enter pip package name: ").strip()
            if not package:
                print("[ERROR] Package name required")
                return False
            tool_config['pip'] = package
            install_cmd = f"pip install {package}"
        
        elif install_method == 'apt':
            package = input("Enter apt package name: ").strip()
            if not package:
                print("[ERROR] Package name required")
                return False
            tool_config['apt'] = package
            install_cmd = f"sudo apt-get install -y {package}"
        
        elif install_method == 'git':
            url = input("Enter git repository URL: ").strip()
            if not url:
                print("[ERROR] Repository URL required")
                return False
            folder = input("Enter folder name after clone: ").strip() or tool_name
            tool_config['git_url'] = url
            tool_config['git_folder'] = folder
            install_cmd = f"git clone {url} && cd {folder} && python setup.py install"
        
        elif install_method == 'brew':
            package = input("Enter brew package name: ").strip()
            if not package:
                print("[ERROR] Package name required")
                return False
            tool_config['brew'] = package
            install_cmd = f"brew install {package}"
        
        else:  # manual
            instructions = input("Enter installation instructions (or press Enter for help): ").strip()
            tool_config['manual_instructions'] = instructions or f"Visit the project page and follow setup instructions"
            install_cmd = "MANUAL_SETUP"
        
        # Verify command
        verify_cmd = input(f"Enter verification command (e.g., '{tool_name} --version', default=which {tool_name}): ").strip()
        if not verify_cmd:
            verify_cmd = f"which {tool_name}"
        
        tool_config['verify_cmd'] = verify_cmd
        
        # Confirm before saving
        print("\n" + "="*70)
        print("TOOL CONFIGURATION SUMMARY")
        print("="*70)
        print(f"Tool Name:        {tool_name}")
        print(f"Category:         {category}")
        print(f"Description:      {description}")
        print(f"Install Method:   {install_method}")
        print(f"Install Command:  {install_cmd}")
        print(f"Verify Command:   {verify_cmd}")
        print("="*70)
        
        confirm = input("\nSave this tool? (y/n, default=y): ").strip().lower() or "y"
        if confirm != 'y':
            print("[CANCELLED] Tool not added")
            return False
        
        # Save to custom tools
        self.custom_tools[tool_name] = tool_config
        self._save_custom_tools()
        
        # Add to tool_manager database
        self.tool_manager.tool_database[tool_name] = tool_config
        
        print(f"\n[SUCCESS] Tool '{tool_name}' added successfully!")
        print(f"Saved to: {self.config_file}")
        
        # Offer to install now
        install_now = input("\nInstall now? (y/n, default=n): ").strip().lower() or "n"
        if install_now == 'y':
            self._install_tool_now(tool_name, install_cmd, verify_cmd)
        
        return True
    
    def _install_tool_now(self, tool_name: str, install_cmd: str, verify_cmd: str):
        """Attempt to install tool immediately"""
        if install_cmd == "MANUAL_SETUP":
            print("\n[INFO] Manual setup required. Please install manually and run:")
            print(f"  {verify_cmd}")
            return False
        
        print(f"\n[*] Installing {tool_name}...")
        print(f"    Command: {install_cmd}")
        
        try:
            result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"[+] Installation attempt completed")
                
                # Verify installation
                print(f"[*] Verifying installation...")
                verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if verify_result.returncode == 0:
                    print(f"[+] {tool_name} verified successfully!")
                    return True
                else:
                    print(f"[!] Verification failed. Tool may not be installed correctly.")
                    print(f"    Try running: {verify_cmd}")
                    return False
            else:
                print(f"[-] Installation failed")
                print(f"    Error: {result.stderr or result.stdout}")
                return False
        
        except subprocess.TimeoutExpired:
            print(f"[-] Installation timed out (>5 min)")
            return False
        except Exception as e:
            print(f"[-] Installation error: {str(e)}")
            return False
    
    def list_custom_tools(self):
        """List all added custom tools"""
        if not self.custom_tools:
            print("\n[INFO] No custom tools added yet")
            return
        
        print("\n" + "="*70)
        print("CUSTOM TOOLS")
        print("="*70)
        for name, config in self.custom_tools.items():
            print(f"\n✓ {name}")
            print(f"  Category:     {config.get('category', 'N/A')}")
            print(f"  Description:  {config.get('description', 'N/A')}")
            print(f"  Method:       {config.get('install_method', 'N/A')}")
    
    def remove_custom_tool(self, tool_name: str) -> bool:
        """Remove a custom tool"""
        if tool_name not in self.custom_tools:
            print(f"[ERROR] Custom tool '{tool_name}' not found")
            return False
        
        confirm = input(f"Remove tool '{tool_name}'? (y/n): ").strip().lower()
        if confirm == 'y':
            del self.custom_tools[tool_name]
            if tool_name in self.tool_manager.tool_database:
                del self.tool_manager.tool_database[tool_name]
            self._save_custom_tools()
            print(f"[SUCCESS] Tool '{tool_name}' removed")
            return True
        return False


def custom_tool_menu(tool_manager):
    """Interactive menu for custom tool management"""
    while True:
        print("\n" + "="*70)
        print("CUSTOM TOOL MANAGER")
        print("="*70)
        print("Options:")
        print("  [1] Add new tool")
        print("  [2] List custom tools")
        print("  [3] Remove tool")
        print("  [4] Back to main menu")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        installer = CustomToolInstaller(tool_manager)
        
        if choice == "1":
            installer.interactive_add_tool()
        elif choice == "2":
            installer.list_custom_tools()
        elif choice == "3":
            tool_name = input("Enter tool name to remove: ").strip().lower()
            installer.remove_custom_tool(tool_name)
        elif choice == "4":
            break
        else:
            print("[ERROR] Invalid choice")


if __name__ == '__main__':
    # Test mode
    print("Custom Tool Installer Module")
    print("This module is meant to be imported and used by automation_scanner_v2.py")
