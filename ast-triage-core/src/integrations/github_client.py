"""
src/integrations/github_client.py - Asynchronous GitHub API client.

Provides non-blocking methods for fetching PR metadata, diffs, posting
triage comments, and verifying webhook HMAC-SHA256 signatures via httpx.
"""
import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Asynchronous client for interacting with the GitHub REST API.

    Uses httpx for non-blocking HTTP requests and hmac for cryptographic
    webhook signature verification.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.settings = get_settings()
        self.token = token or self.settings.GITHUB_TOKEN
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def _get_headers(self, accept: str = "application/vnd.github+json") -> Dict[str, str]:
        """Builds standard headers including authentication if a token is present."""
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ASTRA-Triage-Bot",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def verify_webhook_signature(
        payload_bytes: bytes,
        signature_header: Optional[str],
        secret: Optional[str] = None,
    ) -> bool:
        """
        Validates GitHub HMAC-SHA256 signature from X-Hub-Signature-256.

        Args:
            payload_bytes: Raw request body bytes.
            signature_header: The value of the X-Hub-Signature-256 header.
            secret: Webhook secret key. If omitted, falls back to settings.

        Returns:
            True if signature matches or if secret is unset; False if invalid.
        """
        active_secret = secret or get_settings().GITHUB_WEBHOOK_SECRET
        if not active_secret:
            # If no secret is configured, allow requests through for local testing
            return True

        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header while webhook secret is configured")
            return False

        if not signature_header.startswith("sha256="):
            logger.warning("Invalid signature prefix; expected sha256=")
            return False

        given_sig = signature_header[len("sha256="):]
        computed_sig = hmac.new(
            active_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(given_sig, computed_sig)

    async def post_pr_comment(
        self,
        repo_name: str,
        pr_number: int,
        comment_body: str,
    ) -> bool:
        """
        Posts a triage markdown comment to a GitHub pull request.

        Args:
            repo_name: Repository in owner/repo format (e.g. django/django).
            pr_number: Pull request number.
            comment_body: Markdown content to post.

        Returns:
            True if successfully created (HTTP 201), False otherwise.
        """
        if not self.token:
            logger.info(
                f"No GITHUB_TOKEN configured; skipping comment post on {repo_name} #{pr_number}"
            )
            return False

        url = f"{self.base_url}/repos/{repo_name}/issues/{pr_number}/comments"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"body": comment_body},
                )
                if response.status_code == 201:
                    logger.info(f"Successfully posted triage comment to {repo_name} #{pr_number}")
                    return True
                else:
                    logger.warning(
                        f"Failed to post comment to {repo_name} #{pr_number}: "
                        f"status={response.status_code}, response={response.text}"
                    )
                    return False
            except Exception as e:
                logger.error(f"Error posting comment to {repo_name} #{pr_number}: {e}")
                return False

    async def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """
        Fetches the raw unified diff for a pull request.

        Args:
            repo_name: Repository in owner/repo format.
            pr_number: Pull request number.

        Returns:
            Raw unified diff string.
        """
        url = f"{self.base_url}/repos/{repo_name}/pulls/{pr_number}"
        headers = self._get_headers(accept="application/vnd.github.v3.diff")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.text
                logger.warning(
                    f"Failed to fetch diff for {repo_name} #{pr_number}: status={response.status_code}"
                )
                return ""
            except Exception as e:
                logger.error(f"Error fetching PR diff for {repo_name} #{pr_number}: {e}")
                return ""

    async def get_pr_details(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetches metadata for a pull request.

        Args:
            repo_name: Repository in owner/repo format.
            pr_number: Pull request number.

        Returns:
            Dictionary containing PR metadata fields.
        """
        url = f"{self.base_url}/repos/{repo_name}/pulls/{pr_number}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                return {}
            except Exception as e:
                logger.error(f"Error fetching PR details for {repo_name} #{pr_number}: {e}")
                return {}
