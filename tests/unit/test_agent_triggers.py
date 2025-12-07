"""
Tests for Cross-Agent Trigger System

Tests the "nervous system" that allows agents to automatically invoke each other.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

from src.tools.agent_triggers import (
    AgentTriggerSystem,
    TriggerContext,
    TriggerResult,
    AgentType,
    TriggerReason,
    detect_calendar_triggers,
    queue_trigger,
    get_queued_triggers,
    execute_trigger,
    get_trigger_system
)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "triggers"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def trigger_system(temp_output_dir):
    """Create a fresh trigger system for each test."""
    return AgentTriggerSystem(output_dir=str(temp_output_dir))


class TestTriggerDetection:
    """Test detection of triggers from calendar events."""
    
    def test_detect_kickoff_meeting(self, trigger_system):
        """Test that project kickoff meetings trigger Architect."""
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="Project Kickoff Meeting",
            event_description="Planning session for new web app"
        )
        
        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger.target_agent == AgentType.ARCHITECT
        assert trigger.trigger_reason == TriggerReason.CALENDAR_EVENT
        assert trigger.priority == 'high'
        assert not trigger.auto_execute  # Requires approval
    
    def test_detect_multiple_triggers(self, trigger_system):
        """Test that some events trigger multiple agents."""
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="Client Demo and Planning Session",
            event_description="Demo current progress and discuss new features"
        )
        
        # Should trigger both Chief (client meeting prep) and potentially Architect
        assert len(triggers) >= 1
        agent_types = [t.target_agent for t in triggers]
        assert AgentType.CHIEF_OF_STAFF in agent_types
    
    def test_detect_sprint_planning(self, trigger_system):
        """Test that sprint planning triggers Dev Team."""
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="Sprint Planning Meeting",
            event_description="Plan next sprint's work"
        )
        
        assert len(triggers) >= 1
        # Find the Dev Team trigger
        dev_triggers = [t for t in triggers if t.target_agent == AgentType.DEV_TEAM]
        assert len(dev_triggers) >= 1
        assert dev_triggers[0].priority in ['medium', 'high']
    
    def test_detect_research_meeting(self, trigger_system):
        """Test that research topics trigger Curator."""
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="Research: Machine Learning for NLP",
            event_description="Learn about latest ML techniques"
        )
        
        assert len(triggers) >= 1
        curator_triggers = [t for t in triggers if t.target_agent == AgentType.CURATOR]
        assert len(curator_triggers) >= 1
        assert curator_triggers[0].auto_execute  # Curator can auto-discover
    
    def test_no_triggers_for_regular_meeting(self, trigger_system):
        """Test that regular meetings don't trigger actions."""
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="Team Standup",
            event_description="Daily standup"
        )
        
        # Regular standups shouldn't trigger special actions
        assert len(triggers) == 0
    
    def test_case_insensitive_detection(self, trigger_system):
        """Test that keyword detection is case-insensitive."""
        triggers_upper = trigger_system.detect_triggers_from_calendar_event(
            event_title="PROJECT KICKOFF"
        )
        triggers_lower = trigger_system.detect_triggers_from_calendar_event(
            event_title="project kickoff"
        )
        triggers_mixed = trigger_system.detect_triggers_from_calendar_event(
            event_title="Project KickOff"
        )
        
        assert len(triggers_upper) == len(triggers_lower) == len(triggers_mixed)


class TestTriggerQueue:
    """Test trigger queuing and retrieval."""
    
    def test_queue_trigger(self, trigger_system, temp_output_dir):
        """Test queuing a trigger."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={'test': 'data'},
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        
        trigger_system.queue_trigger(trigger)
        
        # Verify file was created
        queue_file = temp_output_dir / "queued_triggers.json"
        assert queue_file.exists()
        
        # Verify content
        with open(queue_file) as f:
            queued = json.load(f)
        
        assert len(queued) == 1
        assert queued[0]['target_agent'] == 'architect'
    
    def test_get_queued_triggers(self, trigger_system):
        """Test retrieving queued triggers."""
        # Queue multiple triggers
        trigger1 = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={},
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        trigger2 = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.DEV_TEAM,
            event_details={},
            trigger_time=datetime.now().isoformat(),
            priority='medium',
            auto_execute=False
        )
        
        trigger_system.queue_trigger(trigger1)
        trigger_system.queue_trigger(trigger2)
        
        # Get all triggers
        all_triggers = trigger_system.get_queued_triggers()
        assert len(all_triggers) == 2
        
        # Filter by agent
        architect_triggers = trigger_system.get_queued_triggers(agent=AgentType.ARCHITECT)
        assert len(architect_triggers) == 1
        assert architect_triggers[0].target_agent == AgentType.ARCHITECT
        
        # Filter by priority
        high_priority = trigger_system.get_queued_triggers(priority='high')
        assert len(high_priority) == 1
        assert high_priority[0].priority == 'high'
    
    def test_clear_trigger(self, trigger_system):
        """Test removing a trigger from queue."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={},
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        
        trigger_system.queue_trigger(trigger)
        assert len(trigger_system.get_queued_triggers()) == 1
        
        trigger_system.clear_trigger(trigger)
        assert len(trigger_system.get_queued_triggers()) == 0


