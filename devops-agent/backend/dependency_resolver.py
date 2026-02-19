"""
Dependency Resolver - Fixes missing package issues
When ImportError/ModuleNotFoundError occurs, adds package to requirements.txt
"""
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def find_requirements_file(work_dir):
    """Find requirements file in project"""
    candidates = [
        'requirements.txt',
        'requirements-dev.txt',
        'pyproject.toml',
        'setup.py',
        'setup.cfg',
    ]
    
    for candidate in candidates:
        path = os.path.join(work_dir, candidate)
        if os.path.exists(path):
            return path
    
    return os.path.join(work_dir, 'requirements.txt')

def get_existing_packages(requirements_path):
    """Parse existing packages from requirements file"""
    if not os.path.exists(requirements_path):
        return set()
    
    packages = set()
    with open(requirements_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (ignore version specifiers for comparison)
                pkg = re.split(r'[=<>!~]', line)[0].strip().lower()
                if pkg:
                    packages.add(pkg)
    
    return packages

def add_package_to_requirements(work_dir, package_name, requirements_path=None):
    """
    Add missing package to requirements.txt
    Returns: (success, message)
    """
    if not requirements_path:
        requirements_path = find_requirements_file(work_dir)
    
    # Normalize package name (some errors show email_validator, pip needs email-validator)
    package_normalized = package_name.replace('_', '-').lower()
    
    existing = get_existing_packages(requirements_path)
    
    # Check if already present (handle both formats)
    if package_normalized in existing or package_name.replace('-', '_') in existing:
        return False, f"Package {package_name} already in requirements"
    
    # Create requirements.txt if it doesn't exist
    if not os.path.exists(requirements_path):
        os.makedirs(os.path.dirname(requirements_path) or '.', exist_ok=True)
    
    # Append package
    try:
        with open(requirements_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{package_normalized}\n")
        logger.info(f"Added {package_normalized} to {requirements_path}")
        return True, f"Added {package_normalized} to requirements"
    except Exception as e:
        logger.error(f"Failed to add package: {e}")
        return False, str(e)

def fix_dependency_error(work_dir, package_name):
    """
    Fix dependency error by adding package and running pip install
    Returns: (success, message)
    """
    success, msg = add_package_to_requirements(work_dir, package_name)
    if not success:
        return success, msg
    
    # Run pip install to verify
    import subprocess
    try:
        result = subprocess.run(
            ['pip', 'install', package_name.replace('_', '-')],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, f"Added and installed {package_name}"
        else:
            return True, f"Added to requirements (install may need: pip install -r requirements.txt)"
    except Exception as e:
        return True, f"Added to requirements.txt: {msg}"
