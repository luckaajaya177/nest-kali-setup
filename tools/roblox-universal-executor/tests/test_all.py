#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NestExecutor Test Suite
Tests all platform executors and core functionality
"""

import sys
import os
import json
import time

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Core'))

from NestCore import (
    ExecutorFactory,
    Script,
    ExecutionResult,
    VERSION,
    EXECUTOR_NAME,
)


def test_factory():
    """Test platform factory creation."""
    print("\n[TEST] Testing Factory...")
    
    platforms = ['windows', 'darwin', 'linux', 'android', 'ios']
    results = {}
    
    for p in platforms:
        try:
            executor = ExecutorFactory.create(p)
            results[p] = {
                'success': True,
                'type': executor.__class__.__name__,
                'platform': executor.platform_config.name,
                'arch': executor.platform_config.arch,
                'port': executor.port
            }
            print(f"  ✓ {p.upper()}: {executor.__class__.__name__}")
        except Exception as e:
            results[p] = {'success': False, 'error': str(e)}
            print(f"  ✗ {p.upper()}: {e}")
    
    return results


def test_script_management():
    """Test script loading and management."""
    print("\n[TEST] Testing Script Management...")
    
    executor = ExecutorFactory.create()
    
    # Create test scripts
    test_scripts = [
        ("Test1", "print('Hello World')", "test"),
        ("Test2", "local x = 1 + 1\nprint(x)", "math"),
        ("Test3", "game:GetService('Players')", "api"),
    ]
    
    results = []
    for name, content, category in test_scripts:
        script = executor.load_script(name, content, category)
        results.append({
            'name': script.name,
            'hash': script.hash,
            'size': script.size,
            'category': script.category
        })
        print(f"  ✓ Loaded: {name} ({script.hash[:8]})")
    
    # Test listing
    all_scripts = executor.list_scripts()
    print(f"  → Total scripts: {len(all_scripts)}")
    
    # Test filtering
    filtered = executor.list_scripts(category='test')
    print(f"  → Filtered 'test': {len(filtered)} scripts")
    
    return results


def test_execution_flow():
    """Test execution flow (without actual injection)."""
    print("\n[TEST] Testing Execution Flow...")
    
    executor = ExecutorFactory.create()
    
    # Load a script
    script = executor.load_script("ExecutionTest", "print('Test execution')", "test")
    
    # Execute (will return success but no real execution without injection)
    result = executor.execute_script(script)
    
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Time: {result.execution_time:.3f}s")
    
    return result


def test_core_client():
    """Test IPC client functionality."""
    print("\n[TEST] Testing Core Client...")
    
    # This would test the NestCoreClient class
    # For now, just verify it can be imported
    try:
        from NestCore import NestCoreClient
        print("  ✓ NestCoreClient importable")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_port_config():
    """Test port configuration."""
    print("\n[TEST] Testing Port Configuration...")
    
    # Default port
    executor = ExecutorFactory.create()
    print(f"  Default port: {executor.port}")
    
    # Custom port
    executor = ExecutorFactory.create(config={'port': 12345})
    print(f"  Custom port: {executor.port}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print(f"  {EXECUTOR_NAME} v{VERSION} - Test Suite")
    print("=" * 50)
    
    all_results = {
        'factory': test_factory(),
        'scripts': test_script_management(),
        'execution': test_execution_flow(),
        'client': test_core_client(),
        'config': test_port_config(),
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("  TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in all_results.items():
        if isinstance(result, dict):
            if result.get('success') or all(r.get('success') for r in result.values()):
                print(f"  ✓ {test_name}: PASSED")
                passed += 1
            else:
                print(f"  ✗ {test_name}: FAILED")
                failed += 1
        elif isinstance(result, bool):
            if result:
                print(f"  ✓ {test_name}: PASSED")
                passed += 1
            else:
                print(f"  ✗ {test_name}: FAILED")
                failed += 1
        elif isinstance(result, list):
            print(f"  ✓ {test_name}: {len(result)} items")
            passed += 1
    
    print(f"\n  Total: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
