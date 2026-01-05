"""
Notification system for Supakeeper.

Supports notifications via:
- Webhook (Discord, Slack, etc.)
- Telegram Bot API
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx

from supakeeper.logger import get_logger


class Notifier:
    """Send notifications about keep-alive status."""
    
    # Telegram Bot API endpoint
    TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ) -> None:
        """
        Initialize notifier.
        
        Args:
            webhook_url: URL for webhook notifications (Discord, Slack, etc.)
            telegram_bot_token: Telegram Bot token from @BotFather
            telegram_chat_id: Telegram chat ID to send messages to
        """
        self.webhook_url = webhook_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.logger = get_logger()
    
    @property
    def has_webhook(self) -> bool:
        """Check if webhook is configured."""
        return bool(self.webhook_url)
    
    @property
    def has_telegram(self) -> bool:
        """Check if Telegram is configured."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)
    
    def send_success_notification(self, results: list) -> None:
        """Send notification for successful pings."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send via webhook if configured
        if self.has_webhook:
            message = self._build_success_message(results, timestamp)
            self._send_webhook(message)
        
        # Send via Telegram if configured
        if self.has_telegram:
            text = self._build_telegram_success_message(results, timestamp)
            self._send_telegram(text)
    
    def send_failure_notification(self, failed_results: list) -> None:
        """Send notification for failed pings."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send via webhook if configured
        if self.has_webhook:
            message = self._build_failure_message(failed_results, timestamp)
            self._send_webhook(message)
        
        # Send via Telegram if configured
        if self.has_telegram:
            text = self._build_telegram_failure_message(failed_results, timestamp)
            self._send_telegram(text)
    
    # ========================================
    # Webhook methods (Discord, Slack, etc.)
    # ========================================
    
    def _build_success_message(self, results: list, timestamp: str) -> dict:
        """Build success notification message for webhook."""
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
        """Build failure notification message for webhook."""
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
    
    # ========================================
    # Telegram Bot API methods
    # ========================================
    
    def _build_telegram_success_message(self, results: list, timestamp: str) -> str:
        """Build success notification message for Telegram."""
        project_list = "\n".join(
            f"✅ {r.project_name} ({r.response_time_ms:.0f}ms)"
            for r in results
        )
        
        return (
            f"🎉 *Supakeeper - All Projects Active*\n\n"
            f"Successfully pinged {len(results)} project(s):\n\n"
            f"{project_list}\n\n"
            f"_{timestamp}_"
        )
    
    def _build_telegram_failure_message(self, failed_results: list, timestamp: str) -> str:
        """Build failure notification message for Telegram."""
        project_list = "\n".join(
            f"❌ {r.project_name}: {r.message}"
            for r in failed_results
        )
        
        return (
            f"⚠️ *Supakeeper - Some Projects Failed*\n\n"
            f"Failed to ping {len(failed_results)} project(s):\n\n"
            f"{project_list}\n\n"
            f"_{timestamp}_"
        )
    
    def _send_telegram(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message via Telegram Bot API.
        
        Uses the sendMessage method:
        https://core.telegram.org/bots/api#sendmessage
        
        Args:
            text: Message text to send
            parse_mode: Parse mode for formatting (Markdown, HTML, or None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.has_telegram:
            return False
        
        url = self.TELEGRAM_API_BASE.format(token=self.telegram_bot_token)
        
        # Build request payload according to Telegram Bot API
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            # Disable link preview for cleaner messages
            "disable_web_page_preview": True,
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                
                result = response.json()
                
                if response.status_code == 200 and result.get("ok"):
                    self.logger.debug("Telegram notification sent successfully")
                    return True
                else:
                    error_desc = result.get("description", "Unknown error")
                    self.logger.warning(
                        f"Telegram API error: {error_desc} (code: {result.get('error_code')})"
                    )
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
