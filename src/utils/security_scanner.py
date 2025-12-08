"""
Security Scanner for Generated Code

Scans generated code for common security vulnerabilities and issues:
- Hardcoded credentials and secrets
- SQL injection vulnerabilities
- XSS vulnerabilities  
- Insecure dependencies
- Security misconfigurations
- OWASP Top 10 issues

Author: Second Brain Agent Team
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Severity(str, Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability or issue"""
    severity: Severity
    category: str
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['severity'] = self.severity.value
        return data


class SecurityScanner:
    """
    Comprehensive security scanner for generated code.
    
    Features:
    - Static code analysis
    - Secret detection
    - Dependency vulnerability checking
    - SQL injection detection
    - XSS detection
    - Security misconfiguration detection
    """
    
    # Patterns for detecting hardcoded secrets
    SECRET_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
        'password': r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']',
        'secret_key': r'(?i)(secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
        'private_key': r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
        'aws_key': r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)["\']?\s*[:=]\s*["\']([A-Z0-9]{20,})["\']',
        'github_token': r'(?i)gh[p|s|o|u|r]_[a-zA-Z0-9]{36,}',
        'jwt_token': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        'connection_string': r'(?i)(mongodb|postgres|mysql|redis):\/\/[^:]+:[^@]+@',
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'execute\([^)]*\+[^)]*\)',  # String concatenation in execute
        r'\.raw\([^)]*\+[^)]*\)',  # String concatenation in raw queries
        r'f"(SELECT|INSERT|UPDATE|DELETE)[^"]*\{[^}]+\}',  # F-string with SQL
        r'"(SELECT|INSERT|UPDATE|DELETE)[^"]*"\s*\+',  # String concatenation with SQL
    ]
    
    # XSS patterns (for web applications)
    XSS_PATTERNS = [
        r'innerHTML\s*=\s*[^;]+\+',  # innerHTML with concatenation
        r'dangerouslySetInnerHTML',  # React dangerous HTML
        r'\.html\([^)]*\+[^)]*\)',  # jQuery .html() with concatenation
        r'document\.write\([^)]*\+',  # document.write with concatenation
    ]
    
    # Insecure configurations
    INSECURE_CONFIG_PATTERNS = {
        'debug_mode': r'(?i)DEBUG\s*=\s*True',
        'ssl_verification': r'(?i)verify\s*=\s*False',
        'allow_all_origins': r'(?i)allow_origins\s*=\s*\[["\']\*["\']\]',
        'weak_password': r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\'](?:admin|password|123456|test)["\']',
    }
    
    def __init__(self):
        """Initialize security scanner"""
        self.issues: List[SecurityIssue] = []
        self.stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
    
    def scan_directory(self, directory: Path, file_extensions: Optional[Set[str]] = None) -> List[SecurityIssue]:
        """
        Scan all code files in a directory.
        
        Args:
            directory: Path to scan
            file_extensions: Set of file extensions to scan (e.g., {'.py', '.js', '.ts'})
                           If None, scans common code extensions
        
        Returns:
            List of security issues found
        """
        if file_extensions is None:
            file_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs'}
        
        self.issues = []
        self.stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        # Convert to Path if string
        if isinstance(directory, str):
            directory = Path(directory)
        
        logger.info(f"Starting security scan of {directory}")
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in file_extensions:
                self.scan_file(file_path)
        
        self.stats['issues_found'] = len(self.issues)
        logger.info(f"Security scan complete. Found {len(self.issues)} issues in {self.stats['files_scanned']} files")
        
        return self.issues
    
    def scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """
        Scan a single file for security issues.
        
        Args:
            file_path: Path to file
        
        Returns:
            List of security issues found in this file
        """
        self.stats['files_scanned'] += 1
        file_issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Scan for hardcoded secrets
            file_issues.extend(self._scan_secrets(file_path, content, lines))
            
            # Scan for SQL injection vulnerabilities
            file_issues.extend(self._scan_sql_injection(file_path, content, lines))
            
            # Scan for XSS vulnerabilities
            if file_path.suffix in {'.js', '.jsx', '.ts', '.tsx', '.html'}:
                file_issues.extend(self._scan_xss(file_path, content, lines))
            
            # Scan for insecure configurations
            file_issues.extend(self._scan_insecure_config(file_path, content, lines))
            
            # Update stats
            for issue in file_issues:
                self.stats[issue.severity.value] += 1
            
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
        
        return file_issues
    
    def _scan_secrets(self, file_path: Path, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Scan for hardcoded secrets and credentials."""
        issues = []
        
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                issue = SecurityIssue(
                    severity=Severity.CRITICAL,
                    category="Hardcoded Secrets",
                    title=f"Hardcoded {secret_type.replace('_', ' ').title()} Detected",
                    description=f"Found what appears to be a hardcoded {secret_type} in the code",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else None,
                    recommendation="Use environment variables or secure vault solutions like AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault",
                    cwe_id="CWE-798"
                )
                issues.append(issue)
                self.issues.append(issue)
        
        return issues
    
    def _scan_sql_injection(self, file_path: Path, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Scan for potential SQL injection vulnerabilities."""
        issues = []
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                
                issue = SecurityIssue(
                    severity=Severity.HIGH,
                    category="SQL Injection",
                    title="Potential SQL Injection Vulnerability",
                    description="SQL query appears to use string concatenation which may be vulnerable to SQL injection",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else None,
                    recommendation="Use parameterized queries or ORM methods instead of string concatenation",
                    cwe_id="CWE-89"
                )
                issues.append(issue)
                self.issues.append(issue)
        
        return issues
    
    def _scan_xss(self, file_path: Path, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Scan for potential XSS vulnerabilities."""
        issues = []
        
        for pattern in self.XSS_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                issue = SecurityIssue(
                    severity=Severity.HIGH,
                    category="Cross-Site Scripting (XSS)",
                    title="Potential XSS Vulnerability",
                    description="Code may be vulnerable to XSS attacks due to unsafe HTML manipulation",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else None,
                    recommendation="Use safe DOM manipulation methods, sanitize user input, and implement Content Security Policy (CSP)",
                    cwe_id="CWE-79"
                )
                issues.append(issue)
                self.issues.append(issue)
        
        return issues
    
    def _scan_insecure_config(self, file_path: Path, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Scan for insecure configurations."""
        issues = []
        
        for config_type, pattern in self.INSECURE_CONFIG_PATTERNS.items():
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                severity = Severity.HIGH if config_type in ['debug_mode', 'ssl_verification'] else Severity.MEDIUM
                
                issue = SecurityIssue(
                    severity=severity,
                    category="Insecure Configuration",
                    title=f"Insecure Configuration: {config_type.replace('_', ' ').title()}",
                    description=f"Found insecure {config_type} configuration",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else None,
                    recommendation=self._get_config_recommendation(config_type),
                    cwe_id="CWE-16"
                )
                issues.append(issue)
                self.issues.append(issue)
        
        return issues
    
    def _get_config_recommendation(self, config_type: str) -> str:
        """Get recommendation for specific configuration issue."""
        recommendations = {
            'debug_mode': "Set DEBUG=False in production environments",
            'ssl_verification': "Enable SSL verification to prevent man-in-the-middle attacks",
            'allow_all_origins': "Restrict CORS to specific trusted origins instead of allowing all (*)",
            'weak_password': "Use strong, randomly generated passwords and store them securely"
        }
        return recommendations.get(config_type, "Follow security best practices")
    
    def scan_dependencies(self, requirements_file: Path) -> List[SecurityIssue]:
        """
        Scan Python dependencies for known vulnerabilities using safety.
        
        Args:
            requirements_file: Path to requirements.txt
        
        Returns:
            List of security issues in dependencies
        """
        issues = []
        
        try:
            # Try to run safety check
            result = subprocess.run(
                ['safety', 'check', '--file', str(requirements_file), '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse safety output
                import json
                vulnerabilities = json.loads(result.stdout)
                
                for vuln in vulnerabilities:
                    issue = SecurityIssue(
                        severity=Severity.HIGH,
                        category="Vulnerable Dependency",
                        title=f"Vulnerable Package: {vuln.get('package', 'unknown')}",
                        description=vuln.get('advisory', 'No description'),
                        file_path=str(requirements_file),
                        recommendation=f"Update to version {vuln.get('safe_version', 'latest')} or higher",
                        cwe_id="CWE-937"
                    )
                    issues.append(issue)
                    self.issues.append(issue)
            
        except FileNotFoundError:
            logger.warning("safety tool not found. Install with: pip install safety")
        except subprocess.TimeoutExpired:
            logger.error("Dependency scan timed out")
        except Exception as e:
            logger.error(f"Error scanning dependencies: {e}")
        
        return issues
    
    def generate_report(self, format: str = "text") -> str:
        """
        Generate security scan report.
        
        Args:
            format: Report format ('text' or 'json')
        
        Returns:
            Formatted report string
        """
        if format == "json":
            import json
            return json.dumps({
                'stats': self.stats,
                'issues': [issue.to_dict() for issue in self.issues]
            }, indent=2)
        
        # Text format
        report = []
        report.append("\n" + "=" * 70)
        report.append("SECURITY SCAN REPORT")
        report.append("=" * 70)
        
        report.append(f"\nFiles Scanned: {self.stats['files_scanned']}")
        report.append(f"Issues Found:  {self.stats['issues_found']}\n")
        
        report.append("By Severity:")
        report.append(f"  🔴 Critical: {self.stats['critical']}")
        report.append(f"  🟠 High:     {self.stats['high']}")
        report.append(f"  🟡 Medium:   {self.stats['medium']}")
        report.append(f"  🟢 Low:      {self.stats['low']}")
        report.append(f"  ℹ️  Info:     {self.stats['info']}")
        
        if self.issues:
            report.append("\n" + "-" * 70)
            report.append("ISSUES DETAIL")
            report.append("-" * 70)
            
            # Group by severity
            for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if severity_issues:
                    report.append(f"\n{severity.value.upper()} Issues ({len(severity_issues)}):")
                    for idx, issue in enumerate(severity_issues, 1):
                        report.append(f"\n  [{idx}] {issue.title}")
                        report.append(f"      File: {issue.file_path}:{issue.line_number or '?'}")
                        report.append(f"      {issue.description}")
                        if issue.code_snippet:
                            report.append(f"      Code: {issue.code_snippet}")
                        if issue.recommendation:
                            report.append(f"      Fix:  {issue.recommendation}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics."""
        return {
            'files_scanned': self.stats['files_scanned'],
            'total_issues': self.stats['issues_found'],
            'critical': self.stats['critical'],
            'high': self.stats['high'],
            'medium': self.stats['medium'],
            'low': self.stats['low'],
            'passed': self.stats['critical'] == 0 and self.stats['high'] == 0
        }


if __name__ == '__main__':
    # Demo usage
    scanner = SecurityScanner()
    
    # Scan current project
    project_dir = Path(__file__).parent.parent.parent
    issues = scanner.scan_directory(project_dir / "src")
    
    # Print report
    print(scanner.generate_report())
    
    # Check dependencies if requirements.txt exists
    req_file = project_dir / "requirements.txt"
    if req_file.exists():
        print("\nScanning dependencies...")
        dep_issues = scanner.scan_dependencies(req_file)
        if dep_issues:
            print(f"Found {len(dep_issues)} vulnerable dependencies")
