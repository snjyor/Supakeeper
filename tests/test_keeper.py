"""Tests for SupaKeeper core functionality."""

from unittest.mock import MagicMock, patch

import pytest

from supakeeper.config import Config, ProjectConfig
from supakeeper.keeper import PingResult, SupaKeeper


class TestPingResult:
    """Tests for PingResult dataclass."""
    
    def test_success_result(self):
        """Test creating a successful ping result."""
        result = PingResult(
            project_name="Test",
            success=True,
            message="OK",
            response_time_ms=100.5,
        )
        assert result.success is True
        assert result.response_time_ms == 100.5
        assert result.timestamp is not None
    
    def test_failure_result(self):
        """Test creating a failed ping result."""
        result = PingResult(
            project_name="Test",
            success=False,
            message="Connection failed",
        )
        assert result.success is False


class TestSupaKeeper:
    """Tests for SupaKeeper class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return Config(
            projects=[
                ProjectConfig(
                    name="Test Project",
                    url="https://test.supabase.co",
                    key="test-key",
                ),
            ],
            console_output=False,
        )
    
    def test_init(self, mock_config):
        """Test SupaKeeper initialization."""
        keeper = SupaKeeper(mock_config)
        assert keeper.config == mock_config
        assert keeper.logger is not None
    
    def test_get_status(self, mock_config):
        """Test getting status information."""
        keeper = SupaKeeper(mock_config)
        status = keeper.get_status()
        
        assert status["total_projects"] == 1
        assert status["enabled_projects"] == 1
        assert status["interval_hours"] == 48.0
        assert len(status["projects"]) == 1
    
    @patch("supakeeper.keeper.create_client")
    def test_ping_project_with_table(self, mock_create_client, mock_config):
        """Test pinging a project with a specific table."""
        # Setup mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute.return_value = MagicMock()
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client
        
        # Configure project with table
        mock_config.projects[0].table = "test_table"
        
        keeper = SupaKeeper(mock_config)
        result = keeper._ping_project(mock_config.projects[0])
        
        assert result.success is True
        assert "test_table" in result.message
    
    @patch("supakeeper.keeper.create_client")
    def test_ping_project_rest_fallback(self, mock_create_client):
        """Test falling back to REST API ping."""
        import httpx
        
        # Setup mocks to fail table queries but succeed on auth
        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("No table")
        mock_client.auth.get_session.return_value = MagicMock()  # This should succeed
        mock_create_client.return_value = mock_client
        
        config = Config(
            projects=[
                ProjectConfig(
                    name="Test",
                    url="https://test.supabase.co",
                    key="key",
                ),
            ],
            console_output=False,
            retry_attempts=1,
        )
        
        keeper = SupaKeeper(config)
        result = keeper._ping_project(config.projects[0])
        
        assert result.success is True
        assert "auth session" in result.message
    
    def test_ping_all_empty_projects(self):
        """Test pinging with no projects configured."""
        config = Config(projects=[], console_output=False)
        keeper = SupaKeeper(config)
        results = keeper.ping_all()
        
        assert results == []

