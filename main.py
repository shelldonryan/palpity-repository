import subprocess
import time

def run_script(script_name):
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    print(result.stdout)

def main():
    print("🚀 Sistema automático iniciado...")
    run_script("scripts/collector.py")

    while True:
        time.sleep(60)
        run_script("scripts/analyzer.py")
        run_script("scripts/predictor.py")

if __name__ == "__main__":
    main()