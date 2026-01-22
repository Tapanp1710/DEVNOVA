"""
DEVNOVA - AI Developer Operating Environment

A research-grade AI-native development environment that provides
deterministic project understanding, persistent memory, and multi-agent
reasoning using an LLM as a reasoning layer only.
"""

__version__ = "0.1.0"
__author__ = "DEVNOVA Team"

# Core subsystems
from . import ingestion
from . import analysis
from . import memory
from . import state
from . import agents
from . import llm
from . import orchestrator
from . import ide

__all__ = [
    'ingestion',
    'analysis',
    'memory',
    'state',
    'agents',
    'llm',
    'orchestrator',
    'ide'
]