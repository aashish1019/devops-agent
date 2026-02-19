from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
import shutil
import json
import re
import tempfile
from pathlib import Path
import time
from datetime import datetime
import traceback
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Store active jobs
jobs = {}

# Use workspace inside project to avoid Windows temp permission issues
try:
    WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workspace')
except Exception:
    # Fallback if __file__ is not available
    WORKSPACE_DIR = os.path.join(os.getcwd(), 'workspace')

def safe_cleanup(work_dir):
    """Safely remove work directory - handles Windows file lock issues"""
    if not work_dir or not os.path.exists(work_dir):
        return
    
    for attempt in range(3):
        try:
            # On Windows, git may lock .git files - add delay before retry
            if attempt > 0:
                time.sleep(2)
            shutil.rmtree(work_dir, ignore_errors=False)
            logger.info(f"Cleaned up work_dir: {work_dir}")
            return
        except (PermissionError, OSError) as e:
            err = getattr(e, 'winerror', getattr(e, 'errno', None))
            logger.warning(f"Cleanup attempt {attempt + 1} failed (err={err}): {e}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    # Final attempt: remove what we can, ignore errors (never raise)
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
        logger.warning(f"Partial cleanup of {work_dir} - some files may remain")
    except Exception:
        pass  # Never propagate - cleanup must not fail the request

def clone_repository(repo_url, work_dir):
    """Clone repository to temporary directory"""
    try:
        # Check if git is available
        git_check = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if git_check.returncode != 0:
            return False, "Git is not installed or not in PATH. Please install Git."
        
        result = subprocess.run(
            ['git', 'clone', repo_url, work_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown git clone error"
            return False, f"Git clone failed: {error_msg}"
        return True, None
    except FileNotFoundError:
        return False, "Git is not installed or not in PATH. Please install Git."
    except subprocess.TimeoutExpired:
        return False, "Git clone timed out after 120 seconds"
    except Exception as e:
        return False, f"Error cloning repository: {str(e)}"

def discover_test_files(work_dir):
    """Discover all test files in the repository"""
    test_files = []
    test_patterns = [
        '**/test_*.py',
        '**/*_test.py',
        '**/tests/**/*.py',
        '**/test/**/*.py',
        '**/*.test.js',
        '**/*.spec.js',
        '**/__tests__/**/*.js',
        '**/*.test.ts',
        '**/*.spec.ts',
    ]
    
    for pattern in test_patterns:
        for file in Path(work_dir).rglob(pattern):
            if file.is_file():
                test_files.append(str(file.relative_to(work_dir)))
    
    return test_files

def detect_test_runner(work_dir):
    """Detect which test runner to use"""
    if os.path.exists(os.path.join(work_dir, 'package.json')):
        return 'npm'
    elif os.path.exists(os.path.join(work_dir, 'pytest.ini')) or \
         any(f.endswith('test_') or f.startswith('test_') for f in os.listdir(work_dir) if os.path.isfile(os.path.join(work_dir, f))):
        return 'pytest'
    elif os.path.exists(os.path.join(work_dir, 'requirements.txt')):
        return 'pytest'  # Default for Python
    return None

def run_tests(work_dir, test_runner):
    """Run tests and capture output"""
    try:
        if test_runner == 'pytest':
            result = subprocess.run(
                ['python', '-m', 'pytest', '-v', '--tb=short'],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
        elif test_runner == 'npm':
            # Install dependencies first
            subprocess.run(['npm', 'install'], cwd=work_dir, capture_output=True, timeout=120)
            result = subprocess.run(
                ['npm', 'test'],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
        else:
            return None, "Unknown test runner", []
        
        failures = parse_test_failures(result.stdout + result.stderr, test_runner)
        return result.returncode == 0, result.stdout + result.stderr, failures
    except subprocess.TimeoutExpired:
        return False, "Test execution timed out", []
    except Exception as e:
        return False, str(e), []

def parse_test_failures(output, test_runner):
    """Parse test output to extract ALL failure information"""
    failures = []
    
    if test_runner == 'pytest':
        # Parse pytest failures - improved to catch ALL errors
        lines = output.split('\n')
        current_failure = None
        in_traceback = False
        
        for i, line in enumerate(lines):
            # Match FAILED test lines (multiple patterns)
            if 'FAILED' in line or 'ERROR' in line:
                # Save previous failure if exists
                if current_failure:
                    failures.append(current_failure)
                
                # Extract test file and name
                match = re.search(r'(\w+)::(\w+)', line)
                if match:
                    current_failure = {
                        'test_file': match.group(1),
                        'test_name': match.group(2),
                        'error_type': 'LOGIC',
                        'line': None,
                        'message': '',
                        'full_error': line
                    }
                else:
                    # Try alternative pattern
                    file_match = re.search(r'(\S+\.py)::(\w+)', line)
                    if file_match:
                        current_failure = {
                            'test_file': file_match.group(1),
                            'test_name': file_match.group(2),
                            'error_type': 'LOGIC',
                            'line': None,
                            'message': '',
                            'full_error': line
                        }
                in_traceback = True
            
            # Extract error type and line number
            elif current_failure:
                # Check for various error types
                error_type = classify_error(line)
                if error_type != 'LOGIC' or 'Error' in line or 'Exception' in line:
                    current_failure['error_type'] = error_type
                
                # Extract line number (multiple patterns)
                line_match = re.search(r'line (\d+)', line)
                if not line_match:
                    line_match = re.search(r':(\d+):', line)
                if not line_match:
                    line_match = re.search(r'\(line (\d+)\)', line)
                if line_match:
                    try:
                        current_failure['line'] = int(line_match.group(1))
                    except:
                        pass
                
                # Collect error message
                if line.strip() and not line.startswith('=') and not line.startswith('-'):
                    current_failure['message'] += line + '\n'
                    current_failure['full_error'] += '\n' + line
                    
                    # Limit message size but keep collecting
                    if len(current_failure['message']) > 500:
                        current_failure['message'] = current_failure['message'][:500] + '...'
        
        # Add last failure if exists
        if current_failure:
            failures.append(current_failure)
        
        # Also catch any ERROR lines we might have missed
        for i, line in enumerate(lines):
            if 'ERROR' in line and 'FAILED' not in line:
                error_match = re.search(r'(\S+\.py)::(\w+)', line)
                if error_match:
                    failures.append({
                        'test_file': error_match.group(1),
                        'test_name': error_match.group(2),
                        'error_type': classify_error(line),
                        'line': None,
                        'message': line,
                        'full_error': line
                    })
    
    elif test_runner == 'npm':
        # Parse npm/jest failures - improved
        lines = output.split('\n')
        current_failure = None
        
        for line in lines:
            if 'FAIL' in line or 'Error' in line or '✕' in line:
                if current_failure:
                    failures.append(current_failure)
                
                # Extract test file and name
                test_match = re.search(r'(\S+\.(test|spec)\.(js|ts|jsx|tsx))', line)
                file_match = re.search(r'at (\S+\.(js|ts|jsx|tsx)):(\d+):', line)
                
                current_failure = {
                    'test_file': test_match.group(1) if test_match else (file_match.group(1) if file_match else 'unknown'),
                    'test_name': 'unknown',
                    'error_type': classify_error(line),
                    'line': int(file_match.group(3)) if file_match else None,
                    'message': line,
                    'full_error': line
                }
            elif current_failure:
                current_failure['message'] += '\n' + line
                current_failure['full_error'] += '\n' + line
        
        if current_failure:
            failures.append(current_failure)
    
    return failures

def classify_error(error_message):
    """Classify error type - improved to catch ALL error types"""
    if not error_message:
        return 'LOGIC'
    
    error_lower = error_message.lower()
    
    # SYNTAX errors
    if any(keyword in error_lower for keyword in ['syntax', 'invalid syntax', 'syntaxerror', 'parse error', 'unexpected token']):
        return 'SYNTAX'
    
    # IMPORT errors
    if any(keyword in error_lower for keyword in ['import', 'module', 'modulenotfound', 'importerror', 'cannot find module']):
        return 'IMPORT'
    
    # TYPE errors
    if any(keyword in error_lower for keyword in ['typeerror', 'type error', 'wrong type', 'expected', 'got']):
        return 'TYPE_ERROR'
    
    # INDENTATION errors
    if any(keyword in error_lower for keyword in ['indentation', 'indent', 'unindent', 'expected an indented block']):
        return 'INDENTATION'
    
    # LINTING errors
    if any(keyword in error_lower for keyword in ['lint', 'flake8', 'pylint', 'eslint', 'unused', 'undefined']):
        return 'LINTING'
    
    # ATTRIBUTE errors
    if any(keyword in error_lower for keyword in ['attributeerror', 'has no attribute', 'undefined', 'is not defined']):
        return 'TYPE_ERROR'
    
    # KEY errors
    if any(keyword in error_lower for keyword in ['keyerror', 'key not found']):
        return 'LOGIC'
    
    # VALUE errors
    if any(keyword in error_lower for keyword in ['valueerror', 'invalid value']):
        return 'LOGIC'
    
    # NAME errors
    if any(keyword in error_lower for keyword in ['nameerror', 'name is not defined']):
        return 'SYNTAX'
    
    # DEFAULT to LOGIC
    return 'LOGIC'

def generate_fix(failure, work_dir):
    """Generate fix for a failure (simplified - in production, use AI/LLM)"""
    # This is a placeholder - in production, you'd use GPT/Claude/etc.
    fix_suggestions = {
        'SYNTAX': 'Check syntax errors in the code',
        'IMPORT': 'Verify import statements and dependencies',
        'TYPE_ERROR': 'Check type compatibility',
        'INDENTATION': 'Fix indentation issues',
        'LINTING': 'Fix linting errors',
        'LOGIC': 'Review logic and fix assertion failures'
    }
    return fix_suggestions.get(failure['error_type'], 'Review and fix the error')

def apply_fix(failure, work_dir):
    """Apply fix to the code (simplified)"""
    # In production, this would use AI to generate and apply actual fixes
    # For now, we'll just return a placeholder
    return True, "Fix applied (placeholder - use AI in production)"

def create_branch_and_commit(work_dir, branch_name, fixes):
    """Create branch, commit fixes, and push"""
    try:
        # Create branch
        subprocess.run(['git', 'checkout', '-b', branch_name], cwd=work_dir, check=True)
        
        # Stage all changes
        subprocess.run(['git', 'add', '.'], cwd=work_dir, check=True)
        
        # Commit with [AI-AGENT] prefix
        commit_msg = f"[AI-AGENT] Fix {len(fixes)} error(s)"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=work_dir, check=True)
        
        # Push (this would require authentication in production)
        # subprocess.run(['git', 'push', '-u', 'origin', branch_name], cwd=work_dir, check=True)
        
        return True, None
    except Exception as e:
        return False, str(e)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        'message': 'DevOps Agent API is running',
        'version': '1.0.0',
        'endpoints': {
            'analyze': '/api/analyze (POST)',
            'status': '/api/status/<job_id> (GET)',
            'jobs': '/api/jobs (GET)'
        },
        'frontend': 'http://localhost:3000'
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'devops-agent-api'})

@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """Main endpoint to analyze repository"""
    job_id = None
    work_dir = None
    
    try:
        logger.info("Received analyze request")
        
        if not request.json:
            logger.error("No JSON body in request")
            return jsonify({'error': 'JSON body required'}), 400
        
        data = request.json
        repo_url = data.get('repo_url')
        logger.info(f"Repository URL: {repo_url}")
        
        if not repo_url:
            logger.error("No repository URL provided")
            return jsonify({'error': 'Repository URL required'}), 400
    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400
    
    # Generate job ID
    job_id = f"job_{int(time.time())}"
    jobs[job_id] = {
        'status': 'cloning',
        'progress': 0,
        'results': None,
        'start_time': datetime.now().isoformat()
    }
    
    # Create work directory (use project workspace to avoid Windows temp permission issues)
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        work_dir = os.path.join(WORKSPACE_DIR, f"job_{job_id}")
        logger.info(f"Work directory: {work_dir}")
    except Exception as e:
        logger.error(f"Failed to create workspace directory: {e}")
        # Fallback to temp directory
        work_dir = os.path.join(tempfile.gettempdir(), f"devops_agent_{job_id}")
        logger.info(f"Using fallback work directory: {work_dir}")
    
    try:
        # Step 1: Clone repository
        logger.info("Starting repository clone...")
        jobs[job_id]['status'] = 'cloning'
        jobs[job_id]['progress'] = 10
        success, error = clone_repository(repo_url, work_dir)
        if not success:
            logger.error(f"Clone failed: {error}")
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = error
            return jsonify({'job_id': job_id, 'status': 'failed', 'error': error}), 500
        logger.info("Repository cloned successfully")
        
        # Step 2: Discover test files
        logger.info("Discovering test files...")
        jobs[job_id]['status'] = 'discovering_tests'
        jobs[job_id]['progress'] = 30
        test_files = discover_test_files(work_dir)
        logger.info(f"Found {len(test_files)} test files")
        
        # Step 3: Detect test runner
        logger.info("Detecting test runner...")
        test_runner = detect_test_runner(work_dir)
        logger.info(f"Test runner detected: {test_runner}")
        if not test_runner:
            logger.warning("No test runner detected")
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = 'No test runner detected'
            return jsonify({'job_id': job_id, 'status': 'failed', 'error': 'No test runner detected'}), 500
        
        # Step 4: Run tests
        logger.info("Running tests...")
        jobs[job_id]['status'] = 'running_tests'
        jobs[job_id]['progress'] = 50
        all_passed, test_output, failures = run_tests(work_dir, test_runner)
        logger.info(f"Tests completed. Passed: {all_passed}, Failures: {len(failures)}")
        
        # Step 5: Generate fixes
        jobs[job_id]['status'] = 'fixing'
        jobs[job_id]['progress'] = 70
        fixes = []
        for failure in failures:
            fix_desc = generate_fix(failure, work_dir)
            fixes.append({
                'file': failure.get('test_file', 'unknown'),
                'bug_type': failure['error_type'],
                'line': failure.get('line', 0),
                'fix_description': fix_desc,
                'status': 'pending'
            })
        
        # Step 6: Create branch and commit (optional - don't fail if git ops have permission issues)
        jobs[job_id]['status'] = 'committing'
        jobs[job_id]['progress'] = 90
        
        # Extract repo name for branch
        repo_name = repo_url.split('/')[-1].replace('.git', '').upper()
        branch_name = f"{repo_name}_AI_Fix"
        
        try:
            success, error = create_branch_and_commit(work_dir, branch_name, fixes)
            if not success:
                logger.warning(f"Git commit failed (non-fatal): {error}")
        except Exception as git_err:
            logger.warning(f"Git operations failed (non-fatal): {git_err}")
        
        # Step 7: Generate results
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        
        results = {
            'repository': repo_url,
            'branch': branch_name,
            'total_failures': len(failures),
            'total_fixes': len(fixes),
            'iterations': 1,
            'final_status': 'PASSED' if all_passed else 'FAILED',
            'test_files': test_files,
            'test_output': test_output,
            'fixes': fixes
        }
        
        jobs[job_id]['results'] = results
        
        # Cleanup (non-blocking, won't fail the request)
        safe_cleanup(work_dir)
        
        return jsonify({'job_id': job_id, 'results': results})
    
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Exception in analyze_repository: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        
        if job_id:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['traceback'] = error_trace
        
        # Cleanup in background
        if work_dir:
            try:
                safe_cleanup(work_dir)
            except Exception as cleanup_err:
                logger.error(f"Cleanup error: {cleanup_err}")
        
        # Return error response
        error_response = {
            'job_id': job_id or 'unknown',
            'status': 'failed', 
            'error': str(e)
        }
        
        if app.debug:
            error_response['details'] = error_trace[:1000]  # Limit size
        
        return jsonify(error_response), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get status of a job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    return jsonify({'jobs': list(jobs.keys())})

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Error: {str(error)}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

if __name__ == '__main__':
    print("Starting DevOps Agent Backend...")
    print("Logging enabled - check console for detailed errors")
    print("Backend will run on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    try:
        app.run(debug=True, port=5000, host='127.0.0.1', use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Fatal error starting server: {e}")
        traceback.print_exc()
