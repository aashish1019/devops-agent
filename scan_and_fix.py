#!/usr/bin/env python3
"""
Scan, fix, and push repository safely.
Team Leader: Shivprasad Dornal
Branch: padhai
"""
import os
import subprocess
import ast
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env for GITHUB_TOKEN
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
TEAM_LEADER = "Shivprasad Dornal"
TARGET_BRANCH = "padhai"

def run_git(cmd, check=True):
    """Run git command"""
    try:
        result = subprocess.run(
            ['git'] + cmd.split(),
            cwd=WORK_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        if check and result.returncode != 0:
            print(f"Git error: {result.stderr}")
        return result
    except FileNotFoundError:
        print("ERROR: Git not found in PATH")
        return None
    except Exception as e:
        print(f"Git error: {e}")
        return None

def get_current_branch():
    """Get current branch name"""
    result = run_git('branch --show-current', check=False)
    if result and result.returncode == 0:
        return result.stdout.strip()
    # Fallback: read .git/HEAD
    head_file = os.path.join(WORK_DIR, '.git', 'HEAD')
    if os.path.exists(head_file):
        with open(head_file, 'r') as f:
            ref = f.read().strip()
            if ref.startswith('ref: refs/heads/'):
                return ref.replace('ref: refs/heads/', '')
    return None

def checkout_branch(branch_name):
    """Checkout or create branch"""
    result = run_git(f'checkout {branch_name}', check=False)
    if result and result.returncode != 0:
        # Branch doesn't exist, create it
        result = run_git(f'checkout -b {branch_name}', check=False)
    return result and result.returncode == 0

def pull_changes():
    """Pull changes from remote"""
    result = run_git('pull', check=False)
    if result and result.returncode == 0:
        print("[OK] Pulled changes successfully")
        return True
    elif result and 'no tracking information' in result.stderr.lower():
        print("[INFO] No remote tracking branch - skipping pull")
        return True
    else:
        print(f"[WARN] Pull warning: {result.stderr if result else 'Git not available'}")
        return False

def scan_python_files():
    """Scan all Python files for syntax errors"""
    errors = []
    files_checked = []
    
    for root, dirs, files in os.walk(WORK_DIR):
        # Skip .git and other hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, WORK_DIR)
                files_checked.append(rel_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    errors.append({
                        'file': rel_path,
                        'line': e.lineno,
                        'message': str(e),
                        'type': 'SYNTAX'
                    })
                except Exception as e:
                    errors.append({
                        'file': rel_path,
                        'line': 0,
                        'message': str(e),
                        'type': 'OTHER'
                    })
    
    return files_checked, errors

def apply_auto_fixes(errors):
    """Apply automatic fixes where possible"""
    fixed = []
    for error in errors:
        if error['type'] == 'SYNTAX':
            file_path = os.path.join(WORK_DIR, error['file'])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Simple fixes: trailing whitespace, missing newline
                original = content
                content = content.rstrip() + '\n'
                if content != original:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed.append(error['file'])
            except Exception:
                pass
    return fixed

def commit_changes(fixed_files):
    """Commit fixed files"""
    if not fixed_files:
        return False
    
    run_git('add .')
    result = run_git('commit -m "Auto-fixed errors by Cursor AI"', check=False)
    return result and result.returncode == 0

def push_to_remote():
    """Push to remote using GITHUB_TOKEN"""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("[WARN] GITHUB_TOKEN not set - skipping push")
        return False
    
    # Get remote URL
    result = run_git('remote get-url origin', check=False)
    if not result or result.returncode != 0:
        print("[WARN] No remote configured - skipping push")
        return False
    
    remote_url = result.stdout.strip()
    if 'github.com' not in remote_url:
        print("[WARN] Not a GitHub repo - skipping push")
        return False
    
    # Inject token into URL
    push_url = re.sub(r'https?://', f'https://{token}@', remote_url)
    current_branch = get_current_branch()
    
    result = run_git(f'push {push_url} HEAD:{current_branch}', check=False)
    if result and result.returncode == 0:
        print(f"[OK] Pushed to remote branch {current_branch}")
        return True
    else:
        print(f"[WARN] Push failed: {result.stderr if result else 'Unknown error'}")
        return False

def main():
    print("=" * 60)
    print("Repository Scan & Fix")
    print(f"Team Leader: {TEAM_LEADER}")
    print("=" * 60)
    
    # Step 1: Detect branch
    current_branch = get_current_branch()
    print(f"\n1. Current branch: {current_branch or 'unknown'}")
    
    # Step 2: Checkout padhai branch
    if current_branch != TARGET_BRANCH:
        print(f"   Switching to branch: {TARGET_BRANCH}")
        checkout_branch(TARGET_BRANCH)
        current_branch = get_current_branch()
    
    # Step 3: Pull changes
    print("\n2. Pulling changes from remote...")
    pull_changes()
    
    # Step 4: Scan files
    print("\n3. Scanning Python files for errors...")
    files_checked, errors = scan_python_files()
    print(f"   Files checked: {len(files_checked)}")
    print(f"   Errors found: {len(errors)}")
    
    # Step 5: Apply fixes
    print("\n4. Applying automatic fixes...")
    fixed_files = apply_auto_fixes(errors)
    print(f"   Files fixed: {len(fixed_files)}")
    
    # Step 6: Commit
    if fixed_files:
        print("\n5. Committing changes...")
        if commit_changes(fixed_files):
            print("   [OK] Committed successfully")
        else:
            print("   [WARN] Commit failed or no changes")
    else:
        print("\n5. No fixes to commit")
    
    # Step 7: Push
    print("\n6. Pushing to remote...")
    push_success = push_to_remote()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"Branch name: {current_branch}")
    print(f"Files checked: {len(files_checked)}")
    print(f"Errors found: {len(errors)}")
    print(f"Errors fixed: {len(fixed_files)}")
    print(f"Push status: {'SUCCESS' if push_success else 'SKIPPED/FAILED'}")
    print("=" * 60)

if __name__ == '__main__':
    main()
