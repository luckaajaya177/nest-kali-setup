# NestExecutor Build Guide

## Build Instructions by Platform

### Windows (Primary)

#### Prerequisites
- .NET 6.0 SDK or higher
- Visual Studio 2022 (optional, for IDE)

#### Build Steps

**Option 1: Command Line**
```bash
cd tools/roblox-universal-executor/WindowsExecutor
dotnet restore
dotnet build --configuration Release
```

**Option 2: Using build script**
```bash
chmod +x build.sh
./build.sh
```

**Output:** `WindowsExecutor/bin/Release/net6.0-windows/NestExecutor.exe`

---

### macOS

#### Prerequisites
- .NET 6.0 SDK
- Mono (optional, for older Roblox versions)

#### Build Steps
```bash
cd tools/roblox-universal-executor
python3 -m py_compile core/NestCore.py
```

---

### Linux

#### Prerequisites
- .NET 6.0 SDK
- Wine (for Windows builds) or native Linux build

#### Build Steps
```bash
cd tools/roblox-universal-executor
dotnet build --configuration Release
```

---

### Android

#### Prerequisites
- Android Studio
- Frida-server on device
- ADB connected

#### Setup Steps
```bash
# Push Frida server to device
adb push android/frida-server /data/local/tmp/
adb shell "chmod +x /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"

# Run via Frida
frida -U -f com.roblox.client -l android/agent.js
```

---

### iOS

#### Prerequisites
- Jailbroken device
- Frida installed on device
- SSH access

#### Setup Steps
```bash
# Connect to device
frida -U Roblox -l ios/agent.js
```

---

## Dependencies

### Python Core
```bash
pip install psutil
```

### Windows
- Newtonsoft.Json (included in .csproj)

### Android/iOS
- Frida CLI tools
- ADB (Android Debug Bridge)

---

## First Run

### Windows
```bash
# Run as Administrator for injection
.\NestExecutor.exe
```

### macOS/Linux
```bash
sudo python3 nest_executor.py --inject
```

### Android
```bash
frida -U -f com.roblox.client -l android/agent.js
```

---

## Troubleshooting

### Windows Injection Fails
- Run as Administrator
- Close Roblox completely before injecting
- Check antivirus blocking

### macOS Memory Access
- Requires sudo for ptrace
- May need System Integrity Protection disabled

### Android Connection
- Ensure Frida server is running
- Check ADB connection: `adb devices`
- May need root access

### iOS
- Jailbreak required
- Trust certificate for unsigned apps
