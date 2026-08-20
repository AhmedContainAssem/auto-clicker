"""
Automated PyInstaller Build Script for MicroClicker Pro.
Cleans previous caches, generates missing icons, and compiles standalone Windows EXE.
"""

import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_FILE = os.path.join(SCRIPT_DIR, "autoclicker.ico")


def ensure_icon():
    if not os.path.exists(ICON_FILE):
        print("[*] Generating missing application icon (autoclicker.ico)...")
        try:
            from generate_icon import generate_ico
            generate_ico(ICON_FILE)
        except Exception as e:
            print(f"[!] Could not generate icon: {e}")


def clean_previous_builds():
    print("[*] Cleaning old build artifacts and caches...")
    dirs_to_clean = ["build", "__pycache__", "auto-clicker/__pycache__"]
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception:
                pass

    for f in ["AutoClickerPro.spec", "MicroClicker.spec"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass


def build():
    # Detect target entry point
    target_script = "main.py"
    if "--micro" in sys.argv:
        target_script = "micro_clicker.py"
        app_name = "MicroClicker"
    else:
        target_script = "main.py"
        app_name = "AutoClickerPro"

    print(f"============================================================")
    print(f"[*] Building {app_name} from {target_script}")
    print(f"============================================================")

    clean_previous_builds()
    ensure_icon()

    # Determine data separator (; on Windows, : on Unix)
    sep = ";" if sys.platform == "win32" or os.name == "nt" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        f"--name={app_name}",
    ]

    if os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
        cmd.append(f"--add-data={ICON_FILE}{sep}.")

    if os.path.exists("config.json"):
        cmd.append(f"--add-data=config.json{sep}.")

    cmd.append(target_script)

    print(f"[*] Executing PyInstaller command:\n{' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True)
        print("\n============================================================")
        print(f"[✓] BUILD COMPLETED SUCCESSFULLY!")
        print(f"[✓] Executable is located at: dist/{app_name}.exe")
        print(f"[✓] System Tray & Taskbar Icon embedded.")
        print("============================================================\n")

        # Clean build directory afterwards to keep workspace clean
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists(f"{app_name}.spec"):
            os.remove(f"{app_name}.spec")

    except subprocess.CalledProcessError as e:
        print(f"\n[-] Build failed with exit code: {e.returncode}")
        print("[-] Ensure pyinstaller is installed: pip install pyinstaller")
    except Exception as e:
        print(f"\n[-] Unexpected error during build: {e}")


if __name__ == "__main__":
    build()
