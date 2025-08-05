"""
FlatBuffers code generation script for HTTP Interceptor

Usage:
    python scripts/generate_flatbuffers.py
"""
import subprocess
import sys
from pathlib import Path

def generate_backend():
    project_root = Path(__file__).parent.parent
    schema_file = project_root / "schema" / "backend.fbs" 
    output_file = project_root / "backend" / "models"
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    command = f"flatc --python --gen-onefile --gen-all -o {output_file} {schema_file}"
    
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=project_root)
        if result.stdout:
            print(result.stdout.decode(errors="ignore"))
        
        if result.stderr:
            print(result.stderr.decode(errors="ignore"))
    except subprocess.CalledProcessError as e:
        print(f"Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_backend()