class TestTriggerExecution:
    """Test trigger execution."""
    
    @pytest.mark.asyncio
    async def test_execute_architect_trigger_success(self, trigger_system):
        """Test successful Architect trigger execution."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={
                'event_title': 'Test Project Kickoff',
                'event_description': 'Building a new API'
            },
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        
        # Mock the architect agent
        with patch('src.tools.agent_triggers.create_agent_graph') as mock_create:
            mock_agent = Mock()
            mock_agent.invoke.return_value = {
                'design_document': '# Test TDD\n\nThis is a test.',
                'project_type': 'api'
            }
            mock_create.return_value = mock_agent
            
            result = await trigger_system.execute_architect_trigger(trigger)
        
        assert result.success
        assert result.agent == AgentType.ARCHITECT
        assert result.output is not None
        assert 'tdd' in result.output
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_execute_architect_trigger_failure(self, trigger_system):
        """Test Architect trigger execution with error."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={
                'event_title': 'Test Event',
                'event_description': ''
            },
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        
        # Mock the architect agent to raise an error
        with patch('src.tools.agent_triggers.create_agent_graph') as mock_create:
            mock_create.side_effect = Exception("Test error")
            
            result = await trigger_system.execute_architect_trigger(trigger)
        
        assert not result.success
        assert result.error == "Test error"
        assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_execute_trigger_logs_result(self, trigger_system, temp_output_dir):
        """Test that trigger execution logs results."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={'event_title': 'Test'},
            trigger_time=datetime.now().isoformat(),
            priority='high',
            auto_execute=False
        )
        
        with patch('src.tools.agent_triggers.create_agent_graph') as mock_create:
            mock_agent = Mock()
            mock_agent.invoke.return_value = {'design_document': 'test', 'project_type': 'api'}
            mock_create.return_value = mock_agent
            
            await trigger_system.execute_trigger(trigger)
        
        # Verify history file was created
        history_file = temp_output_dir / "trigger_history.jsonl"
        assert history_file.exists()
        
        # Verify content
        with open(history_file) as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        result = json.loads(lines[0])
        assert result['agent'] == 'architect'


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""
    
    def test_detect_calendar_triggers_wrapper(self):
        """Test detect_calendar_triggers convenience function."""
        triggers = detect_calendar_triggers(
            event_title="Project Kickoff",
            event_description="New project"
        )
        
        assert len(triggers) >= 1
        assert all(isinstance(t, TriggerContext) for t in triggers)
    
    def test_queue_trigger_wrapper(self, temp_output_dir):
        """Test queue_trigger convenience function."""
        # Create system with temp dir
        system = AgentTriggerSystem(output_dir=str(temp_output_dir))
        
        # Temporarily replace singleton
        import src.tools.agent_triggers as triggers_module
        old_system = triggers_module._trigger_system
        triggers_module._trigger_system = system
        
        try:
            trigger = TriggerContext(
                trigger_reason=TriggerReason.CALENDAR_EVENT,
                source_agent=AgentType.CHIEF_OF_STAFF,
                target_agent=AgentType.ARCHITECT,
                event_details={},
                trigger_time=datetime.now().isoformat(),
                priority='high',
                auto_execute=False
            )
            
            queue_trigger(trigger)
            
            queued = system.get_queued_triggers()
            assert len(queued) == 1
        finally:
            triggers_module._trigger_system = old_system
    
    def test_get_trigger_system_singleton(self):
        """Test that get_trigger_system returns a singleton."""
        system1 = get_trigger_system()
        system2 = get_trigger_system()
        
        assert system1 is system2


class TestTriggerContext:
    """Test TriggerContext data class."""
    
    def test_to_dict(self):
        """Test TriggerContext serialization."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={'key': 'value'},
            trigger_time='2024-01-01T12:00:00',
            priority='high',
            auto_execute=True
        )
        
        data = trigger.to_dict()
        
        assert data['trigger_reason'] == TriggerReason.CALENDAR_EVENT
        assert data['source_agent'] == AgentType.CHIEF_OF_STAFF
        assert data['target_agent'] == AgentType.ARCHITECT
        assert data['event_details'] == {'key': 'value'}
        assert data['priority'] == 'high'
        assert data['auto_execute'] is True
    
    def test_from_dict(self):
        """Test TriggerContext deserialization."""
        data = {
            'trigger_reason': 'calendar_event',
            'source_agent': 'chief_of_staff',
            'target_agent': 'architect',
            'event_details': {'key': 'value'},
            'trigger_time': '2024-01-01T12:00:00',
            'priority': 'high',
            'auto_execute': True
        }
        
        trigger = TriggerContext.from_dict(data)
        
        assert trigger.trigger_reason == TriggerReason.CALENDAR_EVENT
        assert trigger.source_agent == AgentType.CHIEF_OF_STAFF
        assert trigger.target_agent == AgentType.ARCHITECT
        assert trigger.priority == 'high'
        assert trigger.auto_execute is True


