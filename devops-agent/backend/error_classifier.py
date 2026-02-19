"""
Error Classification Module
Classifies failures into categories for targeted fixing
"""
import re
import logging

logger = logging.getLogger(__name__)

# Failure Classification Patterns
FAILURE_PATTERNS = [
    # DEPENDENCY - Must fix first (environment layer)
    (r"ModuleNotFoundError:\s+No module named ['\"]?([\w\-\.]+)['\"]?", "DEPENDENCY"),
    (r"ImportError:\s+No module named ['\"]?([\w\-\.]+)['\"]?", "DEPENDENCY"),
    (r"ImportError:\s+cannot import name ['\"]?(\w+)['\"]? from", "IMPORT"),
    (r"ModuleNotFoundError:\s+([\w\-\.]+)", "DEPENDENCY"),
    (r"([\w\-]+) is not installed", "DEPENDENCY"),
    (r"pip install (\S+)", "DEPENDENCY"),
    (r"Could not find a version that satisfies the requirement (\S+)", "DEPENDENCY"),
    (r"No matching distribution found for (\S+)", "DEPENDENCY"),
    
    # LINTING
    (r"flake8.*F401", "LINTING"),
    (r"flake8.*F\d{3}", "LINTING"),
    (r"E\d{3}:", "LINTING"),
    (r"W\d{3}:", "LINTING"),
    (r"unused import", "LINTING"),
    (r"undefined name", "LINTING"),
    
    # TYPE_ERROR
    (r"TypeError:", "TYPE_ERROR"),
    (r"ValidationError", "TYPE_ERROR"),
    (r"expected.*got", "TYPE_ERROR"),
    (r"type.*incompatible", "TYPE_ERROR"),
    
    # LOGIC
    (r"AssertionError", "TEST_LOGIC"),
    (r"assert.*failed", "TEST_LOGIC"),
    (r"ValueError:", "LOGIC"),
    (r"KeyError:", "LOGIC"),
    (r"AttributeError:", "TYPE_ERROR"),
    (r"NameError:", "SYNTAX"),
    
    # SYNTAX
    (r"SyntaxError:", "SYNTAX"),
    (r"IndentationError:", "INDENTATION"),
    (r"invalid syntax", "SYNTAX"),
]

def extract_package_from_dependency_error(error_text):
    """
    Parse ImportError/ModuleNotFoundError to extract package name
    Examples:
    - "ModuleNotFoundError: No module named 'email_validator'" -> email_validator
    - "ImportError: email-validator is not installed" -> email-validator
    - "No module named 'pydantic'" -> pydantic
    """
    error_lower = error_text.lower()
    package = None
    
    # Pattern: No module named 'package_name'
    match = re.search(r"No module named ['\"]?([\w\-\.]+)['\"]?", error_text, re.IGNORECASE)
    if match:
        package = match.group(1)
    
    # Pattern: package-name is not installed
    if not package:
        match = re.search(r"([\w\-]+)\s+is not installed", error_text, re.IGNORECASE)
        if match:
            package = match.group(1)
    
    # Pattern: pip install package-name (from error suggestion)
    if not package:
        match = re.search(r"pip install ['\"]?([\w\-]+)['\"]?", error_text, re.IGNORECASE)
        if match:
            package = match.group(1)
    
    # Pattern: install "package[extra]" (e.g., pydantic[email])
    if not package:
        match = re.search(r'install ["\']?([\w\-\[\]]+)["\']?', error_text, re.IGNORECASE)
        if match:
            package = match.group(1)
    
    # Common package name mappings (error message -> pip package name)
    package_mappings = {
        'email_validator': 'email-validator',
        'email_validator': 'email-validator',
        'yaml': 'pyyaml',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'dateutil': 'python-dateutil',
    }
    
    if package and package in package_mappings:
        package = package_mappings[package]
    
    return package

def classify_failure(error_text, raw_error_type=None):
    """
    Classify failure into category for layered fix order
    Returns: (category, extracted_data)
    """
    if not error_text:
        return "LOGIC", {}
    
    error_text = str(error_text)
    extracted = {}
    
    # Check DEPENDENCY first (highest priority - environment layer)
    package = extract_package_from_dependency_error(error_text)
    if package:
        return "DEPENDENCY", {"package": package}
    
    # Check patterns
    for pattern, category in FAILURE_PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            if category == "DEPENDENCY" and not extracted:
                package = extract_package_from_dependency_error(error_text)
                if package:
                    extracted = {"package": package}
            return category, extracted
    
    # Fallback based on raw error type
    if raw_error_type:
        type_map = {
            "ModuleNotFoundError": "DEPENDENCY",
            "ImportError": "DEPENDENCY",
            "SyntaxError": "SYNTAX",
            "IndentationError": "INDENTATION",
            "TypeError": "TYPE_ERROR",
            "AssertionError": "TEST_LOGIC",
            "ValueError": "LOGIC",
            "KeyError": "LOGIC",
        }
        return type_map.get(raw_error_type, "LOGIC"), extracted
    
    return "LOGIC", extracted

def get_fix_priority(category):
    """
    Return fix order - dependency issues must be fixed first
    1 = highest priority
    """
    order = {
        "DEPENDENCY": 1,
        "IMPORT": 2,
        "LINTING": 3,
        "SYNTAX": 4,
        "INDENTATION": 5,
        "TYPE_ERROR": 6,
        "TEST_LOGIC": 7,
        "LOGIC": 8,
    }
    return order.get(category, 9)
