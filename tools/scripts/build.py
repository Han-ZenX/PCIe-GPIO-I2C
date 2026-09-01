#!/usr/bin/env python3
"""
固件构建辅助脚本
用法: python build.py --board=default --release
"""

import argparse
import subprocess
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="固件构建脚本")
    parser.add_argument("--board", default="default", help="目标板级名称")
    parser.add_argument("--release", action="store_true", help="Release构建")
    parser.add_argument("--flash", action="store_true", help="构建后自动烧录")
    parser.add_argument("--clean", action="store_true", help="清理构建目录")
    args = parser.parse_args()

    firmware_dir = os.path.join(os.path.dirname(__file__), "..", "firmware")
    build_dir = os.path.join(firmware_dir, "build")

    if args.clean and os.path.exists(build_dir):
        import shutil
        shutil.rmtree(build_dir)
        print("[OK] 构建目录已清理")
        return

    build_type = "Release" if args.release else "Debug"

    # Configure
    cmd_config = [
        "cmake", "-B", build_dir,
        f"-DBOARD={args.board}",
        f"-DCMAKE_BUILD_TYPE={build_type}"
    ]
    print(f"[BUILD] Configure: {args.board} ({build_type})")
    subprocess.check_call(cmd_config, cwd=firmware_dir)

    # Build
    cmd_build = ["cmake", "--build", build_dir, "-j"]
    print("[BUILD] Compiling...")
    subprocess.check_call(cmd_build)

    if args.flash:
        print("[FLASH] TODO: 实现烧录命令")
        # subprocess.check_call(["openocd", ...])

    print("[DONE] 构建完成")

if __name__ == "__main__":
    main()
