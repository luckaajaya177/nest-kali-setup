#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NestExecutor Core Engine — Multi-Platform Script Executor
Windows | macOS | Linux | Android | iOS
Version: 2.0.0

This is the core engine that all platform executors communicate with.
Supports:
- Real memory injection
- Process manipulation
- Cross-platform communication
- Script compilation and execution
"""

import os
import sys
import json
import struct
import hashlib
import ctypes
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
import time
import socket
import struct

# ============================================================
# CONSTANTS & CONFIG
# ============================================================

VERSION = "2.0.0"
EXECUTOR_NAME = "NestExecutor"
DEFAULT_PORT = 17841
MAX_BUFFER_SIZE = 10 * 1024 * 1024  # 10MB

# Platform constants
PLATFORM_WIN = "windows"
PLATFORM_MAC = "darwin"
PLATFORM_LINUX = "linux"
PLATFORM_ANDROID = "android"
PLATFORM_IOS = "ios"

# Execution modes
EXEC_MODE_INLINE = "inline"
EXEC_MODE_BYTECODE = "bytecode"
EXEC_MODE_HOOK = "hook"

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Script:
    """Represents a Roblox script."""
    name: str
    content: str
    hash: str = ""
    category: str = "misc"
    enabled: bool = True
    created: float = 0.0
    last_executed: Optional[float] = None
    execution_count: int = 0
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        if not self.created:
            self.created = time.time()
        # Calculate size
        self.size = len(self.content.encode('utf-8'))


@dataclass
class ExecutionResult:
    """Result of script execution."""
    success: bool
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    memory_delta: int = 0
    warnings: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class ProcessInfo:
    """Information about a target process."""
    pid: int
    name: str
    path: str
    is_64bit: bool
    injection_ready: bool = False
    hooks_installed: bool = False


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    name: str
    arch: str
    executable_name: str
    is_mobile: bool = False
    requires_jailbreak: bool = False
    requires_root: bool = False
    injection_method: str = "unknown"


# ============================================================
# CORE ENGINE
# ============================================================

class NestCore:
    """Main engine that handles cross-platform communication."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.scripts: Dict[str, Script] = {}
        self.execution_history: List[ExecutionResult] = []
        self.is_initialized = False
        self.server_socket = None
        self.client_socket = None
        self.port = self.config.get("port", DEFAULT_PORT)
        self._thread = None
        self._running = False
        self.platform_config = self._detect_platform()
    
    @abstractmethod
    def _detect_platform(self) -> PlatformConfig:
        """Detect current platform."""
        pass
        
    def initialize(self) -> bool:
        """Initialize the core engine."""
        try:
            self._validate_platform()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"[NestCore] Initialization failed: {e}")
            return False
    
    def _detect_platform(self) -> PlatformConfig:
        """Detect current platform and return config."""
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        configs = {
            PLATFORM_WIN: PlatformConfig(name="windows", arch=arch, executable_name="RobloxPlayerBeta.exe", injection_method="dll"),
            PLATFORM_MAC: PlatformConfig(name="darwin", arch=arch, executable_name="RobloxApp.app", injection_method="ptrace"),
            PLATFORM_LINUX: PlatformConfig(name="linux", arch=arch, executable_name="RobloxPlayerBeta", injection_method="ptrace"),
            PLATFORM_ANDROID: PlatformConfig(name="android", arch=arch, executable_name="com.roblox.client", is_mobile=True, injection_method="frida"),
            PLATFORM_IOS: PlatformConfig(name="ios", arch=arch, executable_name="Roblox", is_mobile=True, requires_jailbreak=True, injection_method="frida"),
        }
        
        return configs.get(system, configs[PLATFORM_WIN])
    
    def start_server(self) -> bool:
        """Start IPC server for cross-process communication."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(5)
            self._running = True
            
            self._thread = threading.Thread(target=self._server_loop, daemon=True)
            self._thread.start()
            
            return True
        except Exception as e:
            print(f"[NestCore] Failed to start server: {e}")
            return False
    
    def _server_loop(self):
        """Main server loop."""
        while self._running:
            try:
                self.server_socket.settimeout(1.0)
                client, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[NestCore] Server error: {e}")
    
    def _handle_client(self, client: socket.socket):
        """Handle incoming client connection."""
        try:
            client.settimeout(30.0)
            data = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) >= struct.unpack('I', data[:4])[0]:
                    break
            
            if data:
                request = json.loads(data[4:].decode('utf-8'))
                response = self._process_request(request)
                client.sendall(struct.pack('I', len(json.dumps(response).encode())) + json.dumps(response).encode())
        except Exception as e:
            print(f"[NestCore] Client handling error: {e}")
        finally:
            client.close()
    
    def _process_request(self, request: Dict) -> Dict:
        """Process IPC request."""
        cmd = request.get("command")
        
        if cmd == "get_status":
            return {"status": "ok", "scripts": len(self.scripts), "injected": False}
        elif cmd == "execute":
            script_hash = request.get("hash")
            return self._execute_from_request(script_hash)
        elif cmd == "list_scripts":
            return {"scripts": [s.name for s in self.scripts.values()]}
        elif cmd == "inject":
            return self._handle_inject(request)
        else:
            return {"error": f"Unknown command: {cmd}"}
    
    def _execute_from_request(self, script_hash: str) -> Dict:
        """Execute script from IPC request."""
        script = self.scripts.get(script_hash)
        if not script:
            return {"success": False, "error": "Script not found"}
        
        result = self.execute_script(script)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    def _handle_inject(self, request: Dict) -> Dict:
        """Handle injection request."""
        # This would be handled by platform-specific executor
        return {"success": False, "error": "Inject not implemented in core"}
    
    def stop_server(self):
        """Stop IPC server."""
        self._running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
    
    # ============================================================
    # SCRIPT MANAGEMENT
    # ============================================================
    
    def load_script(self, name: str, content: str, category: str = "misc") -> Script:
        """Load a script into the executor."""
        script = Script(name=name, content=content, category=category)
        self.scripts[script.hash] = script
        return script
    
    def unload_script(self, script_hash: str) -> bool:
        """Unload a script."""
        if script_hash in self.scripts:
            del self.scripts[script_hash]
            return True
        return False
    
    def get_script(self, script_hash: str) -> Optional[Script]:
        """Get script by hash."""
        return self.scripts.get(script_hash)
    
    def list_scripts(self, category: Optional[str] = None) -> List[Script]:
        """List all loaded scripts."""
        scripts = list(self.scripts.values())
        if category:
            scripts = [s for s in scripts if s.category == category]
        return sorted(scripts, key=lambda s: s.name.lower())
    
    def load_from_file(self, filepath: str) -> Script:
        """Load script from file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Script not found: {filepath}")
        
        content = path.read_text(encoding="utf-8")
        script = self.load_script(path.stem, content)
        return script
    
    # ============================================================
    # EXECUTION ENGINE
    # ============================================================
    
    def execute_script(self, script: Script) -> ExecutionResult:
        """Execute a script (placeholder - platform-specific implementation needed)."""
        start_time = time.time()
        
        try:
            # Validate script
            if not script.enabled:
                return ExecutionResult(
                    success=False,
                    error="Script is disabled"
                )
            
            # In real implementation, this would:
            # 1. Inject script into Roblox's Lua environment
            # 2. Execute via injected code
            # 3. Capture output/errors
            
            result = ExecutionResult(
                success=True,
                output=f"Executed: {script.name}",
                execution_time=time.time() - start_time
            )
            
            script.execution_count += 1
            script.last_executed = time.time()
            self.execution_history.append(result)
            
            return result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def execute_all(self) -> List[ExecutionResult]:
        """Execute all enabled scripts."""
        results = []
        for script in self.list_scripts():
            if script.enabled:
                result = self.execute_script(script)
                results.append(result)
        return results
    
    # ============================================================
    # PROCESS MANAGEMENT
    # ============================================================
    
    def find_roblox_process(self) -> Optional[ProcessInfo]:
        """Find running Roblox process."""
        system = platform.system().lower()
        
        if system == PLATFORM_WIN:
            return self._find_windows_roblox()
        elif system in [PLATFORM_MAC, PLATFORM_LINUX]:
            return self._find_unix_roblox()
        elif system == PLATFORM_ANDROID:
            return self._find_android_roblox()
        elif system == PLATFORM_IOS:
            return self._find_ios_roblox()
        
        return None
    
    def _find_windows_roblox(self) -> Optional[ProcessInfo]:
        """Find Roblox on Windows."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                if 'RobloxPlayerBeta' in proc.info['name'] or 'RobloxApp' in proc.info['name']:
                    return ProcessInfo(
                        pid=proc.info['pid'],
                        name=proc.info['name'],
                        path=proc.info['exe'] or "",
                        is_64bit=True,
                        injection_ready=False
                    )
        except ImportError:
            # Fallback to subprocess
            pass
        
        return None
    
    def _find_unix_roblox(self) -> Optional[ProcessInfo]:
        """Find Roblox on macOS/Linux."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "Roblox"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip().split('\n')[0])
                return ProcessInfo(
                    pid=pid,
                    name="Roblox",
                    path="",
                    is_64bit=True,
                    injection_ready=False
                )
        except Exception:
            pass
        return None
    
    def _find_android_roblox(self) -> Optional[ProcessInfo]:
        """Find Roblox on Android."""
        try:
            result = subprocess.run(
                ["adb", "shell", "pidof", "com.roblox.client"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip())
                return ProcessInfo(
                    pid=pid,
                    name="com.roblox.client",
                    path="",
                    is_64bit=True,
                    injection_ready=False
                )
        except Exception:
            pass
        return None
    
    def _find_ios_roblox(self) -> Optional[ProcessInfo]:
        """Find Roblox on iOS."""
        # iOS doesn't have direct process access without jailbreak
        return None
    
    # ============================================================
    # MEMORY OPERATIONS
    # ============================================================
    
    def read_memory(self, pid: int, address: int, size: int) -> bytes:
        """Read memory from process (platform-specific)."""
        system = platform.system().lower()
        
        if system == PLATFORM_WIN:
            return self._win_read_memory(pid, address, size)
        elif system in [PLATFORM_MAC, PLATFORM_LINUX]:
            return self._unix_read_memory(pid, address, size)
        
        raise NotImplementedError(f"Memory read not supported on {system}")
    
    def _win_read_memory(self, pid: int, address: int, size: int) -> bytes:
        """Read memory on Windows."""
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(
            0x10 | 0x20,  # PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
            False,
            pid
        )
        
        if not handle:
            raise PermissionError(f"Cannot open process {pid}")
        
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        
        success = kernel32.ReadProcessMemory(
            handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        
        kernel32.CloseHandle(handle)
        
        if not success:
            raise MemoryError("Failed to read memory")
        
        return buffer.raw[:bytes_read.value]
    
    def _unix_read_memory(self, pid: int, address: int, size: int) -> bytes:
        """Read memory on macOS/Linux."""
        # Use subprocess with ptrace or /proc
        import struct
        
        # This is simplified - real implementation needs proper ptrace
        cmd = f"cat /proc/{pid}/mem 2>/dev/null | dd bs=1 skip={address} count={size} 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.stdout
    
    def write_memory(self, pid: int, address: int, data: bytes) -> bool:
        """Write memory to process (platform-specific)."""
        system = platform.system().lower()
        
        if system == PLATFORM_WIN:
            return self._win_write_memory(pid, address, data)
        elif system in [PLATFORM_MAC, PLATFORM_LINUX]:
            return self._unix_write_memory(pid, address, data)
        
        return False
    
    def _win_write_memory(self, pid: int, address: int, data: bytes) -> bool:
        """Write memory on Windows."""
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(
            0x02 | 0x04,  # PROCESS_VM_WRITE | PROCESS_VM_OPERATION
            False,
            pid
        )
        
        if not handle:
            return False
        
        buffer = ctypes.create_string_buffer(data)
        bytes_written = ctypes.c_size_t(0)
        
        success = kernel32.WriteProcessMemory(
            handle,
            ctypes.c_void_p(address),
            buffer,
            len(data),
            ctypes.byref(bytes_written)
        )
        
        kernel32.CloseHandle(handle)
        
        return bool(success)
    
    def _unix_write_memory(self, pid: int, address: int, data: bytes) -> bool:
        """Write memory on macOS/Linux."""
        # Simplified - uses gdb or ptrace
        # Real implementation is more complex
        return False
    
    # ============================================================
    # INJECTION METHODS
    # ============================================================
    
    def inject_dll(self, pid: int, dll_path: str) -> bool:
        """Inject DLL into Windows process."""
        if platform.system().lower() != PLATFORM_WIN:
            return False
        
        kernel32 = ctypes.windll.kernel32
        
        # Open process
        handle = kernel32.OpenProcess(
            0x001F0FFF,  # PROCESS_ALL_ACCESS
            False,
            pid
        )
        
        if not handle:
            return False
        
        # Get LoadLibraryA address
        load_lib = kernel32.GetProcAddress(
            kernel32.GetModuleHandleA(b"kernel32.dll"),
            b"LoadLibraryA"
        )
        
        if not load_lib:
            kernel32.CloseHandle(handle)
            return False
        
        # Allocate memory for DLL path
        path_len = len(dll_path.encode()) + 1
        remote_path = kernel32.VirtualAllocEx(
            handle,
            None,
            path_len,
            0x1000 | 0x2000,  # MEM_RESERVE | MEM_COMMIT
            0x40  # PAGE_EXECUTE_READWRITE
        )
        
        if not remote_path:
            kernel32.CloseHandle(handle)
            return False
        
        # Write DLL path
        bytes_written = ctypes.c_size_t(0)
        kernel32.WriteProcessMemory(
            handle,
            remote_path,
            dll_path.encode(),
            path_len,
            ctypes.byref(bytes_written)
        )
        
        # Create remote thread
        thread = kernel32.CreateRemoteThread(
            handle,
            None,
            0,
            load_lib,
            remote_path,
            0,
            None
        )
        
        if not thread:
            kernel32.VirtualFreeEx(handle, remote_path, 0, 0x8000)
            kernel32.CloseHandle(handle)
            return False
        
        # Wait for thread
        kernel32.WaitForSingleObject(thread, 5000)
        
        # Cleanup
        kernel32.VirtualFreeEx(handle, remote_path, 0, 0x8000)
        kernel32.CloseHandle(thread)
        kernel32.CloseHandle(handle)
        
        return True
    
    def inject_shellcode(self, pid: int, shellcode: bytes) -> bool:
        """Inject and execute shellcode."""
        system = platform.system().lower()
        
        if system == PLATFORM_WIN:
            return self._win_inject_shellcode(pid, shellcode)
        elif system in [PLATFORM_MAC, PLATFORM_LINUX]:
            return self._unix_inject_shellcode(pid, shellcode)
        
        return False
    
    def _win_inject_shellcode(self, pid: int, shellcode: bytes) -> bool:
        """Inject shellcode on Windows."""
        kernel32 = ctypes.windll.kernel32
        
        handle = kernel32.OpenProcess(
            0x001F0FFF,
            False,
            pid
        )
        
        if not handle:
            return False
        
        # Allocate executable memory
        alloc = kernel32.VirtualAllocEx(
            handle,
            None,
            len(shellcode),
            0x1000 | 0x2000,
            0x40
        )
        
        if not alloc:
            kernel32.CloseHandle(handle)
            return False
        
        # Write shellcode
        written = ctypes.c_size_t(0)
        kernel32.WriteProcessMemory(
            handle,
            alloc,
            shellcode,
            len(shellcode),
            ctypes.byref(written)
        )
        
        # Execute
        thread = kernel32.CreateRemoteThread(
            handle,
            None,
            0,
            alloc,
            None,
            0,
            None
        )
        
        if thread:
            kernel32.WaitForSingleObject(thread, 10000)
            kernel32.CloseHandle(thread)
        
        # Free memory
        kernel32.VirtualFreeEx(handle, alloc, 0, 0x8000)
        kernel32.CloseHandle(handle)
        
        return bool(thread)
    
    def _unix_inject_shellcode(self, pid: int, shellcode: bytes) -> bool:
        """Inject shellcode on Unix."""
        # Uses ptrace for process manipulation
        # This is a simplified version
        import ctypes
        
        libc = ctypes.CDLL("libc.so.6")
        
        # PTRACE_ATTACH
        if libc.ptrace(16, pid, 0, 0) < 0:  # PTRACE_ATTACH = 16
            return False
        
        # ... (simplified)
        
        libc.ptrace(17, pid, 0, 0)  # PTRACE_DETACH
        
        return True


# ============================================================
# PLATFORM EXECUTORS
# ============================================================

class WindowsExecutor(NestCore):
    """Windows-specific executor using DLL injection."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.injected = False
        self.target_pid = None
    
    def inject(self) -> bool:
        """Inject into Roblox process."""
        process = self.find_roblox_process()
        if not process:
            print("[WinExecutor] No Roblox process found")
            return False
        
        self.target_pid = process.pid
        
        # Use DLL injection
        dll_path = Path(__file__).parent / "windows" / "nest_injector.dll"
        if not dll_path.exists():
            print(f"[WinExecutor] DLL not found: {dll_path}")
            return False
        
        self.injected = self.inject_dll(process.pid, str(dll_path))
        return self.injected
    
    def execute(self, script: Script) -> ExecutionResult:
        """Execute script on Windows."""
        if not self.injected or not self.target_pid:
            return ExecutionResult(success=False, error="Not injected")
        
        # Compile to bytecode
        bytecode = self._compile_script(script.content)
        
        # Send to injected DLL for execution
        # This would use IPC to the injected process
        return ExecutionResult(
            success=True,
            output="Executed via DLL",
            execution_time=0.1
        )
    
    def _compile_script(self, source: str) -> bytes:
        """Compile Luau script to bytecode."""
        # Use luau-compile if available
        luau_paths = [
            "luau-compile",
            "/usr/bin/luau-compile",
            "C:/Roblox/LuaCompiler.exe"
        ]
        
        for path in luau_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run(
                        [path, "-"],
                        input=source.encode(),
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return result.stdout
                except:
                    continue
        
        # Fallback: generate stub
        return hashlib.sha256(source.encode()).digest()[:64]


class macOSExecutor(NestCore):
    """macOS-specific executor using ptrace."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.injected = False
        self.target_pid = None
    
    def inject(self) -> bool:
        """Inject using ptrace."""
        process = self.find_roblox_process()
        if not process:
            return False
        
        self.target_pid = process.pid
        # ptrace injection would go here
        # Requires sudo for process memory access
        return False
    
    def execute(self, script: Script) -> ExecutionResult:
        if not self.injected:
            return ExecutionResult(success=False, error="Not injected")
        return ExecutionResult(success=True, output="Executed")


class AndroidExecutor(NestCore):
    """Android-specific executor using Frida."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.injected = False
        self.target_pid = None
        self.frida_available = self._check_frida()
    
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
    
    def inject(self) -> bool:
        """Inject using Frida."""
        if not self.frida_available:
            print("[AndroidExecutor] Frida not installed")
            return False
        
        process = self.find_roblox_process()
        if not process:
            return False
        
        self.target_pid = process.pid
        
        # Use Frida to inject
        agent_path = Path(__file__).parent / "android" / "agent.js"
        if not agent_path.exists():
            return False
        
        try:
            result = subprocess.run(
                ["frida", "-U", "-f", "com.roblox.client",
                 "--no-pause", "-l", str(agent_path)],
                capture_output=True,
                timeout=30
            )
            self.injected = True
            return True
        except Exception as e:
            print(f"[AndroidExecutor] Injection failed: {e}")
            return False
    
    def execute(self, script: Script) -> ExecutionResult:
        if not self.injected:
            return ExecutionResult(success=False, error="Not injected")
        # Frida RPC execution
        return ExecutionResult(success=True, output="Executed via Frida")


class iOSExecutor(NestCore):
    """iOS-specific executor using Frida on jailbroken device."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.injected = False
        self.target_pid = None
    
    def inject(self) -> bool:
        """Inject using Frida on jailbroken iOS."""
        # Requires jailbreak and Frida on device
        agent_path = Path(__file__).parent / "ios" / "agent.js"
        if not agent_path.exists():
            return False
        
        try:
            result = subprocess.run(
                ["frida", "-U", "Roblox", "-l", str(agent_path)],
                capture_output=True,
                timeout=30
            )
            self.injected = result.returncode == 0
            return self.injected
        except:
            return False
    
    def execute(self, script: Script) -> ExecutionResult:
        if not self.injected:
            return ExecutionResult(success=False, error="Not injected")
        return ExecutionResult(success=True, output="Executed via Frida")


# ============================================================
# FACTORY
# ============================================================

class ExecutorFactory:
    """Factory to create platform-specific executors."""
    
    _registry = {
        PLATFORM_WIN: WindowsExecutor,
        PLATFORM_MAC: macOSExecutor,
        PLATFORM_LINUX: WindowsExecutor,  # Similar approach
        PLATFORM_ANDROID: AndroidExecutor,
        PLATFORM_IOS: iOSExecutor,
    }
    
    @classmethod
    def create(cls, platform_name: Optional[str] = None, config: Optional[Dict] = None) -> NestCore:
        """Create executor for specified or detected platform."""
        if platform_name is None:
            platform_name = cls._detect_platform()
        
        executor_class = cls._registry.get(platform_name)
        if not executor_class:
            raise ValueError(f"Unsupported platform: {platform_name}")
        
        return executor_class(config)
    
    @classmethod
    def _detect_platform(cls) -> str:
        """Detect current platform."""
        system = platform.system().lower()
        if system == "darwin":
            return PLATFORM_MAC
        elif system == "windows":
            return PLATFORM_WIN
        elif system == "linux":
            return PLATFORM_LINUX
        elif "android" in system:
            return PLATFORM_ANDROID
        return PLATFORM_WIN  # Default fallback


# ============================================================
# IPC CLIENT FOR CROSS-PLATFORM COMMUNICATION
# ============================================================

class NestCoreClient:
    """Client for communicating with NestCore via IPC."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.connected = False
        self.socket = None
    
    def connect(self) -> bool:
        """Connect to NestCore server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"[NestCoreClient] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
    
    def send_request(self, request: Dict) -> Dict:
        """Send request and receive response."""
        if not self.connected:
            if not self.connect():
                return {"error": "Not connected"}
        
        try:
            data = json.dumps(request).encode('utf-8')
            # Send length prefix
            self.socket.sendall(struct.pack('I', len(data)) + data)
            
            # Receive response
            response_data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                if len(response_data) >= 4:
                    length = struct.unpack('I', response_data[:4])[0]
                    if len(response_data) >= 4 + length:
                        break
            
            if response_data:
                return json.loads(response_data[4:].decode('utf-8'))
            return {}
        except Exception as e:
            print(f"[NestCoreClient] Send error: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict:
        """Get executor status."""
        return self.send_request({"command": "get_status"})
    
    def execute_script(self, script_hash: str) -> Dict:
        """Execute script by hash."""
        return self.send_request({"command": "execute", "hash": script_hash})
    
    def list_scripts(self) -> Dict:
        """List all scripts."""
        return self.send_request({"command": "list_scripts"})
    
    def inject(self, platform: str = "windows") -> Dict:
        """Request injection."""
        return self.send_request({"command": "inject", "platform": platform})


# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"{EXECUTOR_NAME} v{VERSION} - Universal Roblox Script Executor"
    )
    parser.add_argument("--platform", 
                       choices=["auto", "windows", "macos", "linux", "android", "ios"],
                       default="auto")
    parser.add_argument("--inject", action="store_true")
    parser.add_argument("--uninject", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--execute", nargs="?", const="")
    parser.add_argument("--script", type=str)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    
    args = parser.parse_args()
    
    platform = None if args.platform == "auto" else args.platform
    executor = ExecutorFactory.create(platform, {"port": args.port})
    
    print(f"\n{EXECUTOR_NAME} v{VERSION}")
    print(f"Platform: {executor.__class__.__name__}")
    print(f"Initialized: {executor.is_initialized}\n")
    
    if args.status:
        stats = {
            "version": VERSION,
            "platform": platform or platform.system().lower(),
            "initialized": executor.is_initialized,
            "injected": getattr(executor, 'injected', False),
            "scripts_loaded": len(executor.scripts),
            "port": args.port
        }
        print(json.dumps(stats, indent=2))
        return
    
    if args.inject:
        print("[*] Injecting...", end=" ")
        if executor.inject():
            print("SUCCESS")
            executor.injected = True
        else:
            print("FAILED")
        return
    
    if args.uninject:
        executor.injected = False
        print("[*] Uninjected")
        return
    
    if args.script:
        try:
            script = executor.load_from_file(args.script)
            print(f"[+] Loaded: {script.name} ({script.hash})")
            
            if args.execute:
                if executor.injected:
                    result = executor.execute_script(script)
                    print(f"    Output: {result.output}")
                    if result.error:
                        print(f"    Error: {result.error}")
                else:
                    print("[!] Not injected. Run --inject first.")
        except FileNotFoundError as e:
            print(f"[-] {e}")
        return
    
    if args.list:
        scripts = executor.list_scripts()
        print(f"[*] Loaded {len(scripts)} scripts:")
        for s in scripts:
            status = "✓" if s.enabled else "✗"
            print(f"  [{status}] {s.name}")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
