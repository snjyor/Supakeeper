"""Tests for configuration loading and validation."""

import os

import pytest

from supakeeper.config import Config, ProjectConfig


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""
    
    def test_valid_project(self):
        """Test creating a valid project configuration."""
        project = ProjectConfig(
            name="Test Project",
            url="https://test.supabase.co",
            key="test-key-123",
        )
        assert project.name == "Test Project"
        assert project.url == "https://test.supabase.co"
        assert project.key == "test-key-123"
        assert project.enabled is True
    
    def test_missing_url_raises_error(self):
        """Test that missing URL raises ValueError."""
        with pytest.raises(ValueError, match="URL is required"):
            ProjectConfig(
                name="Test",
                url="",
                key="test-key",
            )
    
    def test_missing_key_raises_error(self):
        """Test that missing key raises ValueError."""
        with pytest.raises(ValueError, match="API key is required"):
            ProjectConfig(
                name="Test",
                url="https://test.supabase.co",
                key="",
            )
    
    def test_invalid_url_raises_error(self):
        """Test that non-HTTPS URL raises ValueError."""
        with pytest.raises(ValueError, match="must start with https://"):
            ProjectConfig(
                name="Test",
                url="http://test.supabase.co",
                key="test-key",
            )


class TestConfig:
    """Tests for Config class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert config.interval_hours == 48.0
        assert config.retry_attempts == 3
        assert config.retry_delay == 30
        assert config.log_level == "INFO"
        assert config.console_output is True
    
    def test_get_enabled_projects(self):
        """Test filtering enabled projects."""
        config = Config(projects=[
            ProjectConfig(name="Enabled", url="https://a.supabase.co", key="k1", enabled=True),
            ProjectConfig(name="Disabled", url="https://b.supabase.co", key="k2", enabled=False),
        ])
        
        enabled = config.get_enabled_projects()
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"
    
    def test_validate_no_projects(self):
        """Test validation with no projects configured."""
        config = Config(projects=[])
        errors = config.validate()
        assert any("No projects" in e for e in errors)
    
    def test_validate_interval_warning(self):
        """Test validation warns about long intervals."""
        config = Config(
            projects=[
                ProjectConfig(name="Test", url="https://t.supabase.co", key="k"),
            ],
            interval_hours=200,
        )
        errors = config.validate()
        assert any("168 hours" in e for e in errors)
    
    def test_load_single_project_from_env(self):
        """Test loading single project from environment variables."""
        os.environ["SUPABASE_URL"] = "https://env-test.supabase.co"
        os.environ["SUPABASE_KEY"] = "env-test-key"
        os.environ["SUPABASE_NAME"] = "My Test Project"
        os.environ["KEEPALIVE_INTERVAL_HOURS"] = "72"
        
        try:
            config = Config.load()
            
            assert len(config.projects) >= 1
            # Find our project
            project = next((p for p in config.projects if p.url == "https://env-test.supabase.co"), None)
            assert project is not None
            assert project.key == "env-test-key"
            assert project.name == "My Test Project"
            assert config.interval_hours == 72.0
        finally:
            del os.environ["SUPABASE_URL"]
            del os.environ["SUPABASE_KEY"]
            del os.environ["SUPABASE_NAME"]
            del os.environ["KEEPALIVE_INTERVAL_HOURS"]
    
    def test_load_multiple_projects_from_env(self):
        """Test loading multiple projects from numbered environment variables."""
        os.environ["SUPABASE_URL_1"] = "https://project1.supabase.co"
        os.environ["SUPABASE_KEY_1"] = "key1"
        os.environ["SUPABASE_NAME_1"] = "Project One"
        os.environ["SUPABASE_URL_2"] = "https://project2.supabase.co"
        os.environ["SUPABASE_KEY_2"] = "key2"
        os.environ["SUPABASE_NAME_2"] = "Project Two"
        
        try:
            config = Config.load()
            
            # Find our projects
            urls = [p.url for p in config.projects]
            assert "https://project1.supabase.co" in urls
            assert "https://project2.supabase.co" in urls
            
            p1 = next((p for p in config.projects if p.url == "https://project1.supabase.co"), None)
            p2 = next((p for p in config.projects if p.url == "https://project2.supabase.co"), None)
            
            assert p1 is not None
            assert p1.name == "Project One"
            assert p2 is not None
            assert p2.name == "Project Two"
        finally:
            for key in ["SUPABASE_URL_1", "SUPABASE_KEY_1", "SUPABASE_NAME_1",
                       "SUPABASE_URL_2", "SUPABASE_KEY_2", "SUPABASE_NAME_2"]:
                if key in os.environ:
                    del os.environ[key]
