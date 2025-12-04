<?php
/**
 * Commission Manager
 * Tracks affiliate commissions from WooCommerce orders and LearnDash enrollments
 */

if (!defined('ABSPATH')) exit;

class SST_Commission_Manager {

    /**
     * Get affiliate statistics
     *
     * @param string $coupon_code Affiliate's coupon code
     * @return array Stats including total sales, commission earned, paid, and pending
     */
    public function get_affiliate_stats($coupon_code) {
        if (!class_exists('WooCommerce')) {
            return [
                'total_sales' => 0,
                'total_commission' => 0,
                'commission_paid' => 0,
                'commission_pending' => 0,
                'order_count' => 0
            ];
        }

        global $wpdb;

        // Get affiliate data to access commission rate
        $affiliate_table = $wpdb->prefix . 'sst_affiliates';
        $affiliate = $wpdb->get_row($wpdb->prepare(
            "SELECT commission_rate FROM {$affiliate_table} WHERE coupon_code = %s",
            $coupon_code
        ));

        if (!$affiliate) {
            return [
                'total_sales' => 0,
                'total_commission' => 0,
                'commission_paid' => 0,
                'commission_pending' => 0,
                'order_count' => 0
            ];
        }

        $commission_rate = floatval($affiliate->commission_rate) / 100;

        // Get all completed orders that used this coupon
        $orders = wc_get_orders([
            'status' => ['completed', 'processing'],
            'limit' => -1,
            'coupon' => $coupon_code
        ]);

        $total_sales = 0;
        $total_commission = 0;
        $order_count = count($orders);

        foreach ($orders as $order) {
            $order_total = $order->get_total();
            $total_sales += $order_total;

            // Use actual commission rate from database
            $commission = $order_total * $commission_rate;
            $total_commission += $commission;
        }

        // Get commission payments from database
        $commission_table = $wpdb->prefix . 'sst_affiliate_commissions';
        $commission_paid = $wpdb->get_var($wpdb->prepare(
            "SELECT SUM(amount) FROM {$commission_table} WHERE coupon_code = %s AND status = 'paid'",
            $coupon_code
        ));

        $commission_paid = $commission_paid ? floatval($commission_paid) : 0;
        $commission_pending = max(0, $total_commission - $commission_paid);

        return [
            'total_sales' => $total_sales,
            'total_commission' => $total_commission,
            'commission_paid' => $commission_paid,
            'commission_pending' => $commission_pending,
            'order_count' => $order_count
        ];
    }

    /**
     * Get detailed order breakdown for an affiliate
     *
     * @param string $coupon_code Affiliate's coupon code
     * @return array Array of order details
     */
    public function get_affiliate_orders($coupon_code) {
        if (!class_exists('WooCommerce')) {
            return [];
        }

        global $wpdb;

        // Get affiliate commission rate
        $affiliate_table = $wpdb->prefix . 'sst_affiliates';
        $affiliate = $wpdb->get_row($wpdb->prepare(
            "SELECT commission_rate FROM {$affiliate_table} WHERE coupon_code = %s",
            $coupon_code
        ));

        if (!$affiliate) {
            return [];
        }

        $commission_rate = floatval($affiliate->commission_rate) / 100;

        $orders = wc_get_orders([
            'status' => ['completed', 'processing'],
            'limit' => -1,
            'coupon' => $coupon_code
        ]);

        $order_details = [];

        foreach ($orders as $order) {
            $order_id = $order->get_id();
            $order_total = $order->get_total();
            $commission = $order_total * $commission_rate;

            $items = [];
            foreach ($order->get_items() as $item) {
                $product = $item->get_product();
                $items[] = [
                    'name' => $item->get_name(),
                    'quantity' => $item->get_quantity(),
                    'total' => $item->get_total(),
                    'product_id' => $product ? $product->get_id() : 0
                ];
            }

            $order_details[] = [
                'order_id' => $order_id,
                'order_number' => $order->get_order_number(),
                'date' => $order->get_date_created()->format('Y-m-d H:i:s'),
                'total' => $order_total,
                'commission' => $commission,
                'status' => $order->get_status(),
                'customer_email' => $order->get_billing_email(),
                'items' => $items
            ];
        }

        return $order_details;
    }

    /**
     * Record commission payment
     *
     * @param string $affiliate_id Affiliate ID
     * @param string $coupon_code Coupon code
     * @param float $amount Payment amount
     * @param string $notes Payment notes
     * @return int|false Commission ID or false on failure
     */
    public function record_payment($affiliate_id, $coupon_code, $amount, $notes = '') {
        global $wpdb;

        $table_name = $wpdb->prefix . 'sst_affiliate_commissions';

        $data = [
            'affiliate_id' => $affiliate_id,
            'coupon_code' => $coupon_code,
            'amount' => $amount,
            'status' => 'paid',
            'paid_at' => current_time('mysql'),
            'paid_by' => get_current_user_id(),
            'notes' => $notes
        ];

        $result = $wpdb->insert($table_name, $data);

        // Send payment notification email to affiliate
        if ($result && get_option('sst_affiliate_notify_on_payment', '1')) {
            SST_Email_Notifications::send_payment_notification($affiliate_id, $amount, $notes);
        }

        return $result ? $wpdb->insert_id : false;
    }

    /**
     * Get commission payment history
     *
     * @param string $affiliate_id Affiliate ID
     * @return array Payment history
     */
    public function get_payment_history($affiliate_id) {
        global $wpdb;

        $table_name = $wpdb->prefix . 'sst_affiliate_commissions';

        return $wpdb->get_results($wpdb->prepare(
            "SELECT * FROM {$table_name} WHERE affiliate_id = %s ORDER BY paid_at DESC",
            $affiliate_id
        ));
    }

    /**
     * Create commission tracking table
     */
    public static function create_table() {
        global $wpdb;

        $table_name = $wpdb->prefix . 'sst_affiliate_commissions';
        $charset_collate = $wpdb->get_charset_collate();

        $sql = "CREATE TABLE IF NOT EXISTS {$table_name} (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            affiliate_id VARCHAR(20) NOT NULL,
            coupon_code VARCHAR(50) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'paid',
            paid_at DATETIME NOT NULL,
            paid_by BIGINT(20),
            notes TEXT,
            KEY idx_affiliate_id (affiliate_id),
            KEY idx_coupon_code (coupon_code),
            KEY idx_status (status)
        ) {$charset_collate};";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }
}