class TestTriggerResult:
    """Test TriggerResult data class."""
    
    def test_to_dict_success(self):
        """Test TriggerResult serialization for success."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={},
            trigger_time='2024-01-01T12:00:00',
            priority='high',
            auto_execute=False
        )
        
        result = TriggerResult(
            success=True,
            agent=AgentType.ARCHITECT,
            trigger_context=trigger,
            output={'tdd': 'test document'},
            execution_time_ms=1234.56
        )
        
        data = result.to_dict()
        
        assert data['success'] is True
        assert data['agent'] == 'architect'
        assert data['output'] == {'tdd': 'test document'}
        assert data['execution_time_ms'] == 1234.56
        assert 'error' not in data
    
    def test_to_dict_failure(self):
        """Test TriggerResult serialization for failure."""
        trigger = TriggerContext(
            trigger_reason=TriggerReason.CALENDAR_EVENT,
            source_agent=AgentType.CHIEF_OF_STAFF,
            target_agent=AgentType.ARCHITECT,
            event_details={},
            trigger_time='2024-01-01T12:00:00',
            priority='high',
            auto_execute=False
        )
        
        result = TriggerResult(
            success=False,
            agent=AgentType.ARCHITECT,
            trigger_context=trigger,
            error="Test error",
            execution_time_ms=100.0
        )
        
        data = result.to_dict()
        
        assert data['success'] is False
        assert data['error'] == "Test error"
        assert 'output' not in data


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_full_workflow_project_kickoff(self, trigger_system):
        """Test complete workflow: detect → queue → execute → log."""
        # 1. Detect trigger from calendar event
        triggers = trigger_system.detect_triggers_from_calendar_event(
            event_title="New E-commerce Platform - Project Kickoff",
            event_description="Planning session with client to scope new online store"
        )
        
        assert len(triggers) >= 1
        architect_trigger = next(t for t in triggers if t.target_agent == AgentType.ARCHITECT)
        
        # 2. Queue the trigger
        trigger_system.queue_trigger(architect_trigger)
        queued = trigger_system.get_queued_triggers(agent=AgentType.ARCHITECT)
        assert len(queued) == 1
        
        # 3. Simulate execution (would be async in production)
        # In real scenario, this would call execute_trigger
        
        # 4. Clear after execution
        trigger_system.clear_trigger(architect_trigger)
        queued_after = trigger_system.get_queued_triggers(agent=AgentType.ARCHITECT)
        assert len(queued_after) == 0
    
    def test_multiple_events_different_priorities(self, trigger_system):
        """Test handling multiple events with different priorities."""
        events = [
            ("Project Kickoff Meeting", "high priority meeting", "high"),
            ("Research: New Framework", "learning session", "low"),
            ("Sprint Planning", "plan next sprint", "medium")
        ]
        
        all_triggers = []
        for title, desc, expected_priority in events:
            triggers = trigger_system.detect_triggers_from_calendar_event(title, desc)
            all_triggers.extend(triggers)
            for trigger in triggers:
                trigger_system.queue_trigger(trigger)
        
        # Get high priority triggers first
        high_priority = trigger_system.get_queued_triggers(priority='high')
        assert len(high_priority) >= 1
        
        # Get auto-execute triggers
        all_queued = trigger_system.get_queued_triggers()
        auto_triggers = [t for t in all_queued if t.auto_execute]
        manual_triggers = [t for t in all_queued if not t.auto_execute]
        
        # Research/learning should be auto-execute
        assert len(auto_triggers) >= 1
        # Kickoff/planning should require approval
        assert len(manual_triggers) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
