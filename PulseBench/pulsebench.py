import os
import json
import sys
import subprocess
import argparse
import shutil
import time
from datetime import datetime
import psutil

ENV_FILE = "pulsebench_env.json"

def load_environment():
    if not os.path.exists(ENV_FILE):
        print("❌ Environment file 'pulsebench_env.json' not found. Please run setup.py first.")
        sys.exit(1)
    with open(ENV_FILE, "r") as f:
        return json.load(f)

def run_command(command, verbose):
    if verbose:
        return subprocess.run(command, check=True)
    else:
        return subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_tool(tool):
    return shutil.which(tool) is not None

def cpu_benchmark(cpu_threads, verbose):
    if not check_tool("sysbench"):
        print("❌ sysbench not found. Please run setup.py or install it manually.")
        sys.exit(1)
    print("\n🧠 Running CPU benchmark...")
    cmd = ["sysbench", "cpu", f"--threads={cpu_threads}", "run"]
    run_command(cmd, verbose)

def disk_benchmark(verbose):
    if not check_tool("fio"):
        print("❌ fio not found. Please run setup.py or install it manually.")
        sys.exit(1)
    print("\n💾 Running Disk benchmark...")
    cmd = ["fio", "--name=randwrite", "--ioengine=libaio", "--rw=randwrite", "--bs=4k", "--size=100M", "--numjobs=1", "--runtime=30", "--time_based", "--group_reporting"]
    run_command(cmd, verbose)

def memory_benchmark(verbose):
    if not check_tool("sysbench"):
        print("❌ sysbench not found. Please run setup.py or install it manually.")
        sys.exit(1)
    print("\n🧠 Running Memory benchmark...")
    cmd = ["sysbench", "memory", "run"]
    run_command(cmd, verbose)

def gpu_benchmark(verbose):
    if not check_tool("glmark2"):
        print("⚠️  glmark2 not found. Skipping GPU benchmark.")
        return
    if "DISPLAY" not in os.environ:
        print("⚠️  No graphical environment detected. Skipping GPU benchmark.")
        return
    print("\n🎮 Running GPU benchmark...")
    cmd = ["glmark2"]
    run_command(cmd, verbose)

def parse_args():
    parser = argparse.ArgumentParser(description="PulseBench - System Benchmark Suite")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-l", "--loop", type=int, help="Loop benchmark suite N times")
    parser.add_argument("-s", "--stepped", action="store_true", help="Run benchmarks step-by-step, waiting for input")
    return parser.parse_args()

def main():
    args = parse_args()
    env = load_environment()

    distro = env.get("distro", "Unknown")
    cpu_threads = env.get("cpu_threads") or psutil.cpu_count(logical=True)

    def pause():
        if args.stepped:
            input("\n⏸️  Press Enter to continue...")

    loop_count = args.loop if args.loop else 1

    for i in range(loop_count):
        print(f"\n🚀 Starting benchmark run {i + 1}/{loop_count}")
        print("=" * 50)
        print(f"🖥️  Distro: {distro}")
        print(f"🧵 CPU Threads: {cpu_threads}")
        print(f"⏱️  Timestamp: {datetime.utcnow().isoformat()} UTC")

        cpu_benchmark(cpu_threads, args.verbose)
        pause()

        memory_benchmark(args.verbose)
        pause()

        disk_benchmark(args.verbose)
        pause()

        gpu_benchmark(args.verbose)
        pause()

        print("\n✅ Benchmark run completed.")
        print("=" * 50)

if __name__ == "__main__":
    main()
