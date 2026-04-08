import subprocess
import sys

def run_script(script_name):
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_name}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    scripts = [
    "cluster.py",
    "getRoute.py",
    "packageFeatures.py",
    "routeFeatures.py",
    "finalFeatures.py"
]
    
    for script in scripts:
        run_script(script)
    
    print("All scripts executed in order.")