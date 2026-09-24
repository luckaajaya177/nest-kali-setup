#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NestExecutor - Universal Roblox Script Executor
Cross-platform: Windows, macOS, Linux, Android, iOS
Version: 1.0.0
"""

import sys
import argparse
import json
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from executor import (
    ExecutorFactory,
    ScriptManager,
    EXECUTOR_NAME,
    VERSION,
)


def main():
    parser = argparse.ArgumentParser(
        description=f"{EXECUTOR_NAME} v{VERSION} - Universal Roblox Script Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --status                    Show executor status
  %(prog)s --inject                    Inject into Roblox
  %(prog)s --script script.luau --execute  Load and execute script
  %(prog)s --list                      List loaded scripts
  %(prog)s --platform android          Target Android platform
        """
    )
    
    parser.add_argument("--platform", 
                       choices=["auto", "windows", "macos", "linux", "android", "ios"],
                       default="auto",
                       help="Target platform (default: auto-detect)")
    parser.add_argument("--inject", action="store_true", help="Inject into Roblox")
    parser.add_argument("--uninject", action="store_true", help="Unload executor")
    parser.add_argument("--list", action="store_true", help="List loaded scripts")
    parser.add_argument("--status", action="store_true", help="Show executor status")
    parser.add_argument("--script", type=str, help="Script file to load")
    parser.add_argument("--execute", action="store_true", help="Execute loaded script")
    parser.add_argument("--output", type=str, help="Output format (text/json)")
    
    args = parser.parse_args()
    
    # Create executor
    platform = None if args.platform == "auto" else args.platform
    executor = ExecutorFactory.create(platform)
    
    # Print header
    print(f"\n{'='*50}")
    print(f"  {EXECUTOR_NAME} v{VERSION}")
    print(f"  {executor.platform_config.name} ({executor.platform_config.arch})")
    print(f"{'='*50}\n")
    
    # Handle commands
    if args.status:
        stats = executor.get_stats()
        if args.output == "json":
            print(json.dumps(stats, indent=2))
        else:
            print(f"Platform: {stats['platform']}")
            print(f"Arch: {stats['arch']}")
            print(f"Injected: {stats['injected']}")
            print(f"Scripts Loaded: {stats['scripts_loaded']}")
            print(f"Total Executions: {stats['total_executions']}")
        return
    
    if args.inject:
        print("[*] Injecting into Roblox...", end=" ")
        if executor.inject():
            print("SUCCESS")
            executor.is_injected = True
        else:
            print("FAILED")
            sys.exit(1)
        return
    
    if args.uninject:
        print("[*] Uninjecting...", end=" ")
        if executor.unload():
            print("SUCCESS")
        else:
            print("FAILED or not injected")
        return
    
    if args.script:
        manager = ScriptManager(executor)
        try:
            script = manager.load_from_file(args.script)
            print(f"[+] Loaded: {script.name}")
            print(f"    Hash: {script.hash}")
            print(f"    Size: {script.size} bytes")
            print(f"    Category: {script.category}")
            
            if args.execute:
                if executor.is_injected:
                    print(f"\n[*] Executing {script.name}...")
                    result = executor.execute_script(script)
                    
                    if result.success:
                        print(f"[+] Success ({result.execution_time:.3f}s)")
                        if result.output:
                            print(f"    Output: {result.output}")
                    else:
                        print(f"[-] Error: {result.error}")
                else:
                    print("[!] Error: Not injected. Run --inject first.")
        except FileNotFoundError as e:
            print(f"[-] {e}")
            sys.exit(1)
        return
    
    if args.list:
        scripts = executor.list_scripts()
        if not scripts:
            print("[*] No scripts loaded.")
        else:
            print(f"[*] Loaded {len(scripts)} scripts:\n")
            for s in scripts:
                status = "✓" if s.enabled else "✗"
                last_exec = ""
                if s.last_executed:
                    from datetime import datetime
                    last_exec = datetime.fromtimestamp(s.last_executed).strftime("%H:%M:%S")
                print(f"  [{status}] {s.name:30} ({s.hash}) - {s.size} bytes  Executed: {s.execution_count}x  Last: {last_exec}")
        return
    
    parser.print_help()
    print()


if __name__ == "__main__":
    main()
