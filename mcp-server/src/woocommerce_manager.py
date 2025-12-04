"""WooCommerce product and sales management."""

from typing import Optional, Literal
from .config import WordPressConfig
from .wp_api import WordPressAPIClient


class WooCommerceManager:
    """Manage WooCommerce products, orders, and coupons."""

    def __init__(self, config: WordPressConfig, wp_api: WordPressAPIClient):
        self.config = config
        self.api = wp_api
        self.wc_base = f"{config.site_url.rstrip('/')}/wp-json/wc/v3"

    # ==================== PRODUCT MANAGEMENT ====================

    def create_product(
        self,
        name: str,
        type: Literal["simple", "variable", "course"] = "simple",
        price: Optional[float] = None,
        regular_price: Optional[float] = None,
        sale_price: Optional[float] = None,
        description: str = "",
        short_description: str = "",
        sku: Optional[str] = None,
        categories: Optional[list[int]] = None,
        course_id: Optional[int] = None,  # For LearnDash integration
        status: Literal["draft", "publish"] = "publish",
    ) -> dict:
        """
        Create a WooCommerce product.

        Args:
            name: Product name
            type: Product type (simple, variable, course)
            price: Product price
            regular_price: Regular price
            sale_price: Sale price (optional)
            description: Full description
            short_description: Short description
            sku: Product SKU
            categories: Category IDs
            course_id: LearnDash course ID (for course products)
            status: Product status

        Returns:
            Created product data
        """
        product_data = {
            "name": name,
            "type": type,
            "status": status,
            "description": description,
            "short_description": short_description,
        }

        if price:
            product_data["regular_price"] = str(price)
        if regular_price:
            product_data["regular_price"] = str(regular_price)
        if sale_price:
            product_data["sale_price"] = str(sale_price)
        if sku:
            product_data["sku"] = sku
        if categories:
            product_data["categories"] = [{"id": cat_id} for cat_id in categories]

        # Add LearnDash course linkage
        if course_id:
            product_data["meta_data"] = [
                {"key": "_related_course", "value": str(course_id)}
            ]

        return self.api._request("POST", f"{self.wc_base}/products", json_data=product_data)

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        sale_price: Optional[float] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        stock_quantity: Optional[int] = None,
    ) -> dict:
        """
        Update an existing product.

        Args:
            product_id: WooCommerce product ID
            name: New name (optional)
            price: New price (optional)
            sale_price: New sale price (optional)
            description: New description (optional)
            status: New status (optional)
            stock_quantity: New stock quantity (optional)

        Returns:
            Updated product data
        """
        update_data = {}

        if name:
            update_data["name"] = name
        if price is not None:
            update_data["regular_price"] = str(price)
        if sale_price is not None:
            update_data["sale_price"] = str(sale_price)
        if description:
            update_data["description"] = description
        if status:
            update_data["status"] = status
        if stock_quantity is not None:
            update_data["stock_quantity"] = stock_quantity
            update_data["manage_stock"] = True

        return self.api._request(
            "PUT",
            f"{self.wc_base}/products/{product_id}",
            json_data=update_data
        )

    def list_products(
        self,
        per_page: int = 20,
        status: Optional[str] = None,
        category: Optional[int] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        """
        List WooCommerce products.

        Args:
            per_page: Number of products to return
            status: Filter by status (publish, draft, pending)
            category: Filter by category ID
            search: Search term

        Returns:
            List of products
        """
        params = {"per_page": per_page}

        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        return self.api._request("GET", f"{self.wc_base}/products", params=params)

    def delete_product(self, product_id: int, force: bool = False) -> dict:
        """
        Delete a product.

        Args:
            product_id: Product ID to delete
            force: Permanently delete (bypass trash)

        Returns:
            Deletion confirmation
        """
        params = {"force": force}
        return self.api._request(
            "DELETE",
            f"{self.wc_base}/products/{product_id}",
            params=params
        )

    # ==================== ORDER MANAGEMENT ====================

    def list_orders(
        self,
        per_page: int = 20,
        status: Optional[str] = None,
        customer: Optional[int] = None,
    ) -> list[dict]:
        """
        List WooCommerce orders.

        Args:
            per_page: Number of orders to return
            status: Filter by status (completed, processing, pending, etc.)
            customer: Filter by customer ID

        Returns:
            List of orders
        """
        params = {"per_page": per_page}

        if status:
            params["status"] = status
        if customer:
            params["customer"] = customer

        return self.api._request("GET", f"{self.wc_base}/orders", params=params)

    def get_order(self, order_id: int) -> dict:
        """Get single order details."""
        return self.api._request("GET", f"{self.wc_base}/orders/{order_id}")

    def update_order_status(
        self,
        order_id: int,
        status: Literal[
            "pending",
            "processing",
            "on-hold",
            "completed",
            "cancelled",
            "refunded",
            "failed",
        ],
    ) -> dict:
        """
        Update order status.

        Args:
            order_id: Order ID
            status: New status

        Returns:
            Updated order
        """
        return self.api._request(
            "PUT",
            f"{self.wc_base}/orders/{order_id}",
            json_data={"status": status}
        )

    # ==================== COUPON MANAGEMENT ====================

    def create_coupon(
        self,
        code: str,
        discount_type: Literal["percent", "fixed_cart", "fixed_product"] = "percent",
        amount: float = 0,
        description: str = "",
        expiry_date: Optional[str] = None,
        minimum_amount: Optional[float] = None,
        maximum_amount: Optional[float] = None,
        product_ids: Optional[list[int]] = None,
        usage_limit: Optional[int] = None,
    ) -> dict:
        """
        Create a coupon code.

        Args:
            code: Coupon code (e.g., "SUMMER2024")
            discount_type: Type of discount
            amount: Discount amount
            description: Coupon description
            expiry_date: Expiration date (YYYY-MM-DD)
            minimum_amount: Minimum order amount
            maximum_amount: Maximum order amount
            product_ids: Specific products coupon applies to
            usage_limit: Max number of uses

        Returns:
            Created coupon data
        """
        coupon_data = {
            "code": code,
            "discount_type": discount_type,
            "amount": str(amount),
            "description": description,
        }

        if expiry_date:
            coupon_data["date_expires"] = expiry_date
        if minimum_amount:
            coupon_data["minimum_amount"] = str(minimum_amount)
        if maximum_amount:
            coupon_data["maximum_amount"] = str(maximum_amount)
        if product_ids:
            coupon_data["product_ids"] = product_ids
        if usage_limit:
            coupon_data["usage_limit"] = usage_limit

        return self.api._request("POST", f"{self.wc_base}/coupons", json_data=coupon_data)

    def list_coupons(self, per_page: int = 20) -> list[dict]:
        """List all coupons."""
        return self.api._request(
            "GET",
            f"{self.wc_base}/coupons",
            params={"per_page": per_page}
        )

    def delete_coupon(self, coupon_id: int, force: bool = True) -> dict:
        """Delete a coupon."""
        return self.api._request(
            "DELETE",
            f"{self.wc_base}/coupons/{coupon_id}",
            params={"force": force}
        )

    # ==================== CATEGORY MANAGEMENT ====================

    def create_product_category(
        self,
        name: str,
        description: str = "",
        parent: Optional[int] = None,
    ) -> dict:
        """
        Create a product category.

        Args:
            name: Category name
            description: Category description
            parent: Parent category ID (for subcategories)

        Returns:
            Created category data
        """
        category_data = {
            "name": name,
            "description": description,
        }

        if parent:
            category_data["parent"] = parent

        return self.api._request(
            "POST",
            f"{self.wc_base}/products/categories",
            json_data=category_data
        )

    def list_product_categories(self, per_page: int = 50) -> list[dict]:
        """List all product categories."""
        return self.api._request(
            "GET",
            f"{self.wc_base}/products/categories",
            params={"per_page": per_page}
        )

    # ==================== CUSTOMER MANAGEMENT ====================

    def list_customers(
        self,
        per_page: int = 20,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        """
        List WooCommerce customers.

        Args:
            per_page: Number to return
            role: Filter by role
            search: Search term

        Returns:
            List of customers
        """
        params = {"per_page": per_page}

        if role:
            params["role"] = role
        if search:
            params["search"] = search

        return self.api._request("GET", f"{self.wc_base}/customers", params=params)

    def get_customer_orders(self, customer_id: int) -> list[dict]:
        """Get all orders for a specific customer."""
        return self.list_orders(customer=customer_id, per_page=100)

    # ==================== REPORTS & ANALYTICS ====================

    def get_sales_report(self, period: Literal["week", "month", "year"] = "month") -> dict:
        """
        Get sales report for period.

        Args:
            period: Time period (week, month, year)

        Returns:
            Sales data
        """
        return self.api._request(
            "GET",
            f"{self.wc_base}/reports/sales",
            params={"period": period}
        )

    def get_top_sellers(self, period: Literal["week", "month", "year"] = "month") -> list[dict]:
        """Get top selling products."""
        return self.api._request(
            "GET",
            f"{self.wc_base}/reports/top_sellers",
            params={"period": period}
        )

    # ==================== LEARNDASH INTEGRATION ====================

    def link_product_to_course(self, product_id: int, course_id: int) -> dict:
        """
        Link a WooCommerce product to a LearnDash course.

        Args:
            product_id: WooCommerce product ID
            course_id: LearnDash course ID

        Returns:
            Updated product with course linkage
        """
        return self.update_product(
            product_id,
            meta_data=[
                {"key": "_related_course", "value": str(course_id)},
                {"key": "_learndash_product", "value": "yes"},
            ]
        )

    def get_course_product(self, course_id: int) -> Optional[dict]:
        """
        Get WooCommerce product linked to a course.

        Args:
            course_id: LearnDash course ID

        Returns:
            Product data if found, None otherwise
        """
        # Search for product with related course meta
        products = self.list_products(per_page=100)

        for product in products:
            meta = product.get("meta_data", [])
            for m in meta:
                if m.get("key") == "_related_course" and m.get("value") == str(course_id):
                    return product

        return None
