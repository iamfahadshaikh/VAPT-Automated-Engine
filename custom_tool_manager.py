"""
Custom Tool Manager - Allow users to add custom tools to the scanner
Interactive interface for adding new scanning tools
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class CustomToolManager:
    """Manage custom tool installation and configuration"""
    
    CONFIG_FILE = "custom_tools.json"
    
    @staticmethod
    def load_config() -> Dict:
        """Load existing custom tools configuration"""
        if os.path.exists(CustomToolManager.CONFIG_FILE):
            with open(CustomToolManager.CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"tools": []}
    
    @staticmethod
    def save_config(config: Dict) -> None:
        """Save custom tools configuration"""
        with open(CustomToolManager.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def add_custom_tool() -> Optional[Dict]:
        """
        Interactive prompt to add a new custom tool
        
        Returns:
            Tool dict or None if cancelled
        """
        print("\n" + "="*70)
        print("ADD CUSTOM SCANNING TOOL")
        print("="*70)
        
        # Get tool name
        tool_name = input("\n[1/5] Tool name (e.g., 'custom_xss_detector'): ").strip()
        if not tool_name:
            print("Tool name required. Cancelled.")
            return None
        
        # Get tool description
        description = input("[2/5] Description (e.g., 'Custom XSS detection tool'): ").strip()
        
        # Get tool category
        print("\n[3/5] Tool category:")
        categories = ["DNS", "Network", "SSL/TLS", "Web", "Vulnerabilities", "Subdomains", "Directory", "Other"]
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
        
        try:
            cat_idx = int(input("Select category (1-8): ")) - 1
            category = categories[cat_idx] if 0 <= cat_idx < len(categories) else "Other"
        except:
            category = "Other"
        
        # Get installation method
        print("\n[4/5] Installation method:")
        methods = ["pip install", "apt install", "git clone", "manual"]
        for i, method in enumerate(methods, 1):
            print(f"  {i}. {method}")
        
        try:
            method_idx = int(input("Select method (1-4): ")) - 1
            install_method = methods[method_idx] if 0 <= method_idx < len(methods) else "manual"
        except:
            install_method = "manual"
        
        # Get installation command
        if install_method == "manual":
            print("\n[5/5] Manual installation notes:")
            install_cmd = input("Enter installation instructions: ").strip()
        else:
            install_cmd = input(f"[5/5] {install_method} command (e.g., 'pip install tool-name'): ").strip()
        
        # Get command to run
        run_command = input("\nCommand to run tool (e.g., 'tool-name -h'): ").strip()
        
        # Confirm
        print("\n--- SUMMARY ---")
        print(f"Name: {tool_name}")
        print(f"Category: {category}")
        print(f"Description: {description}")
        print(f"Install: {install_cmd}")
        print(f"Run: {run_command}")
        
        confirm = input("\nAdd this tool? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Cancelled.")
            return None
        
        return {
            "name": tool_name,
            "category": category,
            "description": description,
            "install_method": install_method,
            "install_command": install_cmd,
            "run_command": run_command,
            "enabled": True
        }
    
    @staticmethod
    def install_custom_tool(tool: Dict) -> bool:
        """
        Attempt to install a custom tool
        
        Args:
            tool: Tool configuration dict
            
        Returns:
            True if installation successful or confirmed, False otherwise
        """
        print(f"\nInstalling {tool['name']}...")
        print(f"Method: {tool['install_method']}")
        print(f"Command: {tool['install_command']}")
        
        if tool['install_method'] == "manual":
            print("\n⚠️  MANUAL INSTALLATION REQUIRED")
            print(f"Please install manually: {tool['install_command']}")
            proceed = input("\nProceed without tool? (y/n): ").lower().strip()
            return proceed == 'y'
        
        # Attempt automatic installation
        try:
            result = subprocess.run(
                tool['install_command'],
                shell=True,
                capture_output=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"✓ {tool['name']} installed successfully")
                return True
            else:
                print(f"✗ Installation failed: {result.stderr.decode()}")
                proceed = input("\nProceed without tool? (y/n): ").lower().strip()
                return proceed == 'y'
        except subprocess.TimeoutExpired:
            print(f"✗ Installation timeout")
            proceed = input("\nProceed without tool? (y/n): ").lower().strip()
            return proceed == 'y'
        except Exception as e:
            print(f"✗ Installation error: {e}")
            proceed = input("\nProceed without tool? (y/n): ").lower().strip()
            return proceed == 'y'
    
    @staticmethod
    def list_custom_tools() -> None:
        """List all registered custom tools"""
        config = CustomToolManager.load_config()
        tools = config.get("tools", [])
        
        if not tools:
            print("\nNo custom tools registered.")
            return
        
        print("\n" + "="*70)
        print("CUSTOM TOOLS")
        print("="*70)
        
        for i, tool in enumerate(tools, 1):
            status = "✓" if tool.get("enabled") else "✗"
            print(f"\n{i}. {status} {tool['name']} ({tool['category']})")
            print(f"   {tool['description']}")
            print(f"   Run: {tool['run_command']}")
    
    @staticmethod
    def register_custom_tool(tool: Dict) -> bool:
        """Register a custom tool in configuration"""
        try:
            config = CustomToolManager.load_config()
            
            # Check if already exists
            for existing in config.get("tools", []):
                if existing["name"] == tool["name"]:
                    print(f"Tool '{tool['name']}' already registered.")
                    return False
            
            config.setdefault("tools", []).append(tool)
            CustomToolManager.save_config(config)
            print(f"✓ Tool '{tool['name']}' registered")
            return True
        except Exception as e:
            print(f"✗ Registration error: {e}")
            return False
    
    @staticmethod
    def interactive_tool_setup() -> None:
        """Interactive setup for custom tools"""
        while True:
            print("\n" + "="*70)
            print("CUSTOM TOOL SETUP")
            print("="*70)
            print("1. Add new tool")
            print("2. List registered tools")
            print("3. Remove tool")
            print("4. Back to scanner")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                tool = CustomToolManager.add_custom_tool()
                if tool:
                    if CustomToolManager.install_custom_tool(tool):
                        CustomToolManager.register_custom_tool(tool)
            
            elif choice == "2":
                CustomToolManager.list_custom_tools()
            
            elif choice == "3":
                config = CustomToolManager.load_config()
                tools = config.get("tools", [])
                if not tools:
                    print("No tools to remove.")
                    continue
                
                for i, tool in enumerate(tools, 1):
                    print(f"{i}. {tool['name']}")
                
                try:
                    idx = int(input("Select tool to remove (number): ")) - 1
                    if 0 <= idx < len(tools):
                        removed = tools.pop(idx)
                        CustomToolManager.save_config(config)
                        print(f"✓ '{removed['name']}' removed")
                except:
                    print("Invalid selection.")
            
            elif choice == "4":
                break
            
            else:
                print("Invalid option.")
