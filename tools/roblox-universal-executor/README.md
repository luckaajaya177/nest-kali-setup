# NestExecutor - Universal Roblox Script Executor

**Version:** 1.0.0  
**Author:** nest-kali-setup  
**License:** Educational/Research  

## Overview

Universal Roblox script executor supporting Windows, macOS, Linux, Android, and iOS.

## Architecture

```
nest_executor.py          # Main entry point
├── core/
│   └── executor.py       # Core engine with platform implementations
├── windows/              # Windows-specific (DLL injection)
│   ├── nest_injector.dll
│   └── injector.exe
├── android/              # Android-specific (Frida)
│   └── agent.js
├── ios/                  # iOS-specific (Frida)
│   └── agent.js
├── scripts/              # Pre-loaded scripts
│   └── default_scripts.py
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- Frida (for Android/iOS)
- ADB (for Android)
- iTunes/Finder (for iOS)

### Install Dependencies

```bash
# Python dependencies
pip install psutil frida frida-tools

# Android (optional)
brew install android-platform-tools  # or download SDK

# iOS (optional, jailbroken device required)
brew install frida-tools
```

## Usage

### Basic Commands

```bash
# Status check
python nest_executor.py --status

# Inject into Roblox
python nest_executor.py --inject

# List scripts
python nest_executor.py --list

# Load and execute script
python nest_executor.py --script scripts/example.luau --execute

# Specify platform
python nest_executor.py --platform android --inject
python nest_executor.py --platform ios --inject
```

### Platform-Specific

#### Windows/macOS/Linux
- Requires Roblox Studio or Player to be running
- DLL injection method
- May require admin/root privileges

#### Android
- Requires Frida server on device
- Root access OR modified Roblox APK
- ADB connection required

```bash
# Start frida-server on device
adb push frida-server /data/local/tmp/
adb shell "chmod +x /data/local/tmp/frida-server && /data/local/tmp/frida-server &"

# Run executor
python nest_executor.py --platform android --inject
```

#### iOS
- Requires jailbroken device
- Frida installed on device
- SSH access to device

```bash
# Connect to device
frida -U Roblox

# Or via USB
frida -D <device_id> Roblox
```

## Scripts

### Built-in Scripts
| Script | Description | Platform |
|--------|-------------|----------|
| clock | Show current time | All |
| fps_counter | Display FPS | All |
| auto_reconnect | Auto reconnect on disconnect | All |
| esp | Player ESP (through walls) | PC |
| aimbot | Aim assistance indicator | PC |
| auto_farm | Auto collect/farm | PC |
| spam | Chat spam (testing) | All |
| debug_inspector | Debug info display | All |

### Creating Custom Scripts

Create `.luau` files in `scripts/` directory:

```lua
-- my_script.luau
local Players = game:GetService("Players")
print("[NestExecutor] My script loaded!")
```

Load and execute:
```bash
python nest_executor.py --script my_script.luau --execute
```

## Security Notes

⚠️ **Use responsibly:**
- Only on games where you have permission
- For educational purposes
- Research and security testing
- NOT for cheating in multiplayer games

## Troubleshooting

### Injection Fails
- Ensure Roblox is running
- Check administrator privileges
- Verify anti-cheat is disabled (for research)

### Android Issues
- Ensure Frida server is running
- Check ADB connection: `adb devices`
- May need root access

### iOS Issues
- Device must be jailbroken
- Frida must be installed on device
- Trust certificate for unsigned apps

## API Reference

### Python API

```python
from executor import ExecutorFactory, ScriptManager

# Create executor
executor = ExecutorFactory.create("android")

# Inject
executor.inject()

# Load script
manager = ScriptManager(executor)
script = manager.load_from_file("my_script.luau")

# Execute
result = executor.execute_script(script)
print(result.output)

# Cleanup
executor.unload()
```

## Development

### Adding Platform Support

1. Create new class in `core/executor.py`:
```python
class NewPlatformExecutor(ExecutorCore):
    def _detect_platform(self):
        return PlatformConfig(name="newplatform", arch="arm64")
    
    def inject(self):
        # Platform-specific injection
        pass
```

2. Register in factory:
```python
ExecutorFactory._registry["newplatform"] = NewPlatformExecutor
```

## License

Educational/Research use only. See LICENSE for details.

## Credits

- Based on Roblox Lua/Luau scripting
- Frida framework for mobile injection
- Cross-platform architecture patterns
