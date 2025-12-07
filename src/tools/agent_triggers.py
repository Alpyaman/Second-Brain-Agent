"""
Cross-Agent Trigger System

This module implements the "nervous system" for the Second Brain Agent,
allowing agents to automatically invoke each other based on detected events
and patterns.

Example:
    Chief of Staff sees "Project Kickoff" on calendar
    → Automatically triggers Architect to generate project template
    → Template is ready before the meeting starts
"""

import asyncio  # noqa: F401
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Available agent types for triggering."""
    ARCHITECT = "architect"
    DEV_TEAM = "dev_team"
    CURATOR = "curator"
    CHIEF_OF_STAFF = "chief_of_staff"


class TriggerReason(str, Enum):
    """Reasons for triggering an agent."""
    CALENDAR_EVENT = "calendar_event"
    EMAIL_RECEIVED = "email_received"
    KNOWLEDGE_GAP = "knowledge_gap"
    DEADLINE_APPROACHING = "deadline_approaching"
    PATTERN_DETECTED = "pattern_detected"
    MANUAL = "manual"


@dataclass
class TriggerContext:
    """Context information for a triggered agent action."""
    
    trigger_reason: TriggerReason
    source_agent: AgentType
    target_agent: AgentType
    event_details: Dict[str, Any]
    trigger_time: str
    priority: Literal["low", "medium", "high", "urgent"]
    auto_execute: bool = False  # Whether to execute immediately or queue for approval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerContext':
        """Create from dictionary."""
        return cls(
            trigger_reason=TriggerReason(data['trigger_reason']),
            source_agent=AgentType(data['source_agent']),
            target_agent=AgentType(data['target_agent']),
            event_details=data['event_details'],
            trigger_time=data['trigger_time'],
            priority=data['priority'],
            auto_execute=data.get('auto_execute', False)
        )


@dataclass
class TriggerResult:
    """Result of a triggered agent action."""
    
    success: bool
    agent: AgentType
    trigger_context: TriggerContext
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'success': self.success,
            'agent': self.agent.value,
            'trigger_context': self.trigger_context.to_dict(),
            'execution_time_ms': self.execution_time_ms
        }
        if self.output:
            result['output'] = self.output
        if self.error:
            result['error'] = self.error
        return result


class AgentTriggerSystem:
    """
    Central system for managing cross-agent triggers.
    
    This acts as the "nervous system" connecting all agents, allowing them
    to automatically respond to events and patterns detected by other agents.
    """
    
    def __init__(self, output_dir: str = "output/triggers"):
        """
        Initialize the trigger system.
        
        Args:
            output_dir: Directory for storing trigger logs and queued actions
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.trigger_history_file = self.output_dir / "trigger_history.jsonl"
        self.queued_triggers_file = self.output_dir / "queued_triggers.json"
        
        logger.info(f"AgentTriggerSystem initialized with output_dir: {self.output_dir}")
    
    def detect_triggers_from_calendar_event(
        self, 
        event_title: str, 
        event_description: str = "",
        event_start: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> List[TriggerContext]:
        """
        Analyze a calendar event to detect if it should trigger other agents.
        
        Patterns that trigger actions:
        - "Kickoff", "Planning", "Design Review" → Architect
        - "Code Review", "Sprint Planning" → Dev Team
        - "Research", "Knowledge Gap" → Curator
        
        Args:
            event_title: Title of the calendar event
            event_description: Description/notes for the event
            event_start: ISO format datetime of event start
            attendees: List of attendee emails
        
        Returns:
            List of trigger contexts for detected patterns
        """
        triggers = []
        combined_text = f"{event_title} {event_description}".lower()
        
        # Pattern: Project kickoff/planning → Architect should prepare template
        kickoff_keywords = [
            'kickoff', 'kick-off', 'planning meeting', 'project planning',
            'design session', 'architecture review', 'design review',
            'initial meeting', 'scoping', 'requirements gathering'
        ]
        
        if any(keyword in combined_text for keyword in kickoff_keywords):
            triggers.append(TriggerContext(
                trigger_reason=TriggerReason.CALENDAR_EVENT,
                source_agent=AgentType.CHIEF_OF_STAFF,
                target_agent=AgentType.ARCHITECT,
                event_details={
                    'event_title': event_title,
                    'event_description': event_description,
                    'event_start': event_start,
                    'attendees': attendees,
                    'action': 'generate_project_template',
                    'suggestion': f'Generate project template for: {event_title}'
                },
                trigger_time=datetime.now().isoformat(),
                priority='high',
                auto_execute=False  # Require approval for architecture generation
            ))
        
        # Pattern: Sprint planning/code review → Dev Team should prepare
        sprint_keywords = [
            'sprint planning', 'sprint review', 'code review',
            'technical review', 'implementation', 'development meeting'
        ]
        
        if any(keyword in combined_text for keyword in sprint_keywords):
            triggers.append(TriggerContext(
                trigger_reason=TriggerReason.CALENDAR_EVENT,
                source_agent=AgentType.CHIEF_OF_STAFF,
                target_agent=AgentType.DEV_TEAM,
                event_details={
                    'event_title': event_title,
                    'event_description': event_description,
                    'event_start': event_start,
                    'attendees': attendees,
                    'action': 'prepare_code_review',
                    'suggestion': 'Gather recent changes and prepare review materials'
                },
                trigger_time=datetime.now().isoformat(),
                priority='medium',
                auto_execute=False
            ))
        
        # Pattern: Research/learning topics → Curator should ingest resources
        research_keywords = [
            'research', 'learn', 'study', 'training', 'workshop',
            'knowledge sharing', 'tech talk', 'presentation prep'
        ]
        
        if any(keyword in combined_text for keyword in research_keywords):
            triggers.append(TriggerContext(
                trigger_reason=TriggerReason.CALENDAR_EVENT,
                source_agent=AgentType.CHIEF_OF_STAFF,
                target_agent=AgentType.CURATOR,
                event_details={
                    'event_title': event_title,
                    'event_description': event_description,
                    'event_start': event_start,
                    'action': 'discover_resources',
                    'suggestion': f'Find and ingest resources related to: {event_title}'
                },
                trigger_time=datetime.now().isoformat(),
                priority='low',
                auto_execute=True  # Curator can auto-execute discovery
            ))
        
        # Pattern: Client meeting → Prepare relevant context
        client_keywords = [
            'client meeting', 'customer call', 'demo', 'presentation',
            'stakeholder', 'pitch', 'proposal'
        ]
        
        if any(keyword in combined_text for keyword in client_keywords):
            triggers.append(TriggerContext(
                trigger_reason=TriggerReason.CALENDAR_EVENT,
                source_agent=AgentType.CHIEF_OF_STAFF,
                target_agent=AgentType.CHIEF_OF_STAFF,
                event_details={
                    'event_title': event_title,
                    'event_description': event_description,
                    'event_start': event_start,
                    'attendees': attendees,
                    'action': 'prepare_meeting_brief',
                    'suggestion': 'Compile relevant notes and prepare talking points'
                },
                trigger_time=datetime.now().isoformat(),
                priority='high',
                auto_execute=True  # Chief can auto-prepare briefs
            ))
        
        if triggers:
            logger.info(f"Detected {len(triggers)} triggers from event: {event_title}")
            for trigger in triggers:
                logger.debug(f"  → {trigger.target_agent.value}: {trigger.event_details.get('action')}")
        
        return triggers
    
    def queue_trigger(self, trigger: TriggerContext) -> None:
        """
        Queue a trigger for later execution or approval.
        
        Args:
            trigger: Trigger context to queue
        """
        # Load existing queue
        queued = []
        if self.queued_triggers_file.exists():
            try:
                with open(self.queued_triggers_file, 'r') as f:
                    queued = json.load(f)
            except Exception as e:
                logger.error(f"Error loading queued triggers: {e}")
        
        # Add new trigger
        queued.append(trigger.to_dict())
        
        # Save queue
        try:
            with open(self.queued_triggers_file, 'w') as f:
                json.dump(queued, f, indent=2)
            logger.info(f"Queued trigger: {trigger.target_agent.value} from {trigger.source_agent.value}")
        except Exception as e:
            logger.error(f"Error saving queued trigger: {e}")
    
    def get_queued_triggers(
        self, 
        agent: Optional[AgentType] = None,
        priority: Optional[str] = None
    ) -> List[TriggerContext]:
        """
        Get queued triggers, optionally filtered by agent or priority.
        
        Args:
            agent: Filter by target agent
            priority: Filter by priority level
        
        Returns:
            List of queued trigger contexts
        """
        if not self.queued_triggers_file.exists():
            return []
        
        try:
            with open(self.queued_triggers_file, 'r') as f:
                queued = json.load(f)
            
            triggers = [TriggerContext.from_dict(t) for t in queued]
            
            # Apply filters
            if agent:
                triggers = [t for t in triggers if t.target_agent == agent]
            if priority:
                triggers = [t for t in triggers if t.priority == priority]
            
            return triggers
        except Exception as e:
            logger.error(f"Error loading queued triggers: {e}")
            return []
    
    def clear_trigger(self, trigger: TriggerContext) -> None:
        """
        Remove a trigger from the queue after execution.
        
        Args:
            trigger: Trigger to remove
        """
        if not self.queued_triggers_file.exists():
            return
        
        try:
            with open(self.queued_triggers_file, 'r') as f:
                queued = json.load(f)
            
            # Remove matching trigger
            trigger_dict = trigger.to_dict()
            queued = [t for t in queued if t != trigger_dict]
            
            # Save updated queue
            with open(self.queued_triggers_file, 'w') as f:
                json.dump(queued, f, indent=2)
            
            logger.info(f"Cleared trigger: {trigger.target_agent.value}")
        except Exception as e:
            logger.error(f"Error clearing trigger: {e}")
    
    def log_trigger_result(self, result: TriggerResult) -> None:
        """
        Log the result of a trigger execution to history.
        
        Args:
            result: Result of trigger execution
        """
        try:
            with open(self.trigger_history_file, 'a') as f:
                f.write(json.dumps(result.to_dict()) + '\n')
            logger.info(f"Logged trigger result: {result.agent.value} (success={result.success})")
        except Exception as e:
            logger.error(f"Error logging trigger result: {e}")
    
    async def execute_architect_trigger(
        self, 
        trigger: TriggerContext
    ) -> TriggerResult:
        """
        Execute an Architect agent trigger.
        
        Args:
            trigger: Trigger context with event details
        
        Returns:
            Result of the trigger execution
        """
        start_time = datetime.now()
        
        try:
            from src.agents.architect.graph import create_agent_graph
            
            event_title = trigger.event_details.get('event_title', '')
            event_description = trigger.event_details.get('event_description', '')
            
            # Create a project goal from the event
            goal = f"Project from meeting: {event_title}"
            if event_description:
                goal += f"\n\nDetails: {event_description}"
            
            logger.info(f"Triggering Architect for: {event_title}")
            
            # Create architect agent
            architect = create_agent_graph()
            
            # Initial state for architecture generation
            initial_state = {
                "goal": goal,
                "is_job_description": False,
                "required_features": [],
                "project_type": "unknown",
                "relevant_code": "",
                "user_preferences": "",
                "design_document": "",
                "feedback": "",
                "iteration_count": 0,
                "max_iterations": 1,  # Single pass for auto-triggered
                "messages": []
            }
            
            # Run architect
            final_state = architect.invoke(initial_state)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract the generated TDD
            tdd = final_state.get("design_document", "")
            
            # Save TDD to docs/
            docs_dir = Path("docs")
            docs_dir.mkdir(exist_ok=True)
            
            # Create filename from event title
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in event_title)
            safe_title = safe_title.replace(' ', '_').lower()
            tdd_file = docs_dir / f"tdd_{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
            
            tdd_file.write_text(tdd)
            
            logger.info(f"✅ Architect completed in {execution_time:.0f}ms")
            logger.info(f"   TDD saved to: {tdd_file}")
            
            return TriggerResult(
                success=True,
                agent=AgentType.ARCHITECT,
                trigger_context=trigger,
                output={
                    'tdd': tdd,
                    'tdd_file': str(tdd_file),
                    'project_type': final_state.get('project_type', 'unknown')
                },
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"❌ Architect trigger failed: {e}")
            
            return TriggerResult(
                success=False,
                agent=AgentType.ARCHITECT,
                trigger_context=trigger,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def execute_trigger(self, trigger: TriggerContext) -> TriggerResult:
        """
        Execute a trigger by invoking the appropriate agent.
        
        Args:
            trigger: Trigger context to execute
        
        Returns:
            Result of the trigger execution
        """
        logger.info(f"Executing trigger: {trigger.target_agent.value} (priority: {trigger.priority})")
        
        if trigger.target_agent == AgentType.ARCHITECT:
            result = await self.execute_architect_trigger(trigger)
        elif trigger.target_agent == AgentType.DEV_TEAM:
            # TODO: Implement dev_team trigger
            result = TriggerResult(
                success=False,
                agent=AgentType.DEV_TEAM,
                trigger_context=trigger,
                error="Dev Team triggers not yet implemented"
            )
        elif trigger.target_agent == AgentType.CURATOR:
            # TODO: Implement curator trigger
            result = TriggerResult(
                success=False,
                agent=AgentType.CURATOR,
                trigger_context=trigger,
                error="Curator triggers not yet implemented"
            )
        else:
            result = TriggerResult(
                success=False,
                agent=trigger.target_agent,
                trigger_context=trigger,
                error=f"Trigger execution not implemented for {trigger.target_agent.value}"
            )
        
        # Log result to history
        self.log_trigger_result(result)
        
        # Clear from queue if it was queued
        self.clear_trigger(trigger)
        
        return result


# Singleton instance
_trigger_system: Optional[AgentTriggerSystem] = None


def get_trigger_system() -> AgentTriggerSystem:
    """Get or create the global trigger system instance."""
    global _trigger_system
    if _trigger_system is None:
        _trigger_system = AgentTriggerSystem()
    return _trigger_system


# Convenience functions for use in agent workflows

def detect_calendar_triggers(
    event_title: str,
    event_description: str = "",
    event_start: Optional[str] = None,
    attendees: Optional[List[str]] = None
) -> List[TriggerContext]:
    """
    Detect triggers from a calendar event.
    
    Convenience wrapper around AgentTriggerSystem.detect_triggers_from_calendar_event
    """
    system = get_trigger_system()
    return system.detect_triggers_from_calendar_event(
        event_title, event_description, event_start, attendees
    )


def queue_trigger(trigger: TriggerContext) -> None:
    """Queue a trigger for later execution."""
    system = get_trigger_system()
    system.queue_trigger(trigger)


def get_queued_triggers(
    agent: Optional[AgentType] = None,
    priority: Optional[str] = None
) -> List[TriggerContext]:
    """Get queued triggers, optionally filtered."""
    system = get_trigger_system()
    return system.get_queued_triggers(agent, priority)


async def execute_trigger(trigger: TriggerContext) -> TriggerResult:
    """Execute a trigger."""
    system = get_trigger_system()
    return await system.execute_trigger(trigger)
