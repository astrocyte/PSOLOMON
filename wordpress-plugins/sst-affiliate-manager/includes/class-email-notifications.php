<?php
/**
 * Email Notifications Manager
 * Sends automated emails to affiliates for sales, commissions, and payouts
 */

if (!defined('ABSPATH')) exit;

class SST_Email_Notifications {

    /**
     * Initialize hooks for WooCommerce order events
     */
    public function __construct() {
        // Send notification when order with affiliate coupon is completed
        add_action('woocommerce_order_status_completed', [$this, 'notify_affiliate_on_sale'], 10, 1);
        add_action('woocommerce_order_status_processing', [$this, 'notify_affiliate_on_sale'], 10, 1);
    }

    /**
     * Notify affiliate when someone uses their coupon
     *
     * @param int $order_id WooCommerce order ID
     */
    public function notify_affiliate_on_sale($order_id) {
        if (!get_option('sst_affiliate_notify_on_sale', '1')) {
            return; // Notifications disabled
        }

        $order = wc_get_order($order_id);
        if (!$order) return;

        // Check if order used an affiliate coupon
        $coupons = $order->get_coupon_codes();
        if (empty($coupons)) return;

        global $wpdb;
        $table_name = $wpdb->prefix . 'sst_affiliates';

        foreach ($coupons as $coupon_code) {
            // Find affiliate by coupon code
            $affiliate = $wpdb->get_row($wpdb->prepare(
                "SELECT * FROM {$table_name} WHERE coupon_code = %s",
                $coupon_code
            ));

            if ($affiliate) {
                $this->send_sale_notification($affiliate, $order);
            }
        }
    }

    /**
     * Send sale notification email to affiliate
     *
     * @param object $affiliate Affiliate record
     * @param WC_Order $order WooCommerce order
     */
    private function send_sale_notification($affiliate, $order) {
        $order_total = $order->get_total();
        $commission = $order_total * ($affiliate->commission_rate / 100);

        $subject = '💰 New Sale! You earned $' . number_format($commission, 2) . ' commission';

        $message = "Hi " . $affiliate->first_name . ",\n\n";
        $message .= "Great news! Someone just used your coupon code and completed a purchase.\n\n";
        $message .= "📊 Sale Details:\n";
        $message .= "• Order #: " . $order->get_order_number() . "\n";
        $message .= "• Order Total: $" . number_format($order_total, 2) . "\n";
        $message .= "• Your Commission (" . $affiliate->commission_rate . "%): $" . number_format($commission, 2) . "\n";
        $message .= "• Date: " . $order->get_date_created()->format('F j, Y g:i A') . "\n\n";

        $message .= "📦 Products Purchased:\n";
        foreach ($order->get_items() as $item) {
            $message .= "  - " . $item->get_name() . " x" . $item->get_quantity() . "\n";
        }

        $message .= "\n🎯 Keep sharing your coupon code (" . $affiliate->coupon_code . ") to earn more!\n\n";
        $message .= "Questions? Reply to this email or contact support@sst.nyc\n\n";
        $message .= "Best regards,\n";
        $message .= "The Predictive Safety Team\n";
        $message .= "SST.NYC";

        wp_mail($affiliate->email, $subject, $message);
    }

    /**
     * Send commission payment notification
     *
     * @param string $affiliate_id Affiliate ID
     * @param float $amount Payment amount
     * @param string $notes Payment notes
     */
    public static function send_payment_notification($affiliate_id, $amount, $notes = '') {
        global $wpdb;
        $table_name = $wpdb->prefix . 'sst_affiliates';

        $affiliate = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table_name} WHERE affiliate_id = %s",
            $affiliate_id
        ));

        if (!$affiliate) return;

        // Get updated stats
        $commission_manager = new SST_Commission_Manager();
        $stats = $commission_manager->get_affiliate_stats($affiliate->coupon_code);

        $subject = '💸 Commission Payment: $' . number_format($amount, 2) . ' sent!';

        $message = "Hi " . $affiliate->first_name . ",\n\n";
        $message .= "Your commission payment has been processed!\n\n";
        $message .= "💰 Payment Details:\n";
        $message .= "• Amount Paid: $" . number_format($amount, 2) . "\n";
        $message .= "• Payment Date: " . current_time('F j, Y') . "\n";
        if (!empty($notes)) {
            $message .= "• Notes: " . $notes . "\n";
        }
        $message .= "\n📊 Your Updated Stats:\n";
        $message .= "• Total Sales: $" . number_format($stats['total_sales'], 2) . "\n";
        $message .= "• Total Commission Earned: $" . number_format($stats['total_commission'], 2) . "\n";
        $message .= "• Commission Paid to Date: $" . number_format($stats['commission_paid'], 2) . "\n";
        $message .= "• Commission Pending: $" . number_format($stats['commission_pending'], 2) . "\n\n";

        $message .= "🎯 Keep up the great work!\n\n";
        $message .= "Questions about your payment? Reply to this email or contact support@sst.nyc\n\n";
        $message .= "Best regards,\n";
        $message .= "The Predictive Safety Team\n";
        $message .= "SST.NYC";

        wp_mail($affiliate->email, $subject, $message);
    }

    /**
     * Send monthly commission summary to affiliate
     *
     * @param string $affiliate_id Affiliate ID
     */
    public static function send_monthly_summary($affiliate_id) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'sst_affiliates';

        $affiliate = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table_name} WHERE affiliate_id = %s",
            $affiliate_id
        ));

        if (!$affiliate) return;

        // Get stats
        $commission_manager = new SST_Commission_Manager();
        $stats = $commission_manager->get_affiliate_stats($affiliate->coupon_code);

        // Get this month's orders
        $orders = $commission_manager->get_affiliate_orders($affiliate->coupon_code);
        $current_month = date('Y-m');
        $month_orders = array_filter($orders, function($order) use ($current_month) {
            return strpos($order['date'], $current_month) === 0;
        });

        $month_sales = array_sum(array_column($month_orders, 'total'));
        $month_commission = array_sum(array_column($month_orders, 'commission'));

        $subject = '📈 Your ' . date('F Y') . ' Commission Summary';

        $message = "Hi " . $affiliate->first_name . ",\n\n";
        $message .= "Here's your performance summary for " . date('F Y') . ":\n\n";
        $message .= "📊 This Month:\n";
        $message .= "• Sales: $" . number_format($month_sales, 2) . "\n";
        $message .= "• Commission Earned: $" . number_format($month_commission, 2) . "\n";
        $message .= "• Orders: " . count($month_orders) . "\n\n";

        $message .= "💰 All-Time Stats:\n";
        $message .= "• Total Sales: $" . number_format($stats['total_sales'], 2) . "\n";
        $message .= "• Total Commission: $" . number_format($stats['total_commission'], 2) . "\n";
        $message .= "• Total Orders: " . $stats['order_count'] . "\n";
        $message .= "• Commission Pending: $" . number_format($stats['commission_pending'], 2) . "\n\n";

        $message .= "🎯 Your Coupon: " . $affiliate->coupon_code . "\n";
        $message .= "🔗 Your Referral Link: " . $affiliate->referral_link . "\n\n";

        $message .= "Keep sharing and earning!\n\n";
        $message .= "Best regards,\n";
        $message .= "The Predictive Safety Team\n";
        $message .= "SST.NYC";

        wp_mail($affiliate->email, $subject, $message);
    }
}
