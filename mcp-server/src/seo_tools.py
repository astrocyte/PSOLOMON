"""SEO analysis tools for WordPress content."""

import json
import re
from typing import Any, Optional
from bs4 import BeautifulSoup


class SEOAnalyzer:
    """Analyze WordPress content for SEO."""

    @staticmethod
    def extract_elementor_content(post_data: dict) -> dict:
        """
        Extract readable content from Elementor JSON data.

        Elementor stores page structure in _elementor_data meta field as JSON.
        """
        # Try to get Elementor data from meta
        meta = post_data.get("meta", {})
        elementor_data = meta.get("_elementor_data", "")

        if not elementor_data:
            return {
                "is_elementor": False,
                "text_content": "",
                "headings": [],
                "images": [],
            }

        try:
            if isinstance(elementor_data, str):
                data = json.loads(elementor_data)
            else:
                data = elementor_data

            text_content = []
            headings = []
            images = []

            def extract_from_element(element):
                """Recursively extract content from Elementor elements."""
                if isinstance(element, dict):
                    # Get widget type
                    widget_type = element.get("elType") or element.get("widgetType", "")

                    # Extract text from heading widgets
                    if "heading" in widget_type.lower():
                        settings = element.get("settings", {})
                        title = settings.get("title", "")
                        if title:
                            headings.append({
                                "text": title,
                                "tag": settings.get("header_size", "h2")
                            })

                    # Extract text from text editor widgets
                    if "text-editor" in widget_type.lower():
                        settings = element.get("settings", {})
                        text = settings.get("editor", "")
                        if text:
                            # Strip HTML tags
                            clean_text = BeautifulSoup(text, "html.parser").get_text()
                            text_content.append(clean_text)

                    # Extract images
                    if "image" in widget_type.lower():
                        settings = element.get("settings", {})
                        img_data = settings.get("image", {})
                        if isinstance(img_data, dict):
                            images.append({
                                "url": img_data.get("url", ""),
                                "alt": img_data.get("alt", ""),
                                "id": img_data.get("id", "")
                            })

                    # Recurse into child elements
                    elements = element.get("elements", [])
                    for child in elements:
                        extract_from_element(child)

            # Process all elements
            if isinstance(data, list):
                for element in data:
                    extract_from_element(element)

            return {
                "is_elementor": True,
                "text_content": "\n".join(text_content),
                "headings": headings,
                "images": images,
            }

        except (json.JSONDecodeError, Exception) as e:
            return {
                "is_elementor": True,
                "error": str(e),
                "text_content": "",
                "headings": [],
                "images": [],
            }

    @staticmethod
    def analyze_seo_metadata(post_data: dict) -> dict:
        """Analyze SEO-relevant metadata from a post."""
        title = post_data.get("title", {})
        if isinstance(title, dict):
            title = title.get("rendered", "")

        content = post_data.get("content", {})
        if isinstance(content, dict):
            content = content.get("rendered", "")

        excerpt = post_data.get("excerpt", {})
        if isinstance(excerpt, dict):
            excerpt = excerpt.get("rendered", "")

        # Parse HTML content
        soup = BeautifulSoup(content, "html.parser")

        # Extract headings
        headings = {
            "h1": [h.get_text().strip() for h in soup.find_all("h1")],
            "h2": [h.get_text().strip() for h in soup.find_all("h2")],
            "h3": [h.get_text().strip() for h in soup.find_all("h3")],
        }

        # Extract images and check alt tags
        images = []
        for img in soup.find_all("img"):
            images.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "has_alt": bool(img.get("alt")),
            })

        # Extract links
        internal_links = []
        external_links = []
        for link in soup.find_all("a"):
            href = link.get("href", "")
            if href:
                if href.startswith("http"):
                    external_links.append(href)
                else:
                    internal_links.append(href)

        # Get text content
        text_content = soup.get_text()
        word_count = len(text_content.split())

        # Check for meta from Yoast or RankMath (if available in meta field)
        meta = post_data.get("meta", {})
        yoast_title = meta.get("_yoast_wpseo_title", "")
        yoast_desc = meta.get("_yoast_wpseo_metadesc", "")

        return {
            "title": title,
            "title_length": len(title),
            "meta_title": yoast_title or title,
            "meta_description": yoast_desc or excerpt,
            "meta_description_length": len(yoast_desc or excerpt),
            "word_count": word_count,
            "headings": headings,
            "images": {
                "total": len(images),
                "without_alt": len([img for img in images if not img["has_alt"]]),
                "details": images,
            },
            "links": {
                "internal": len(internal_links),
                "external": len(external_links),
            },
        }

    @staticmethod
    def get_seo_recommendations(analysis: dict) -> list[str]:
        """Generate SEO recommendations based on analysis."""
        recommendations = []

        # Title checks
        if analysis["title_length"] < 30:
            recommendations.append("Title is too short (< 30 characters)")
        elif analysis["title_length"] > 60:
            recommendations.append("Title is too long (> 60 characters)")

        # Meta description checks
        if analysis["meta_description_length"] < 120:
            recommendations.append("Meta description is too short (< 120 characters)")
        elif analysis["meta_description_length"] > 160:
            recommendations.append("Meta description is too long (> 160 characters)")

        # Word count
        if analysis["word_count"] < 300:
            recommendations.append("Content is thin (< 300 words)")

        # Heading structure
        h1_count = len(analysis["headings"]["h1"])
        if h1_count == 0:
            recommendations.append("No H1 heading found")
        elif h1_count > 1:
            recommendations.append(f"Multiple H1 headings found ({h1_count})")

        # Image alt tags
        images_without_alt = analysis["images"]["without_alt"]
        if images_without_alt > 0:
            recommendations.append(
                f"{images_without_alt} image(s) missing alt text"
            )

        # Internal linking
        if analysis["links"]["internal"] < 2:
            recommendations.append("Add more internal links (< 2 found)")

        return recommendations
