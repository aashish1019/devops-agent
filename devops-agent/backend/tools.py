"""
Automated Code Fixing Tools Integration
Uses real-world tools instead of placeholder AI fixes
"""
import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def run_autopep8(file_path):
    """Run autopep8 to auto-fix Python linting issues"""
    try:
        result = subprocess.run(
            ['autopep8', '--in-place', '--aggressive', '--aggressive', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return False, "autopep8 not installed"
    except Exception as e:
        return False, str(e)

def run_black(file_path):
    """Run black to format Python code"""
    try:
        result = subprocess.run(
            ['black', '--quiet', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return False, "black not installed"
    except Exception as e:
        return False, str(e)

def run_flake8(file_path):
    """Run flake8 to detect linting issues (parse default text output)"""
    try:
        result = subprocess.run(
            ['flake8', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        # flake8 outputs: file:line:col: code message
        issues = []
        for line in (result.stdout or '').splitlines():
            parts = line.split(':', 3)
            if len(parts) >= 4:
                issues.append({
                    'line_number': int(parts[1]) if parts[1].isdigit() else 0,
                    'text': parts[3].strip()
                })
        return issues, result.stderr
    except FileNotFoundError:
        return [], "flake8 not installed"
    except Exception as e:
        return [], str(e)

def run_pylint(file_path):
    """Run pylint to detect errors and warnings (one JSON object per line)"""
    try:
        result = subprocess.run(
            ['pylint', '--output-format=json', file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        import json
        issues = []
        for line in (result.stdout or '').strip().splitlines():
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    issues.append(obj)
            except (json.JSONDecodeError, TypeError):
                pass
        return issues, result.stderr
    except FileNotFoundError:
        return [], "pylint not installed"
    except Exception as e:
        return [], str(e)

def run_mypy(file_path):
    """Run mypy to detect type errors"""
    try:
        result = subprocess.run(
            ['mypy', '--show-error-codes', '--no-error-summary', file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Parse mypy output
        errors = []
        for line in result.stdout.split('\n'):
            if 'error:' in line:
                errors.append(line.strip())
        return errors, result.stderr
    except FileNotFoundError:
        return [], "mypy not installed"
    except Exception as e:
        return [], str(e)

def run_bandit(file_path):
    """Run bandit to detect security issues"""
    try:
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        import json
        try:
            report = json.loads(result.stdout)
            issues = report.get('results', [])
        except:
            issues = []
        return issues, result.stderr
    except FileNotFoundError:
        return [], "bandit not installed"
    except Exception as e:
        return [], str(e)

def auto_fix_python_file(file_path):
    """Automatically fix Python file - use black only (autopep8 needs lib2to3, removed in Python 3.12+)"""
    fixes_applied = []
    
    # Skip autopep8 on Python 3.12+ (lib2to3 removed) - use black only
    try:
        import sys
        if sys.version_info < (3, 12):
            success, output = run_autopep8(file_path)
            if success:
                fixes_applied.append("autopep8: Fixed linting issues")
            else:
                logger.warning(f"autopep8 failed: {output}")
    except Exception as e:
        logger.warning(f"autopep8 skipped: {e}")
    
    # Run black (formats code)
    success, output = run_black(file_path)
    if success:
        fixes_applied.append("black: Formatted code")
    else:
        logger.warning(f"black failed: {output}")
    
    return fixes_applied

def detect_all_issues(work_dir, file_path=None):
    """Detect all issues in Python files using multiple tools"""
    all_issues = []
    
    if file_path and file_path.endswith('.py'):
        # Run all static analysis tools
        flake8_issues, _ = run_flake8(file_path)
        pylint_issues, _ = run_pylint(file_path)
        mypy_issues, _ = run_mypy(file_path)
        bandit_issues, _ = run_bandit(file_path)
        
        # Classify and add issues (handle various output formats)
        for issue in (flake8_issues if isinstance(flake8_issues, list) else []):
            if isinstance(issue, dict):
                all_issues.append({
                    'file': file_path,
                    'line': issue.get('line_number', issue.get('line', 0)),
                    'type': 'LINTING',
                    'message': issue.get('text', issue.get('message', str(issue))),
                    'tool': 'flake8'
                })
        
        for issue in (pylint_issues if isinstance(pylint_issues, list) else []):
            if isinstance(issue, dict):
                msg = issue.get('message', {})
                msg_text = msg.get('message', str(msg)) if isinstance(msg, dict) else str(msg)
                all_issues.append({
                    'file': file_path,
                    'line': issue.get('line', 0),
                    'type': classify_pylint_message(msg) if isinstance(msg, dict) else 'LOGIC',
                    'message': msg_text,
                    'tool': 'pylint'
                })
        
        for error in (mypy_issues if isinstance(mypy_issues, list) else []):
            all_issues.append({
                'file': file_path,
                'line': 0,
                'type': 'TYPE_ERROR',
                'message': str(error),
                'tool': 'mypy'
            })
        
        for issue in (bandit_issues if isinstance(bandit_issues, list) else []):
            if isinstance(issue, dict):
                all_issues.append({
                    'file': file_path,
                    'line': issue.get('line_number', 0),
                    'type': 'SECURITY',
                    'message': issue.get('issue_text', str(issue)),
                    'tool': 'bandit'
                })
    
    return all_issues

def classify_pylint_message(message_obj):
    """Classify pylint message type"""
    if not isinstance(message_obj, dict):
        return 'LOGIC'
    
    msg_id = message_obj.get('message-id', '')
    msg_type = message_obj.get('type', '')
    
    if 'C' in msg_id or 'convention' in msg_type:
        return 'LINTING'
    elif 'E' in msg_id or 'error' in msg_type:
        return 'SYNTAX'
    elif 'W' in msg_id or 'warning' in msg_type:
        return 'LOGIC'
    elif 'R' in msg_id or 'refactor' in msg_type:
        return 'LINTING'
    else:
        return 'LOGIC'

def fix_js_file(file_path):
    """Fix JavaScript/TypeScript file using ESLint (if available)"""
    try:
        # Check if ESLint is available
        result = subprocess.run(
            ['npx', 'eslint', '--fix', file_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(file_path)
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)
