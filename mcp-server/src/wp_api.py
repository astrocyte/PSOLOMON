"""WordPress REST API client."""

import requests
from typing import Any, Optional
from .config import WordPressConfig


class WordPressAPIError(Exception):
    """Exception raised for WordPress API errors."""
    pass


class WordPressAPIClient:
    """Client for WordPress REST API operations."""

    def __init__(self, config: WordPressConfig):
        self.config = config
        self.base_url = f"{config.site_url.rstrip('/')}/wp-json/wp/v2"

        # Support both JWT and Application Password authentication
        if config.jwt_token:
            self.auth = None
            self.headers = {"Authorization": f"Bearer {config.jwt_token}"}
        else:
            self.auth = (config.api_user, config.api_password)
            self.headers = {}

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = requests.request(
            method=method,
            url=url,
            auth=self.auth,
            headers=self.headers,
            params=params,
            json=json_data,
            timeout=30
        )

        if not response.ok:
            raise WordPressAPIError(
                f"API request failed ({response.status_code}): {response.text}"
            )

        return response.json()

    def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        status: str = "publish"
    ) -> list[dict]:
        """Get posts from WordPress."""
        params = {
            "per_page": per_page,
            "page": page,
            "status": status,
        }

        if search:
            params["search"] = search

        return self._request("GET", "posts", params=params)

    def get_post(self, post_id: int) -> dict:
        """Get single post by ID."""
        return self._request("GET", f"posts/{post_id}")

    def get_pages(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None
    ) -> list[dict]:
        """Get pages from WordPress."""
        params = {
            "per_page": per_page,
            "page": page,
            "status": "publish",
        }

        if search:
            params["search"] = search

        return self._request("GET", "pages", params=params)

    def get_page(self, page_id: int) -> dict:
        """Get single page by ID."""
        return self._request("GET", f"pages/{page_id}")

    def get_post_meta(self, post_id: int) -> dict:
        """
        Get post metadata.
        Note: Requires custom endpoint or plugin that exposes meta.
        """
        # This is a basic implementation - may need adjustment based on your setup
        post = self.get_post(post_id)
        return post.get("meta", {})

    def search_content(self, query: str, post_type: str = "posts") -> list[dict]:
        """Search across content."""
        params = {
            "search": query,
            "per_page": 20,
        }

        return self._request("GET", post_type, params=params)
