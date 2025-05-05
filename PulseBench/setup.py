#!/usr/bin/env python3

import os
import platform
import json
import subprocess
import shutil
import sys
from datetime import datetime, timezone

try:
    import psutil
except ImportError:
    print("Installing missing Python module 'psutil'...")
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

REQUIRED_TOOLS = ["sysbench", "fio", "cyclictest", "glmark2"]

DISTRO_PACKAGE_MAP = {
    "arch": ["sysbench", "fio", "rt-tests", "glmark2"],
    "manjaro": ["sysbench", "fio", "rt-tests", "glmark2"],
    "ubuntu": ["sysbench", "fio", "rt-tests", "glmark2"],
    "debian": ["sysbench", "fio", "rt-tests", "glmark2"],
    "fedora": ["sysbench", "fio", "rt-tests", "glmark2"],
    "rhel": ["epel-release", "sysbench", "fio", "rt-tests", "glmark2"],
    "centos": ["epel-release", "sysbench", "fio", "rt-tests", "glmark2"],
    "almalinux": ["epel-release", "sysbench", "fio", "rt-tests", "glmark2"],
    "opensuse": ["sysbench", "fio", "rt-tests", "glmark2"],
    "gentoo": ["app-benchmarks/sysbench", "app-benchmarks/fio", "sys-process/rt-tests", "x11-misc/glmark2"],
    "steamos": ["sysbench", "fio", "rt-tests", "glmark2"],
    "chromeos": ["sysbench", "fio", "rt-tests", "glmark2"],
}

PACKAGE_MANAGERS = {
    "arch": ["pacman", "-S", "--noconfirm"],
    "manjaro": ["pacman", "-S", "--noconfirm"],
    "ubuntu": ["apt", "install", "-y"],
    "debian": ["apt", "install", "-y"],
    "fedora": ["dnf", "install", "-y"],
    "rhel": ["dnf", "install", "-y"],
    "centos": ["yum", "install", "-y"],
    "almalinux": ["dnf", "install", "-y"],
    "opensuse": ["zypper", "install", "-y"],
    "gentoo": ["emerge", "--ask=n"],
    "steamos": ["apt", "install", "-y"],
    "chromeos": ["apt", "install", "-y"]
}

def detect_distro():
    try:
        return platform.freedesktop_os_release().get("ID", "").lower()
    except Exception:
        return platform.system().lower()

def is_wsl():
    return "WSL" in platform.release()

def is_container():
    try:
        with open("/proc/1/cgroup", "rt", errors="ignore") as f:
            return any("container" in line for line in f)
    except Exception:
        return False

def check_required_tools(tools):
    return [tool for tool in tools if not shutil.which(tool)]

def install_packages(distro, packages):
    manager = PACKAGE_MANAGERS.get(distro)
    if not manager:
        print(f"❌ Unknown package manager for distro: {distro}. Install manually: {packages}")
        return

    print(f"📦 Installing missing packages with: {' '.join(manager)}")
    try:
        subprocess.run(["sudo"] + manager + packages, check=True)
        print("✅ Installation successful.")
    except subprocess.CalledProcessError:
        print("❌ Package installation failed. Please check your internet connection or package sources.")
        sys.exit(1)

def collect_system_info():
    return {
        "distro": detect_distro(),
        "kernel": platform.uname().release,
        "arch": platform.machine(),
        "cpu": platform.processor() or "Unknown",
        "cpu_threads": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "is_wsl": is_wsl(),
        "is_container": is_container(),
        "collected_at": datetime.now(timezone.utc).isoformat()
    }

def save_env_file(info, filename="pulsebench_env.json"):
    with open(filename, "w") as f:
        json.dump(info, f, indent=4)

def main():
    print("🔧 PulseBench: Auto-Setup Mode")
    system_info = collect_system_info()
    distro = system_info["distro"]

    print(f"Detected Distro:      {distro}")
    print(f"Kernel:               {system_info['kernel']}")
    print(f"CPU:                  {system_info['cpu']} ({system_info['cpu_threads']} threads)")
    print(f"RAM:                  {system_info['ram_gb']} GB")
    print(f"Architecture:         {system_info['arch']}")
    if system_info['is_wsl']:
        print("⚠️  Running inside WSL")
    if system_info['is_container']:
        print("⚠️  Running inside a container")

    missing_tools = check_required_tools(REQUIRED_TOOLS)
    if missing_tools:
        print(f"\n🚨 Missing tools: {', '.join(missing_tools)}")
        packages = DISTRO_PACKAGE_MAP.get(distro, [])
        if not packages:
            print("❌ Cannot determine package list for your distro. Install manually.")
            sys.exit(1)

        install_packages(distro, packages)
        # Re-check after install
        missing_tools = check_required_tools(REQUIRED_TOOLS)
        if missing_tools:
            print(f"❌ Still missing: {', '.join(missing_tools)}. Please resolve manually.")
            sys.exit(1)

    print("✅ All required tools are installed.")
    save_env_file(system_info)
    print(f"\n📝 System profile saved to 'pulsebench_env.json'")
    print("✅ Setup complete. Ready to run: ./pulsebench.py")

if __name__ == "__main__":
    main()
