#!/usr/bin/env python3
"""
APEX v18 — False Positive Detection Engine
Detects SPA fallbacks, placeholder APIs, benign configurations
"""
import urllib.request
import urllib.error
import json
import re
from urllib.parse import urlparse

class FPDetector:
    """False Positive Detection for security scan findings"""
    
    SPA_PATTERNS = [
        '<!doctype html',
        '<html',
        '<head>',
        '<script type="module"',
        'angular.js',
        'react-dom',
        'next/static',
        '_next/',
        'vue.app',
    ]
    
    PLACEHOLDER_PATTERNS = [
        "a house is not a home",
        "v1 home",
        "hello world",
        "placeholder",
        "mock",
        "demo only",
        "test endpoint",
    ]
    
    GAME_CONTENT_PATTERNS = [
        "productType",
        "core.feeds",
        "agent.microsite",
        "game_config",
        "assetUrl",
        "storageKeyPrefix",
    ]
    
    def __init__(self):
        self.fp_log = []
    
    def detect_spa_fallback(self, url, content_type, body_preview):
        if content_type and 'text/html' in content_type.lower():
            for pattern in self.SPA_PATTERNS:
                if pattern in body_preview.lower():
                    return True, f"SPA fallback (Content-Type: {content_type})"
        return False, None
    
    def detect_placeholder_api(self, url, body):
        if not body:
            return False, None
        body_lower = body.lower()
        for pattern in self.PLACEHOLDER_PATTERNS:
            if pattern in body_lower:
                return True, f"Placeholder API: '{pattern}'"
        return False, None
    
    def detect_game_content(self, url, json_data):
        if not isinstance(json_data, dict):
            return False, None
        keys = list(json_data.keys())
        for pattern in self.GAME_CONTENT_PATTERNS:
            for k in keys:
                if pattern.lower() in k.lower():
                    return True, f"Game config: {k}"
        return False, None
    
    def detect_real_secret(self, url, body):
        """Check if content looks like REAL secrets (not game data)"""
        if not body:
            return False, None
        body_lower = body.lower()
        
        # Real secret patterns
        secret_patterns = [
            ('password', r'password\s*[:=]\s*["\']?[a-z0-9!@#$%^&*]{8,}'),
            ('api_key', r'api[_-]?key\s*[:=]\s*["\']?[a-z0-9]{20,}'),
            ('secret', r'secret\s*[:=]\s*["\']?[a-z0-9]{16,}'),
            ('database_url', r'database[_-]?url\s*[:=]\s*["\']?[a-z0-9:/]+'),
            ('aws_access', r'aws[_-]?access[_-]?key\s*[:=]\s*["\']?[A-Z0-9]{20}'),
            ('jwt_secret', r'jwt[_-]?secret\s*[:=]\s*["\']?[a-z0-9]{16,}'),
            ('private_key', r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'),
        ]
        
        for name, pattern in secret_patterns:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return True, f"Real secret detected: {name}"
        
        return False, None
    
    def verify_subdomain_risk(self, domain, content_type, body_preview):
        """Assess if subdomain exposure is actually risky"""
        risk = "LOW"
        reasons = []
        
        # Check if it redirects to main site
        if 'splinterlands.com' in domain and domain != 'splinterlands.com':
            if 'redirect' in body_preview.lower() or 'canonical' in body_preview.lower():
                return "BENIGN", "Redirects to main site"
        
        # Check for staging/dev indicators
        if any(s in domain for s in ['staging', 'dev', 'test']):
            reasons.append("Staging/dev environment")
            # Check for API keys in env files
            if '__env.js' in body_preview or 'window.__' in body_preview:
                # Check if env is empty
                if '{};' in body_preview or '={};' in body_preview:
                    return "LOW", f"Empty env config ({', '.join(reasons)})"
        
        # Check content type
        if content_type and 'text/html' in content_type.lower():
            reasons.append("HTML response (web app)")
        
        return risk, "; ".join(reasons) if reasons else "Standard web app"
    
    def calculate_confidence(self, finding_type, evidence, fp_check_result):
        """Calculate confidence score for a finding"""
        base_confidence = 80
        
        if fp_check_result:
            base_confidence -= 50  # Likely false positive
        
        # Adjust based on finding type
        if finding_type in ['CORS_WILDCARD_CREDENTIALS']:
            base_confidence += 10  # High confidence when confirmed
        elif finding_type in ['MISSING_SECURITY_HEADER']:
            base_confidence -= 15  # Lower confidence (common false positive)
        elif finding_type in ['EXPOSED_FILE']:
            base_confidence -= 30  # Often SPA fallback
        
        return max(10, min(100, base_confidence))
    
    def analyze_finding(self, finding, resp_headers=None, resp_body=""):
        """Full false positive analysis for a finding"""
        url = finding.get('url', finding.get('endpoint', ''))
        finding_type = finding.get('type', '')
        
        result = {
            'is_fp': False,
            'fp_reason': None,
            'confidence': 80,
            'adjusted_severity': finding.get('severity', 'MEDIUM'),
            'notes': []
        }
        
        # 1. Check for SPA fallback
        content_type = resp_headers.get('content-type', '') if resp_headers else ''
        is_fp, reason = self.detect_spa_fallback(url, content_type, resp_body)
        if is_fp:
            result['is_fp'] = True
            result['fp_reason'] = reason
            result['adjusted_severity'] = 'INFO'
            result['confidence'] = 15
            result['notes'].append('SPA fallback - not a real vulnerability')
            return result
        
        # 2. Check for placeholder API
        is_fp, reason = self.detect_placeholder_api(url, resp_body)
        if is_fp:
            result['is_fp'] = True
            result['fp_reason'] = reason
            result['adjusted_severity'] = 'INFO'
            result['confidence'] = 20
            result['notes'].append('Placeholder API - no real data exposed')
            return result
        
        # 3. Check for game content
        try:
            json_data = json.loads(resp_body) if resp_body.startswith('{') else None
            if json_data:
                is_game, reason = self.detect_game_content(url, json_data)
                if is_game:
                    result['notes'].append(f"Likely game config: {reason}")
                    result['is_fp'] = True
                    result['fp_reason'] = reason
                    result['adjusted_severity'] = 'INFO'
                    result['confidence'] = 25
                    return result
        except:
            pass
        
        # 4. Check for real secrets
        is_real_secret, reason = self.detect_real_secret(url, resp_body)
        if is_real_secret:
            result['confidence'] = 95
            result['adjusted_severity'] = 'CRITICAL'
            result['notes'].append(f'Real secret confirmed: {reason}')
        
        # 5. Calculate confidence
        result['confidence'] = self.calculate_confidence(finding_type, resp_body, result['is_fp'])
        
        return result
