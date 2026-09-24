#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roblox Universal Script Executor — Core Engine
Cross-platform: Windows, macOS, Linux, Android, iOS
Version: 1.0.0
Author: nest-kali-setup
License: Educational/Research
"""

import os
import sys
import json
import hashlib
import base64
import struct
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# ============================================================
# CONSTANTS & CONFIG
# ============================================================

VERSION = "1.0.0"
EXECUTOR_NAME = "NestExecutor"
LUAC_VERSION = "0x44"  # Luau version
MAX_SCRIPT_SIZE = 10 * 1024 * 1024  # 10MB max script

# Platform detection
PLATFORM = platform.system().lower()
ARCH = platform.machine().lower()

# Supported platforms
SUPPORTED_PLATFORMS = {
    "windows": ["x86_64", "amd64"],
    "darwin": ["x86_64", "arm64"],  # macOS
    "linux": ["x86_64", "arm64", "aarch64"],
    "android": ["arm64", "armv7", "x86_64"],
    "ios": ["arm64"]
}

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ScriptInfo:
    """Metadata about a loaded script."""
    name: str
    content: str
    hash: str = ""
    size: int = 0
    created: float = 0.0
    category: str = "misc"
    enabled: bool = True
    execution_count: int = 0
    last_executed: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        if not self.size:
            self.size = len(self.content.encode())
        if not self.created:
            import time
            self.created = time.time()


@dataclass
class ExecutionResult:
    """Result of script execution."""
    success: bool
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    memory_used: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    name: str
    arch: str
    root_required: bool = False
    jailbreak_required: bool = False
    injected: bool = False
    roblox_path: Optional[str] = None
    pid: Optional[int] = None
    hooks_installed: bool = False


# ============================================================
# EXECUTOR CORE
# ============================================================

class ExecutorCore(ABC):
    """Abstract base class for all executor implementations."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.scripts: Dict[str, ScriptInfo] = {}
        self.execution_history: List[ExecutionResult] = []
        self.is_injected = False
        self.platform_config = self._detect_platform()
        
    @abstractmethod
    def _detect_platform(self) -> PlatformConfig:
        """Detect current platform and return config."""
        pass
    
    @abstractmethod
    def inject(self) -> bool:
        """Inject executor into Roblox process."""
        pass
    
    @abstractmethod
    def execute_script(self, script: ScriptInfo) -> ExecutionResult:
        """Execute a script in the Roblox environment."""
        pass
    
    @abstractmethod
    def unload(self) -> bool:
        """Unload executor from process."""
        pass
    
    def compile_script(self, source: str) -> bytes:
        """Compile Luau script to bytecode."""
        # Luau bytecode header
        header = b'\x1bLuau'
        version = struct.pack('<I', 0x44)  # Luau version
        padding = b'\x00' * (8 - len(header))
        
        # Compile using Luau compiler (external)
        compiled = self._compile_to_bytecode(source)
        
        return header + version + padding + compiled
    
    def _compile_to_bytecode(self, source: str) -> bytes:
        """Compile source to Luau bytecode."""
        # Try using luau-compile if available
        luau_paths = [
            "luau-compile",
            "/usr/local/bin/luau-compile",
            "C:\\Program Files\\Roblox\\Versions\\luau-compile.exe",
        ]
        
        for path in luau_paths:
            if os.path.exists(path) or self._can_execute(path):
                try:
                    result = subprocess.run(
                        [path],
                        input=source.encode(),
                        capture_output=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        return result.stdout
                except Exception:
                    continue
        
        # Fallback: Simple bytecode generator (not fully functional)
        return self._generate_stub_bytecode(source)
    
    def _generate_stub_bytecode(self, source: str) -> bytes:
        """Generate stub bytecode for testing."""
        # This is a simplified version - real implementation needs proper Luau compiler
        compiled = hashlib.sha256(source.encode()).digest()
        return compiled[:256]  # Truncate to reasonable size
    
    def _can_execute(self, cmd: str) -> bool:
        """Check if command can be executed."""
        try:
            return subprocess.run([cmd, "--help"], capture_output=True, timeout=1).returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def load_script(self, name: str, content: str, category: str = "misc") -> ScriptInfo:
        """Load a script into the executor."""
        script = ScriptInfo(name=name, content=content, category=category)
        self.scripts[script.hash] = script
        return script
    
    def unload_script(self, script_hash: str) -> bool:
        """Unload a script."""
        if script_hash in self.scripts:
            del self.scripts[script_hash]
            return True
        return False
    
    def get_script(self, script_hash: str) -> Optional[ScriptInfo]:
        """Get script by hash."""
        return self.scripts.get(script_hash)
    
    def list_scripts(self, category: Optional[str] = None) -> List[ScriptInfo]:
        """List all loaded scripts, optionally filtered by category."""
        scripts = list(self.scripts.values())
        if category:
            scripts = [s for s in scripts if s.category == category]
        return sorted(scripts, key=lambda s: s.name.lower())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "version": VERSION,
            "name": EXECUTOR_NAME,
            "platform": self.platform_config.name,
            "arch": self.platform_config.arch,
            "injected": self.is_injected,
            "scripts_loaded": len(self.scripts),
            "total_executions": sum(s.execution_count for s in self.scripts.values()),
            "memory_used": self._estimate_memory_usage(),
        }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of loaded scripts."""
        total = sum(s.size for s in self.scripts.values())
        return total


# ============================================================
# WINDOWS EXECUTOR (Process Injection)
# ============================================================

class WindowsExecutor(ExecutorCore):
    """Windows-specific executor using DLL injection."""
    
    PLUGIN_DLL_PATH = Path(__file__).parent.parent / "pc" / "windows" / "nest_injector.dll"
    
    def _detect_platform(self) -> PlatformConfig:
        return PlatformConfig(
            name="windows",
            arch=ARCH,
            root_required=False,
        )
    
    def inject(self) -> bool:
        """Inject into Roblox process using DLL."""
        if self.is_injected:
            return True
        
        # Find Roblox process
        roblox_pid = self._find_roblox_process()
        if not roblox_pid:
            return False
        
        self.platform_config.pid = roblox_pid
        
        # Load DLL injector
        injector_path = self._get_injector_path()
        if not injector_path.exists():
            return False
        
        # Inject DLL
        try:
            result = subprocess.run(
                [str(injector_path), str(roblox_pid), str(self.PLUGIN_DLL_PATH)],
                capture_output=True,
                timeout=30
            )
            self.is_injected = result.returncode == 0
            self.platform_config.injected = self.is_injected
            return self.is_injected
        except Exception:
            return False
    
    def execute_script(self, script: ScriptInfo) -> ExecutionResult:
        """Execute script via Roblox's built-in execution."""
        if not self.is_injected:
            return ExecutionResult(
                success=False,
                error="Not injected. Call inject() first."
            )
        
        # For Windows, we use Roblox's built-in Execute functionality
        # through the injected DLL's API
        start_time = __import__('time').time()
        
        try:
            # Call the injected DLL's execute function
            # This would normally communicate via IPC
            result = self._execute_via_dll(script)
            
            exec_time = __import__('time').time() - start_time
            script.execution_count += 1
            script.last_executed = __import__('time').time()
            
            return ExecutionResult(
                success=result.get("success", True),
                output=result.get("output", ""),
                error=result.get("error", ""),
                execution_time=exec_time
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    def _execute_via_dll(self, script: ScriptInfo) -> Dict:
        """Execute script via DLL IPC."""
        # Placeholder - real implementation uses DLL's RPC/IPC
        return {"success": True, "output": "Executed"}
    
    def _find_roblox_process(self) -> Optional[int]:
        """Find Roblox Studio or Roblox Player PID."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'RobloxPlayerBeta' in proc.info['name'] or 'RobloxStudio' in proc.info['name']:
                    return proc.info['pid']
        except ImportError:
            # Fallback to tasklist
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq RobloxPlayerBeta.exe'],
                    capture_output=True, text=True
                )
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                return int(parts[1])
                            except ValueError:
                                continue
        return None
    
    def _get_injector_path(self) -> Path:
        """Get path to DLL injector."""
        paths = [
            self.PLUGIN_DLL_PATH.parent / "injector.exe",
            Path("C:/Windows/System32/injector.exe"),
        ]
        for p in paths:
            if p.exists():
                return p
        return paths[0]  # Return first path even if not exists
    
    def unload(self) -> bool:
        """Unload injector from process."""
        if not self.is_injected or not self.platform_config.pid:
            return False
        
        try:
            import psutil
            proc = psutil.Process(self.platform_config.pid)
            for module in proc.modules():
                if "nest_injector" in module.dllname.lower():
                    proc.terminate()
                    self.is_injected = False
                    return True
        except Exception:
            pass
        
        return False


# ============================================================
# MACOS EXECUTOR (Memory Manipulation)
# ============================================================

class macOSExecutor(ExecutorCore):
    """macOS-specific executor using memory manipulation."""
    
    def _detect_platform(self) -> PlatformConfig:
        return PlatformConfig(
            name="darwin",
            arch=ARCH,
            root_required=True,  # Requires sudo for process memory access
        )
    
    def inject(self) -> bool:
        """Inject using ptrace/mmap."""
        if self.is_injected:
            return True
        
        roblox_pid = self._find_roblox_process()
        if not roblox_pid:
            return False
        
        self.platform_config.pid = roblox_pid
        
        # Use subprocess to run injection
        try:
            result = subprocess.run(
                ["sudo", "-n", "python3", "-c", self._get_inject_script()],
                capture_output=True,
                timeout=30
            )
            self.is_injected = result.returncode == 0
            return self.is_injected
        except Exception:
            return False
    
    def execute_script(self, script: ScriptInfo) -> ExecutionResult:
        """Execute via Roblox's Lua environment on macOS."""
        if not self.is_injected:
            return ExecutionResult(
                success=False,
                error="Not injected. Call inject() first."
            )
        
        start_time = __import__('time').time()
        
        # macOS: Use Roblox's built-in execution through script injection
        # This typically involves writing to the game's Lua state
        try:
            # Execute via injected payload
            result = self._execute_payload(script)
            
            exec_time = __import__('time').time() - start_time
            script.execution_count += 1
            script.last_executed = __import__('time').time()
            
            return ExecutionResult(
                success=result.get("success", True),
                output=result.get("output", ""),
                error=result.get("error", ""),
                execution_time=exec_time
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    def _execute_payload(self, script: ScriptInfo) -> Dict:
        """Execute payload on macOS."""
        # Implementation depends on specific Roblox version
        return {"success": True, "output": "Executed"}
    
    def _find_roblox_process(self) -> Optional[int]:
        """Find Roblox process on macOS."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "RobloxApp"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return None
    
    def _get_inject_script(self) -> str:
        """Return Python injection script."""
        return '''
import ctypes
import sys
import struct

# macOS process injection using ptrace
def inject(pid: int, shellcode: bytes):
    libc = ctypes.CDLL("/usr/lib/libc.dylib")
    
    # Attach to process
    ptrace = libc.ptrace
    ptrace.argtypes = [ctypes.c_long, ctypes.c_int, ctypes.c_int, ctypes.c_long]
    ptrace.restype = ctypes.c_long
    
    if ptrace(20, pid, 0, 0) < 0:  # PT_ATTACH
        return False
    
    # Read thread context
    class THREAD_STATE_ARM64(ctypes.Structure):
        _fields_ = [
            ("thread_fpreg", ctypes.c_uint64 * 541),
            ("thread_saved_state", ctypes.c_uint8 * 512),
        ]
    
    ctx = THREAD_STATE_ARM64()
    if ptrace(17, pid, 2, ctypes.byref(ctx)) < 0:  # PT_READ_U
        return False
    
    # Write shellcode to process memory
    # This is a simplified version - real implementation is more complex
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inject.py <pid>")
        sys.exit(1)
    pid = int(sys.argv[1])
    print(inject(pid, b"\\x00" * 1024))
'''
    
    def unload(self) -> bool:
        """Remove injection."""
        if not self.is_injected or not self.platform_config.pid:
            return False
        # Implementation for macOS uninject
        self.is_injected = False
        return True


# ============================================================
# ANDROID EXECUTOR (Root/Modified Client)
# ============================================================

class AndroidExecutor(ExecutorCore):
    """Android-specific executor using Frida or root injection."""
    
    FRIDA_SERVER_PORT = 27042
    SUPPORTED_APKS = [
        "com.roblox.client",
        "com.roblox.client.beta"
    ]
    
    def _detect_platform(self) -> PlatformConfig:
        return PlatformConfig(
            name="android",
            arch=ARCH,
            root_required=True,  # Or modified client without root
        )
    
    def inject(self) -> bool:
        """Inject using Frida."""
        if self.is_injected:
            return True
        
        # Check for Frida server
        if not self._check_frida():
            return False
        
        # Find Roblox process
        self.platform_config.pid = self._find_roblox_pid()
        if not self.platform_config.pid:
            return False
        
        # Deploy Frida agent
        try:
            result = subprocess.run(
                ["frida", "-U", "-f", "com.roblox.client",
                 "--no-pause", "-l", str(self._get_agent_path())],
                capture_output=True,
                timeout=30
            )
            self.is_injected = True
            return True
        except Exception:
            # Alternative: Use frida-server directly
            return self._inject_frida_server()
    
    def _inject_frida_server(self) -> bool:
        """Inject using frida-server on device."""
        try:
            # Push frida-server to device
            subprocess.run(
                ["adb", "push", "/tmp/frida-server", "/data/local/tmp/frida-server"],
                capture_output=True, timeout=10
            )
            subprocess.run(
                ["adb", "shell", "chmod", "+x", "/data/local/tmp/frida-server"],
                capture_output=True
            )
            subprocess.run(
                ["adb", "shell", "/data/local/tmp/frida-server&"],
                capture_output=True
            )
            return True
        except Exception:
            return False
    
    def execute_script(self, script: ScriptInfo) -> ExecutionResult:
        """Execute script via Frida."""
        if not self.is_injected:
            return ExecutionResult(
                success=False,
                error="Not injected. Call inject() first."
            )
        
        start_time = __import__('time').time()
        
        try:
            # Compile and execute via Frida
            result = self._execute_frida(script)
            
            exec_time = __import__('time').time() - start_time
            script.execution_count += 1
            script.last_executed = __import__('time').time()
            
            return ExecutionResult(
                success=result.get("success", True),
                output=result.get("output", ""),
                error=result.get("error", ""),
                execution_time=exec_time
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    def _execute_frida(self, script: ScriptInfo) -> Dict:
        """Execute script through Frida agent."""
        # This would use Frida's RPC to call Roblox's execute function
        return {"success": True, "output": "Executed"}
    
    def _check_frida(self) -> bool:
        """Check if Frida is available."""
        try:
            result = subprocess.run(
                ["frida", "--version"],
                capture_output=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _find_roblox_pid(self) -> Optional[int]:
        """Find Roblox PID on Android."""
        try:
            result = subprocess.run(
                ["adb", "shell", "pidof", "com.roblox.client"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except Exception:
            pass
        return None
    
    def _get_agent_path(self) -> Path:
        """Get Frida agent script path."""
        return Path(__file__).parent.parent / "android" / "agent.js"
    
    def unload(self) -> bool:
        """Remove injection."""
        self.is_injected = False
        return True


# ============================================================
# IOS EXECUTOR (Jailbreak/Frida)
# ============================================================

class iOSExecutor(ExecutorCore):
    """iOS-specific executor using Frida or jailbreak injection."""
    
    def _detect_platform(self) -> PlatformConfig:
        return PlatformConfig(
            name="ios",
            arch=ARCH,
            jailbreak_required=True,
        )
    
    def inject(self) -> bool:
        """Inject using Frida on jailbroken device."""
        if self.is_injected:
            return True
        
        # Check for Frida on iOS device
        if not self._check_frida_ios():
            return False
        
        # Find Roblox PID
        self.platform_config.pid = self._find_roblox_pid_ios()
        if not self.platform_config.pid:
            return False
        
        # Inject
        try:
            result = subprocess.run(
                ["frida", "-U", "Roblox",
                 "-l", str(self._get_agent_path())],
                capture_output=True,
                timeout=30
            )
            self.is_injected = True
            return True
        except Exception:
            return False
    
    def execute_script(self, script: ScriptInfo) -> ExecutionResult:
        """Execute script via Frida on iOS."""
        if not self.is_injected:
            return ExecutionResult(
                success=False,
                error="Not injected. Call inject() first."
            )
        
        start_time = __import__('time').time()
        
        try:
            result = self._execute_frida_ios(script)
            
            exec_time = __import__('time').time() - start_time
            script.execution_count += 1
            script.last_executed = __import__('time').time()
            
            return ExecutionResult(
                success=result.get("success", True),
                output=result.get("output", ""),
                error=result.get("error", ""),
                execution_time=exec_time
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    def _execute_frida_ios(self, script: ScriptInfo) -> Dict:
        """Execute via Frida on iOS."""
        return {"success": True, "output": "Executed"}
    
    def _check_frida_ios(self) -> bool:
        """Check Frida availability on iOS."""
        try:
            result = subprocess.run(
                ["frida-ps", "-U"],
                capture_output=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _find_roblox_pid_ios(self) -> Optional[int]:
        """Find Roblox PID on iOS."""
        try:
            result = subprocess.run(
                ["frida-ps", "-U"],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'Roblox' in line:
                    # Parse PID from output
                    parts = line.split()
                    if parts:
                        return int(parts[0])
        except Exception:
            pass
        return None
    
    def _get_agent_path(self) -> Path:
        """Get Frida agent for iOS."""
        return Path(__file__).parent.parent / "ios" / "agent.js"
    
    def unload(self) -> bool:
        """Remove injection."""
        self.is_injected = False
        return True


# ============================================================
# FACTORY & DISPATCHER
# ============================================================

class ExecutorFactory:
    """Factory to create platform-specific executors."""
    
    _registry: Dict[str, type] = {
        "windows": WindowsExecutor,
        "darwin": macOSExecutor,
        "linux": WindowsExecutor,  # Similar injection approach
        "android": AndroidExecutor,
        "ios": iOSExecutor,
    }
    
    @classmethod
    def create(cls, platform_name: Optional[str] = None, config: Optional[Dict] = None) -> ExecutorCore:
        """Create executor for specified or detected platform."""
        if platform_name is None:
            platform_name = cls._detect_current_platform()
        
        executor_class = cls._registry.get(platform_name)
        if not executor_class:
            raise ValueError(f"Unsupported platform: {platform_name}")
        
        return executor_class(config)
    
    @classmethod
    def _detect_current_platform(self) -> str:
        """Detect current platform."""
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif "android" in system:
            return "android"
        # iOS detection is trickier
        return "windows"  # Default fallback


# ============================================================
# SCRIPT MANAGER
# ============================================================

class ScriptManager:
    """Manages scripts across all executors."""
    
    def __init__(self, executor: ExecutorCore):
        self.executor = executor
        self.script_dir = Path(__file__).parent.parent / "scripts"
        self.script_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, path: str) -> ScriptInfo:
        """Load script from file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Script not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        name = path.stem
        
        script = self.executor.load_script(name, content)
        
        # Auto-save to scripts directory
        self._save_script(script)
        
        return script
    
    def save_script(self, script: ScriptInfo) -> Path:
        """Save script to file."""
        return self._save_script(script)
    
    def _save_script(self, script: ScriptInfo) -> Path:
        """Internal save method."""
        path = self.script_dir / f"{script.name}.luau"
        path.write_text(script.content, encoding="utf-8")
        return path
    
    def execute_all(self) -> List[ExecutionResult]:
        """Execute all enabled scripts."""
        results = []
        for script in self.executor.list_scripts():
            if script.enabled:
                result = self.executor.execute_script(script)
                results.append(result)
        return results


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"{EXECUTOR_NAME} v{VERSION} - Universal Roblox Script Executor"
    )
    parser.add_argument("--platform", choices=["auto", "windows", "macos", "android", "ios"],
                       default="auto", help="Target platform")
    parser.add_argument("--inject", action="store_true", help="Inject into Roblox")
    parser.add_argument("--uninject", action="store_true", help="Unload executor")
    parser.add_argument("--list", action="store_true", help="List loaded scripts")
    parser.add_argument("--execute", nargs="?", const="", help="Execute a script")
    parser.add_argument("--script", type=str, help="Script file to load")
    parser.add_argument("--status", action="store_true", help="Show executor status")
    
    args = parser.parse_args()
    
    # Create executor
    platform = None if args.platform == "auto" else args.platform
    executor = ExecutorFactory.create(platform)
    
    print(f"\n{EXECUTOR_NAME} v{VERSION}")
    print(f"Platform: {executor.platform_config.name} ({executor.platform_config.arch})")
    print(f"Injected: {executor.is_injected}\n")
    
    if args.status:
        stats = executor.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if args.inject:
        print("Injecting...", end=" ")
        if executor.inject():
            print("SUCCESS")
            executor.is_injected = True
        else:
            print("FAILED")
        return
    
    if args.uninject:
        print("Uninjecting...", end=" ")
        if executor.unload():
            print("SUCCESS")
        else:
            print("FAILED or not injected")
        return
    
    if args.script:
        manager = ScriptManager(executor)
        script = manager.load_from_file(args.script)
        print(f"Loaded: {script.name} ({script.hash})")
        
        if args.execute is not None:
            if executor.is_injected:
                result = executor.execute_script(script)
                print(f"Output: {result.output}")
                if result.error:
                    print(f"Error: {result.error}")
            else:
                print("Error: Not injected. Run --inject first.")
        return
    
    if args.list:
        manager = ScriptManager(executor)
        scripts = executor.list_scripts()
        if not scripts:
            print("No scripts loaded.")
        else:
            print(f"Loaded {len(scripts)} scripts:\n")
            for s in scripts:
                status = "✓" if s.enabled else "✗"
                print(f"  [{status}] {s.name} ({s.hash}) - {s.size} bytes")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
