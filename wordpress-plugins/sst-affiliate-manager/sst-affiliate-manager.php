<?php
/**
 * Plugin Name: Predictive Safety Affiliate Manager
 * Description: Complete affiliate management system - applications, approvals, referral tracking, commission management, payout tracking, automated email notifications, and WooCommerce coupon generation with smart borough-based codes
 * Version: 2.4
 * Author: Predictive Safety (SST.NYC)
 * Requires at least: 5.0
 * Requires PHP: 7.4
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

// Define plugin constants
define('SST_AFFILIATE_VERSION', '2.4');
define('SST_AFFILIATE_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('SST_AFFILIATE_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main Plugin Class
 */
class SST_Affiliate_Manager {

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        // Activation/Deactivation hooks
        register_activation_hook(__FILE__, [$this, 'activate']);
        register_deactivation_hook(__FILE__, [$this, 'deactivate']);

        // Load dependencies
        $this->load_dependencies();

        // Initialize components
        add_action('plugins_loaded', [$this, 'init']);
    }

    /**
     * Load plugin dependencies
     */
    private function load_dependencies() {
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-database.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-affiliate.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-form-handler.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-zapier.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-qr-generator.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-coupon-manager.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-commission-manager.php';
        require_once SST_AFFILIATE_PLUGIN_DIR . 'includes/class-email-notifications.php';

        // Admin includes
        if (is_admin()) {
            require_once SST_AFFILIATE_PLUGIN_DIR . 'admin/class-admin-dashboard.php';
            require_once SST_AFFILIATE_PLUGIN_DIR . 'admin/class-affiliate-list-table.php';
        }
    }

    /**
     * Initialize plugin components
     */
    public function init() {
        // Initialize database
        SST_Affiliate_Database::get_instance();

        // Initialize form handler
        SST_Affiliate_Form_Handler::get_instance();

        // Initialize Zapier integration (optional)
        SST_Affiliate_Zapier::get_instance();

        // Initialize email notifications
        new SST_Email_Notifications();

        // Initialize admin if in admin area
        if (is_admin()) {
            SST_Affiliate_Admin_Dashboard::get_instance();
        }
    }

    /**
     * Plugin activation
     */
    public function activate() {
        // Create database tables
        SST_Affiliate_Database::create_tables();
        SST_Commission_Manager::create_table();

        // Set default options
        add_option('sst_affiliate_default_commission', '10.00');
        add_option('sst_affiliate_cookie_duration', '60');
        add_option('sst_affiliate_zapier_enabled', '1'); // Enabled by default for backward compatibility
        add_option('sst_affiliate_admin_email', get_option('admin_email'));
        add_option('sst_affiliate_notify_admin', '1');
        add_option('sst_affiliate_notify_applicant', '1');
        add_option('sst_affiliate_notify_on_sale', '1'); // Notify affiliate when coupon is used
        add_option('sst_affiliate_notify_on_payment', '1'); // Notify affiliate when paid

        // Coupon settings
        add_option('sst_affiliate_coupon_enabled', '1');
        add_option('sst_affiliate_coupon_type', 'percent');
        add_option('sst_affiliate_coupon_amount', '10');
        add_option('sst_affiliate_coupon_prefix', 'AFFILIATE');
        add_option('sst_affiliate_coupon_free_shipping', '0');
        add_option('sst_affiliate_coupon_individual_use', '1');
        add_option('sst_affiliate_coupon_expiry', '0'); // 0 = no expiry

        // Banner settings
        add_option('sst_affiliate_banner_enabled', '1');
        add_option('sst_affiliate_banner_message', 'Earn at least 10% commission! Join our affiliate program.');
        add_option('sst_affiliate_banner_button_text', 'Become an Affiliate');
        add_option('sst_affiliate_banner_bg_color', '#667eea');
        add_option('sst_affiliate_banner_text_color', '#ffffff');

        // Flush rewrite rules
        flush_rewrite_rules();
    }

    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Flush rewrite rules
        flush_rewrite_rules();
    }
}

// Initialize the plugin
function sst_affiliate_manager() {
    return SST_Affiliate_Manager::get_instance();
}

// Start the plugin
sst_affiliate_manager();
