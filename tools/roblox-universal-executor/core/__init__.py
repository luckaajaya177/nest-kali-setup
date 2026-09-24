"""
NestExecutor Core Package
"""
from .NestCore import (
    NestCore,
    NestCoreClient,
    WindowsExecutor,
    macOSExecutor,
    AndroidExecutor,
    iOSExecutor,
    ExecutorFactory,
    Script,
    ExecutionResult,
    ProcessInfo,
    PlatformConfig,
    VERSION,
    EXECUTOR_NAME,
)

__version__ = VERSION
__all__ = [
    "NestCore",
    "NestCoreClient",
    "WindowsExecutor",
    "macOSExecutor",
    "AndroidExecutor",
    "iOSExecutor",
    "ExecutorFactory",
    "Script",
    "ExecutionResult",
    "ProcessInfo",
    "PlatformConfig",
    "VERSION",
    "EXECUTOR_NAME",
]
