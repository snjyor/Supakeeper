"""
Notification system for Supakeeper.

Supports webhook notifications to Discord, Slack, and other services.
"""

from datetime import datetime
from typing import Optional

import httpx

from supakeeper.logger import get_logger


class Notifier:
    """Send notifications about keep-alive status."""
    
    def __init__(self, webhook_url: Optional[str] = None) -> None:
        """
        Initialize notifier.
        
        Args:
            webhook_url: URL for webhook notifications (Discord, Slack, etc.)
        """
        self.webhook_url = webhook_url
        self.logger = get_logger()
    
    def send_success_notification(self, results: list) -> None:
        """Send notification for successful pings."""
        if not self.webhook_url:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message for Discord/Slack
        message = self._build_success_message(results, timestamp)
        self._send_webhook(message)
    
    def send_failure_notification(self, failed_results: list) -> None:
        """Send notification for failed pings."""
        if not self.webhook_url:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message for Discord/Slack
        message = self._build_failure_message(failed_results, timestamp)
        self._send_webhook(message)
    
    def _build_success_message(self, results: list, timestamp: str) -> dict:
        """Build success notification message."""
        project_list = "\n".join(
            f"✅ {r.project_name} ({r.response_time_ms:.0f}ms)"
            for r in results
        )
        
        # Discord embed format (also works with many other webhooks)
        return {
            "embeds": [
                {
                    "title": "🎉 Supakeeper - All Projects Active",
                    "description": f"Successfully pinged {len(results)} project(s):\n\n{project_list}",
                    "color": 5763719,  # Green
                    "footer": {"text": f"Supakeeper | {timestamp}"},
                }
            ],
            # Slack format fallback
            "text": f"✅ Supakeeper: Successfully pinged {len(results)} project(s)",
        }
    
    def _build_failure_message(self, failed_results: list, timestamp: str) -> dict:
        """Build failure notification message."""
        project_list = "\n".join(
            f"❌ {r.project_name}: {r.message}"
            for r in failed_results
        )
        
        # Discord embed format
        return {
            "embeds": [
                {
                    "title": "⚠️ Supakeeper - Some Projects Failed",
                    "description": f"Failed to ping {len(failed_results)} project(s):\n\n{project_list}",
                    "color": 15548997,  # Red
                    "footer": {"text": f"Supakeeper | {timestamp}"},
                }
            ],
            # Slack format fallback
            "text": f"⚠️ Supakeeper: Failed to ping {len(failed_results)} project(s)",
        }
    
    def _send_webhook(self, payload: dict) -> bool:
        """
        Send webhook notification.
        
        Args:
            payload: JSON payload to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            return False
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code in (200, 204):
                    self.logger.debug("Webhook notification sent successfully")
                    return True
                else:
                    self.logger.warning(
                        f"Webhook returned status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False

