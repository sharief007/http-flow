"""
FlatBuffers code generation script for HTTP Interceptor

Usage:
    python scripts/generate_flatbuffers.py
"""
import subprocess
import sys
from pathlib import Path

def _generate(command: str):
    project_root = Path(__file__).parent.parent
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=project_root)
        if result.stdout:
            print(result.stdout.decode(errors="ignore"))
        
        if result.stderr:
            print(result.stderr.decode(errors="ignore"))
    except subprocess.CalledProcessError as e:
        print(f"Generation failed: {e}")
        sys.exit(1)

def generate_python_stubs():
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "backend" / "models"

    command = f"flatc --python --gen-onefile --gen-all -o {output_dir} {schema_file}"
    schema_file = project_root / "schema" / "backend.fbs"
    _generate(command)
    
    schema_file = project_root / "schema" / "events.fbs"
    command = f"flatc --python --gen-onefile -o {output_dir} {schema_file}"
    _generate(command)
    

def generate_ts_stubs():
    project_root = Path(__file__).parent.parent
    schema_file = project_root / "schema" / "events.fbs" 
    output_dir = project_root / "frontend" / "src" / "models"
    command = f"flatc --ts --gen-object-api --gen-all -o {output_dir} {schema_file}"
    _generate(command)


if __name__ == "__main__":
    generate_python_stubs()
    generate_ts_stubs()
