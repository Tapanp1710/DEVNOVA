# devnova/orchestrator/orchestrator.py
"""
Orchestrator

Assigns tasks to agents, validates outputs, rejects unsafe actions.
"""

import json
from typing import Dict, Any, List, Optional
from devnova.state.api import ProjectStateAPI
from devnova.llm.interface import LLMInterface, create_llm_interface
from devnova.agents.architect_agent import ArchitectAgent
from devnova.agents.feature_agent import FeatureAgent
from devnova.agents.debug_agent import DebugAgent
from devnova.agents.test_agent import TestAgent
from devnova.agents.docs_agent import DocsAgent


class TaskOrchestrator:
    """
    Orchestrates tasks across agents.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.state_api = ProjectStateAPI(project_path)
        self.llm_interface = create_llm_interface()
        
        # Initialize agents
        self.agents = {
            'architect': ArchitectAgent(self.project_path, self.llm_interface),
            'feature': FeatureAgent(self.project_path, self.llm_interface),
            'debug': DebugAgent(self.project_path, self.llm_interface),
            'test': TestAgent(self.project_path, self.llm_interface),
            'docs': DocsAgent(self.project_path, self.llm_interface),
        }

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task by routing to appropriate agent.
        """
        task_type = task.get('type', 'unknown')
        agent_name = self._determine_agent(task_type)
        
        if agent_name not in self.agents:
            return {
                'status': 'error',
                'error': f'No agent available for task type: {task_type}',
                'task': task
            }

        agent = self.agents[agent_name]
        
        # Validate task safety
        if not self._validate_task_safety(task):
            return {
                'status': 'rejected',
                'reason': 'Task failed safety validation',
                'task': task
            }

        # Execute task
        try:
            result = agent.process_task(task)
            
            # Validate result
            if not self._validate_result(result):
                return {
                    'status': 'error',
                    'error': 'Agent result validation failed',
                    'task': task,
                    'result': result
                }
            
            return {
                'status': 'success',
                'agent': agent_name,
                'task': task,
                'result': result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Agent execution failed: {str(e)}',
                'task': task
            }

    def _determine_agent(self, task_type: str) -> str:
        """
        Determine which agent should handle the task.
        """
        mapping = {
            'architecture_review': 'architect',
            'feature_planning': 'feature',
            'bug_analysis': 'debug',
            'test_coverage': 'test',
            'documentation': 'docs',
            'code_review': 'architect',  # Default to architect
        }
        return mapping.get(task_type, 'architect')  # Default fallback

    def _validate_task_safety(self, task: Dict[str, Any]) -> bool:
        """
        Validate that the task is safe to execute.
        Rejects tasks that could:
        - Modify files directly
        - Execute arbitrary code
        - Access sensitive data
        """
        description = task.get('description', '').lower()
        
        # Reject direct file modifications
        unsafe_keywords = [
            'write file', 'modify file', 'delete file', 'execute code',
            'run command', 'shell command', 'system call', 'eval',
            'access database', 'connect to', 'send email', 'http request'
        ]
        
        for keyword in unsafe_keywords:
            if keyword in description:
                return False
        
        # Only allow read-only operations
        allowed_operations = [
            'analyze', 'review', 'suggest', 'recommend', 'identify',
            'assess', 'evaluate', 'check', 'examine', 'inspect'
        ]
        
        has_allowed = any(op in description for op in allowed_operations)
        if not has_allowed:
            return False
            
        return True

    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate agent result structure and safety.
        """
        if 'result' not in result:
            return False
            
        agent_result = result['result']
        
        # Check for error responses
        if 'error' in agent_result:
            return True  # Errors are acceptable, just logged
            
        # Ensure structured output (should be dict from LLM)
        if not isinstance(agent_result, dict):
            return False
            
        # Check for dangerous suggestions
        dangerous_patterns = [
            'execute', 'run', 'delete', 'modify', 'write',
            'system', 'shell', 'command', 'eval'
        ]
        
        result_str = json.dumps(agent_result).lower()
        for pattern in dangerous_patterns:
            if f'"{pattern}"' in result_str or f"'{pattern}'" in result_str:
                return False
                
        return True

    def get_available_agents(self) -> List[str]:
        """
        Get list of available agents.
        """
        return list(self.agents.keys())

    def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific agent.
        """
        if agent_name not in self.agents:
            return {}
            
        # TODO: Define detailed capabilities per agent
        capabilities = {
            'architect': {
                'tasks': ['architecture_review', 'code_structure', 'design_patterns'],
                'outputs': ['analysis', 'recommendations', 'diagrams']
            },
            'feature': {
                'tasks': ['feature_planning', 'requirements_analysis', 'implementation_planning'],
                'outputs': ['feature_specs', 'implementation_plans', 'dependencies']
            },
            'debug': {
                'tasks': ['bug_identification', 'error_analysis', 'fix_suggestions'],
                'outputs': ['issue_reports', 'fix_recommendations', 'test_cases']
            },
            'test': {
                'tasks': ['test_coverage_analysis', 'test_case_generation', 'quality_assessment'],
                'outputs': ['test_plans', 'test_cases', 'coverage_reports']
            },
            'docs': {
                'tasks': ['documentation_review', 'doc_gap_analysis', 'doc_structure'],
                'outputs': ['doc_plans', 'doc_templates', 'readiness_assessments']
            }
        }
        
        return capabilities.get(agent_name, {})


# CLI interface for testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m devnova.orchestrator.orchestrator <project_path> <task_type> <task_description>")
        sys.exit(1)

    project_path = sys.argv[1]
    task_type = sys.argv[2]
    task_description = ' '.join(sys.argv[3:])

    orchestrator = TaskOrchestrator(project_path)
    
    task = {
        'type': task_type,
        'description': task_description
    }
    
    result = orchestrator.process_task(task)
    print(json.dumps(result, indent=2))