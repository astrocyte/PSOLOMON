"""WordPress MCP Server - Main entry point."""

import os
import asyncio
from typing import Any
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import Tool, TextContent

from .config import WordPressConfig
from .wp_cli import WPCLIClient, WPCLIError
from .wp_api import WordPressAPIClient, WordPressAPIError
from .seo_tools import SEOAnalyzer
from .image_optimizer import ImageOptimizer
from .learndash_manager import LearnDashManager
from .woocommerce_manager import WooCommerceManager
from .backup_manager import BackupManager

# Load environment variables
load_dotenv()

# Initialize server
server = Server("wordpress-seo-admin")

# Global clients (initialized on first use)
wp_cli: WPCLIClient | None = None
wp_api: WordPressAPIClient | None = None
img_optimizer: ImageOptimizer | None = None
ld_manager: LearnDashManager | None = None
wc_manager: WooCommerceManager | None = None
backup_manager: BackupManager | None = None
config: WordPressConfig | None = None


def get_clients():
    """Get or initialize WordPress clients."""
    global wp_cli, wp_api, img_optimizer, ld_manager, wc_manager, backup_manager, config

    if config is None:
        config = WordPressConfig.from_env()
        errors = config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    if wp_cli is None:
        wp_cli = WPCLIClient(config)

    if wp_api is None:
        wp_api = WordPressAPIClient(config)

    if img_optimizer is None:
        img_optimizer = ImageOptimizer(config)

    if ld_manager is None:
        ld_manager = LearnDashManager(config, wp_cli)

    if wc_manager is None:
        wc_manager = WooCommerceManager(config, wp_api)

    if backup_manager is None:
        backup_manager = BackupManager(config)

    return wp_cli, wp_api, img_optimizer, ld_manager, wc_manager, backup_manager


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        # Site Info & Management
        Tool(
            name="wp_get_info",
            description="Get WordPress site information (version, URL, theme, active plugins)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="wp_plugin_list",
            description="List all installed WordPress plugins with their status",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: active, inactive, or must-use",
                        "enum": ["active", "inactive", "must-use"],
                    }
                },
            },
        ),
        Tool(
            name="wp_theme_list",
            description="List all installed WordPress themes",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Content Operations
        Tool(
            name="wp_post_list",
            description="List WordPress posts or pages",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_type": {
                        "type": "string",
                        "description": "Post type to list",
                        "default": "post",
                    },
                    "post_status": {
                        "type": "string",
                        "description": "Post status filter",
                        "default": "publish",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of posts to return",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="wp_get_post",
            description="Get full details of a specific post or page by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "number",
                        "description": "WordPress post ID",
                    },
                },
                "required": ["post_id"],
            },
        ),
        Tool(
            name="wp_search",
            description="Search WordPress content across posts and pages",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "post_type": {
                        "type": "string",
                        "description": "Post type to search (post, page, etc.)",
                        "default": "post",
                    },
                },
                "required": ["query"],
            },
        ),
        # SEO Tools
        Tool(
            name="seo_analyze_post",
            description="Perform comprehensive SEO analysis on a post or page",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "number",
                        "description": "WordPress post ID to analyze",
                    },
                },
                "required": ["post_id"],
            },
        ),
        Tool(
            name="elementor_extract_content",
            description="Extract and analyze content from Elementor page builder pages",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "number",
                        "description": "WordPress post ID with Elementor content",
                    },
                },
                "required": ["post_id"],
            },
        ),
        # Maintenance & Updates
        Tool(
            name="wp_check_updates",
            description="Check for available WordPress core, plugin, and theme updates",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Image Optimization Tools
        Tool(
            name="image_analyze",
            description="Analyze a WordPress media image for optimization opportunities",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "number",
                        "description": "WordPress media attachment ID",
                    },
                },
                "required": ["media_id"],
            },
        ),
        Tool(
            name="image_optimize",
            description="Optimize an image (convert to WebP, compress, resize) and return the optimized version",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Image URL to optimize",
                    },
                    "format": {
                        "type": "string",
                        "description": "Target format (auto, webp, jpeg, png)",
                        "enum": ["auto", "webp", "jpeg", "png"],
                        "default": "auto",
                    },
                    "quality": {
                        "type": "number",
                        "description": "Quality setting (1-100)",
                        "default": 85,
                    },
                    "max_width": {
                        "type": "number",
                        "description": "Maximum width in pixels",
                        "default": 2048,
                    },
                    "max_height": {
                        "type": "number",
                        "description": "Maximum height in pixels",
                        "default": 2048,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="image_audit_site",
            description="Audit all images on the site for SEO and performance issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of images to analyze",
                        "default": 50,
                    },
                },
            },
        ),
        # LearnDash Course Management
        Tool(
            name="ld_create_course",
            description="Create a new LearnDash course",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Course title"},
                    "content": {"type": "string", "description": "Course description"},
                    "status": {
                        "type": "string",
                        "enum": ["publish", "draft", "private"],
                        "default": "draft",
                    },
                    "price": {"type": "number", "description": "Course price (optional)"},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="ld_update_course",
            description="Update an existing LearnDash course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "number", "description": "Course ID"},
                    "title": {"type": "string", "description": "New title (optional)"},
                    "content": {"type": "string", "description": "New content (optional)"},
                    "price": {"type": "number", "description": "New price (optional)"},
                },
                "required": ["course_id"],
            },
        ),
        Tool(
            name="ld_list_courses",
            description="List all LearnDash courses",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "default": "any"},
                    "limit": {"type": "number", "default": 50},
                },
            },
        ),
        Tool(
            name="ld_create_lesson",
            description="Create a new lesson in a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "number", "description": "Parent course ID"},
                    "title": {"type": "string", "description": "Lesson title"},
                    "content": {"type": "string", "description": "Lesson content"},
                    "order": {"type": "number", "description": "Lesson order (optional)"},
                },
                "required": ["course_id", "title"],
            },
        ),
        Tool(
            name="ld_update_lesson",
            description="Update an existing lesson",
            inputSchema={
                "type": "object",
                "properties": {
                    "lesson_id": {"type": "number", "description": "Lesson ID"},
                    "title": {"type": "string", "description": "New title (optional)"},
                    "content": {"type": "string", "description": "New content (optional)"},
                    "order": {"type": "number", "description": "New order (optional)"},
                },
                "required": ["lesson_id"],
            },
        ),
        Tool(
            name="ld_create_quiz",
            description="Create a new quiz for a course/lesson",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "number", "description": "Associated course ID"},
                    "lesson_id": {"type": "number", "description": "Associated lesson ID (optional)"},
                    "title": {"type": "string", "description": "Quiz title"},
                    "passing_score": {"type": "number", "default": 80},
                },
                "required": ["course_id", "title"],
            },
        ),
        Tool(
            name="ld_add_quiz_question",
            description="Add a question to a quiz",
            inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {"type": "number", "description": "Quiz ID"},
                    "question_text": {"type": "string", "description": "The question"},
                    "question_type": {
                        "type": "string",
                        "enum": ["single", "multiple", "free_answer", "essay"],
                        "default": "single",
                    },
                    "points": {"type": "number", "default": 1},
                },
                "required": ["quiz_id", "question_text"],
            },
        ),
        Tool(
            name="ld_enroll_user",
            description="Enroll a user in a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "number", "description": "WordPress user ID"},
                    "course_id": {"type": "number", "description": "Course ID"},
                },
                "required": ["user_id", "course_id"],
            },
        ),
        Tool(
            name="ld_create_group",
            description="Create a LearnDash group",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Group name"},
                    "description": {"type": "string", "description": "Group description"},
                    "course_ids": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Course IDs to associate",
                    },
                },
                "required": ["title"],
            },
        ),
        # WooCommerce Product Management
        Tool(
            name="wc_create_product",
            description="Create a WooCommerce product",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name"},
                    "price": {"type": "number", "description": "Product price"},
                    "description": {"type": "string", "description": "Full description"},
                    "sku": {"type": "string", "description": "Product SKU"},
                    "course_id": {"type": "number", "description": "Link to LearnDash course (optional)"},
                },
                "required": ["name", "price"],
            },
        ),
        Tool(
            name="wc_update_product",
            description="Update a WooCommerce product",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "number", "description": "Product ID"},
                    "name": {"type": "string", "description": "New name (optional)"},
                    "price": {"type": "number", "description": "New price (optional)"},
                    "sale_price": {"type": "number", "description": "Sale price (optional)"},
                },
                "required": ["product_id"],
            },
        ),
        Tool(
            name="wc_list_products",
            description="List WooCommerce products",
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {"type": "number", "default": 20},
                    "search": {"type": "string", "description": "Search term (optional)"},
                },
            },
        ),
        Tool(
            name="wc_list_orders",
            description="List WooCommerce orders",
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {"type": "number", "default": 20},
                    "status": {"type": "string", "description": "Filter by status (optional)"},
                },
            },
        ),
        Tool(
            name="wc_create_coupon",
            description="Create a discount coupon",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Coupon code (e.g., SUMMER2024)"},
                    "discount_type": {
                        "type": "string",
                        "enum": ["percent", "fixed_cart", "fixed_product"],
                        "default": "percent",
                    },
                    "amount": {"type": "number", "description": "Discount amount"},
                    "usage_limit": {"type": "number", "description": "Max uses (optional)"},
                },
                "required": ["code", "amount"],
            },
        ),
        Tool(
            name="wc_get_sales_report",
            description="Get sales report for period",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["week", "month", "year"],
                        "default": "month",
                    },
                },
            },
        ),
        # Backup Management
        Tool(
            name="wp_create_backup",
            description="Create a complete WordPress backup (database + files) and download to local machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_files": {
                        "type": "boolean",
                        "description": "Include wp-content directory",
                        "default": True,
                    },
                    "include_database": {
                        "type": "boolean",
                        "description": "Include database dump",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="wp_list_backups",
            description="List all available local backups",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="wp_delete_backup",
            description="Delete a specific backup file",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup_filename": {
                        "type": "string",
                        "description": "Filename of backup to delete (e.g., sst_nyc_20251203_153000.tar.gz)",
                    },
                },
                "required": ["backup_filename"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        cli, api, img_opt, ld, wc, backup = get_clients()

        # Site Info & Management
        if name == "wp_get_info":
            info = cli.get_info()
            plugins = cli.list_plugins(status="active")
            themes = cli.list_themes()
            active_theme = next((t for t in themes if t.get("status") == "active"), {})

            result = {
                **info,
                "active_theme": active_theme.get("name", "Unknown"),
                "active_plugins_count": len(plugins),
            }
            return [TextContent(type="text", text=str(result))]

        elif name == "wp_plugin_list":
            status = arguments.get("status")
            plugins = cli.list_plugins(status=status)
            return [TextContent(type="text", text=str(plugins))]

        elif name == "wp_theme_list":
            themes = cli.list_themes()
            return [TextContent(type="text", text=str(themes))]

        # Content Operations
        elif name == "wp_post_list":
            post_type = arguments.get("post_type", "post")
            post_status = arguments.get("post_status", "publish")
            limit = arguments.get("limit", 10)

            posts = cli.list_posts(
                post_type=post_type,
                post_status=post_status,
                limit=limit
            )
            return [TextContent(type="text", text=str(posts))]

        elif name == "wp_get_post":
            post_id = arguments["post_id"]
            # Use REST API for richer data
            post = api.get_post(post_id)
            return [TextContent(type="text", text=str(post))]

        elif name == "wp_search":
            query = arguments["query"]
            post_type = arguments.get("post_type", "post")

            results = cli.search_posts(search=query, post_type=post_type)
            return [TextContent(type="text", text=str(results))]

        # SEO Tools
        elif name == "seo_analyze_post":
            post_id = arguments["post_id"]
            post = api.get_post(post_id)

            # Analyze SEO
            seo_analysis = SEOAnalyzer.analyze_seo_metadata(post)
            recommendations = SEOAnalyzer.get_seo_recommendations(seo_analysis)

            result = {
                "analysis": seo_analysis,
                "recommendations": recommendations,
            }
            return [TextContent(type="text", text=str(result))]

        elif name == "elementor_extract_content":
            post_id = arguments["post_id"]
            post = api.get_post(post_id)

            # Extract Elementor content
            elementor_data = SEOAnalyzer.extract_elementor_content(post)
            return [TextContent(type="text", text=str(elementor_data))]

        # Maintenance & Updates
        elif name == "wp_check_updates":
            updates = cli.check_updates()
            return [TextContent(type="text", text=str(updates))]

        # Image Optimization Tools
        elif name == "image_analyze":
            media_id = arguments["media_id"]
            analysis = img_opt.analyze_wordpress_image(media_id)
            return [TextContent(type="text", text=str(analysis))]

        elif name == "image_optimize":
            url = arguments["url"]
            format = arguments.get("format", "auto")
            quality = arguments.get("quality", 85)
            max_width = arguments.get("max_width", 2048)
            max_height = arguments.get("max_height", 2048)

            optimized_data, result = img_opt.optimize_image(
                url=url,
                target_format=format,
                quality=quality,
                max_width=max_width,
                max_height=max_height
            )

            # Return optimization results
            result_dict = {
                "original_size_kb": round(result.original_size / 1024, 2),
                "optimized_size_kb": round(result.optimized_size / 1024, 2),
                "savings_kb": round(result.savings_bytes / 1024, 2),
                "savings_percent": round(result.savings_percent, 1),
                "format": result.format,
                "dimensions": f"{result.width}x{result.height}",
                "note": "Optimized image data is ready for upload (not shown in text output)"
            }
            return [TextContent(type="text", text=str(result_dict))]

        elif name == "image_audit_site":
            limit = arguments.get("limit", 50)

            # Get all media from WordPress
            media_url = f"{api.base_url.replace('/wp/v2', '/wp/v2')}/media"
            response = img_opt.session.get(
                media_url,
                params={"per_page": limit, "media_type": "image"},
                timeout=30
            )
            response.raise_for_status()
            media_items = response.json()

            # Analyze each image
            results = []
            for media in media_items:
                try:
                    analysis = img_opt.analyze_wordpress_image(media["id"])
                    results.append(analysis)
                except Exception as e:
                    results.append({
                        "media_id": media["id"],
                        "error": str(e)
                    })

            # Generate summary
            total_images = len(results)
            missing_alt = len([r for r in results if not r.get("has_alt_text")])
            large_files = len([r for r in results if r.get("file_size_kb", 0) > 500])
            total_potential_savings = sum(
                r.get("estimated_webp_savings_kb", 0) for r in results
            )

            summary = {
                "total_images_analyzed": total_images,
                "missing_alt_text": missing_alt,
                "large_files_over_500kb": large_files,
                "total_potential_webp_savings_kb": round(total_potential_savings, 2),
                "images": results
            }

            return [TextContent(type="text", text=str(summary))]

        # LearnDash Course Management
        elif name == "ld_create_course":
            result = ld.create_course(
                title=arguments["title"],
                content=arguments.get("content", ""),
                status=arguments.get("status", "draft"),
                price=arguments.get("price"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_update_course":
            result = ld.update_course(
                course_id=arguments["course_id"],
                title=arguments.get("title"),
                content=arguments.get("content"),
                price=arguments.get("price"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_list_courses":
            courses = ld.list_courses(
                status=arguments.get("status", "any"),
                limit=arguments.get("limit", 50)
            )
            return [TextContent(type="text", text=str(courses))]

        elif name == "ld_create_lesson":
            result = ld.create_lesson(
                course_id=arguments["course_id"],
                title=arguments["title"],
                content=arguments.get("content", ""),
                order=arguments.get("order"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_update_lesson":
            result = ld.update_lesson(
                lesson_id=arguments["lesson_id"],
                title=arguments.get("title"),
                content=arguments.get("content"),
                order=arguments.get("order"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_create_quiz":
            result = ld.create_quiz(
                course_id=arguments["course_id"],
                lesson_id=arguments.get("lesson_id"),
                title=arguments["title"],
                passing_score=arguments.get("passing_score", 80),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_add_quiz_question":
            result = ld.add_quiz_question(
                quiz_id=arguments["quiz_id"],
                question_text=arguments["question_text"],
                question_type=arguments.get("question_type", "single"),
                points=arguments.get("points", 1),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_enroll_user":
            result = ld.enroll_user(
                user_id=arguments["user_id"],
                course_id=arguments["course_id"],
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "ld_create_group":
            result = ld.create_group(
                title=arguments["title"],
                description=arguments.get("description", ""),
                course_ids=arguments.get("course_ids"),
            )
            return [TextContent(type="text", text=str(result))]

        # WooCommerce Product Management
        elif name == "wc_create_product":
            result = wc.create_product(
                name=arguments["name"],
                price=arguments["price"],
                description=arguments.get("description", ""),
                sku=arguments.get("sku"),
                course_id=arguments.get("course_id"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "wc_update_product":
            result = wc.update_product(
                product_id=arguments["product_id"],
                name=arguments.get("name"),
                price=arguments.get("price"),
                sale_price=arguments.get("sale_price"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "wc_list_products":
            products = wc.list_products(
                per_page=arguments.get("per_page", 20),
                search=arguments.get("search"),
            )
            return [TextContent(type="text", text=str(products))]

        elif name == "wc_list_orders":
            orders = wc.list_orders(
                per_page=arguments.get("per_page", 20),
                status=arguments.get("status"),
            )
            return [TextContent(type="text", text=str(orders))]

        elif name == "wc_create_coupon":
            result = wc.create_coupon(
                code=arguments["code"],
                discount_type=arguments.get("discount_type", "percent"),
                amount=arguments["amount"],
                usage_limit=arguments.get("usage_limit"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "wc_get_sales_report":
            report = wc.get_sales_report(
                period=arguments.get("period", "month")
            )
            return [TextContent(type="text", text=str(report))]

        # Backup Management
        elif name == "wp_create_backup":
            include_files = arguments.get("include_files", True)
            include_database = arguments.get("include_database", True)

            result = backup.create_backup(
                include_files=include_files,
                include_database=include_database
            )

            summary = f"""
Backup Created Successfully!

Timestamp: {result['timestamp']}
Archive: {result['archive_path']}
Total Size: {result['total_size']}

Backed up:
- Database: {'✓' if result['database_backed_up'] else '✗'} {result.get('database_size', '')}
- Files: {'✓' if result['files_backed_up'] else '✗'} {result.get('files_size', '')}

The backup is saved locally and excluded from git via .gitignore
"""
            return [TextContent(type="text", text=summary)]

        elif name == "wp_list_backups":
            backups = backup.list_backups()

            if not backups:
                return [TextContent(type="text", text="No backups found in ./backups/")]

            result = "Available Backups:\n\n"
            for b in backups:
                result += f"- {b['filename']}\n"
                result += f"  Size: {b['size']}\n"
                result += f"  Created: {b['created']}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "wp_delete_backup":
            filename = arguments["backup_filename"]
            success = backup.delete_backup(filename)

            if success:
                return [TextContent(type="text", text=f"✓ Backup deleted: {filename}")]
            else:
                return [TextContent(type="text", text=f"✗ Backup not found: {filename}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except (WPCLIError, WordPressAPIError) as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
