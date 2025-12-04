<?php
/**
 * Admin Dashboard
 * Main admin interface for affiliate management
 */

if (!defined('ABSPATH')) exit;

class SST_Affiliate_Admin_Dashboard {

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
        add_action('admin_post_sst_approve_affiliate', [$this, 'handle_approve']);
        add_action('admin_post_sst_reject_affiliate', [$this, 'handle_reject']);
        add_action('admin_post_sst_delete_affiliate', [$this, 'handle_delete']);
        add_action('admin_post_sst_update_affiliate', [$this, 'handle_update']);
        add_action('admin_post_sst_save_settings', [$this, 'handle_save_settings']);
        add_action('admin_post_sst_deactivate_affiliate', [$this, 'handle_deactivate']);
        add_action('admin_post_sst_reactivate_affiliate', [$this, 'handle_reactivate']);
        add_action('admin_post_sst_update_commission', [$this, 'handle_update_commission']);
        add_action('admin_post_sst_update_coupon', [$this, 'handle_update_coupon']);
    }

    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_menu_page(
            'SST Affiliates',
            'Affiliates',
            'manage_options',
            'sst-affiliates',
            [$this, 'render_dashboard'],
            'dashicons-groups',
            30
        );

        add_submenu_page(
            'sst-affiliates',
            'All Affiliates',
            'All Affiliates',
            'manage_options',
            'sst-affiliates',
            [$this, 'render_dashboard']
        );

        add_submenu_page(
            'sst-affiliates',
            'Settings',
            'Settings',
            'manage_options',
            'sst-affiliate-settings',
            [$this, 'render_settings']
        );
    }

    /**
     * Enqueue admin assets
     */
    public function enqueue_admin_assets($hook) {
        if (strpos($hook, 'sst-affiliate') === false) {
            return;
        }

        wp_enqueue_style('sst-affiliate-admin', SST_AFFILIATE_PLUGIN_URL . 'admin/css/admin-styles.css', [], SST_AFFILIATE_VERSION);
    }

    /**
     * Render main dashboard
     */
    public function render_dashboard() {
        $action = isset($_GET['action']) ? $_GET['action'] : 'list';
        $affiliate_id = isset($_GET['id']) ? sanitize_text_field($_GET['id']) : '';

        switch ($action) {
            case 'view':
                $this->render_single_affiliate($affiliate_id);
                break;
            default:
                $this->render_affiliate_list();
                break;
        }
    }

    /**
     * Render affiliate list
     */
    private function render_affiliate_list() {
        require_once SST_AFFILIATE_PLUGIN_DIR . 'admin/views/dashboard.php';
    }

    /**
     * Render single affiliate view
     */
    private function render_single_affiliate($affiliate_id) {
        $affiliate_model = new SST_Affiliate();
        $affiliate = $affiliate_model->get($affiliate_id);

        if (!$affiliate) {
            wp_die('Affiliate not found');
        }

        require_once SST_AFFILIATE_PLUGIN_DIR . 'admin/views/affiliate-detail.php';
    }

    /**
     * Render settings page
     */
    public function render_settings() {
        require_once SST_AFFILIATE_PLUGIN_DIR . 'admin/views/settings.php';
    }

    /**
     * Handle approve action
     */
    public function handle_approve() {
        check_admin_referer('sst_approve_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->approve($affiliate_id);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'approved'], wp_get_referer()));
        }
        exit;
    }

    /**
     * Handle reject action
     */
    public function handle_reject() {
        check_admin_referer('sst_reject_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->reject($affiliate_id);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'rejected'], wp_get_referer()));
        }
        exit;
    }

    /**
     * Handle delete action
     */
    public function handle_delete() {
        check_admin_referer('sst_delete_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->delete($affiliate_id);

        wp_redirect(add_query_arg(['message' => 'deleted'], admin_url('admin.php?page=sst-affiliates')));
        exit;
    }

    /**
     * Handle update action
     */
    public function handle_update() {
        check_admin_referer('sst_update_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $update_data = [];

        if (isset($_POST['commission_rate'])) {
            $update_data['commission_rate'] = floatval($_POST['commission_rate']);
        }

        if (isset($_POST['notes'])) {
            $update_data['notes'] = sanitize_textarea_field($_POST['notes']);
        }

        if (isset($_POST['status'])) {
            $update_data['status'] = sanitize_text_field($_POST['status']);
        }

        $affiliate_model = new SST_Affiliate();
        $affiliate_model->update($affiliate_id, $update_data);

        wp_redirect(add_query_arg(['message' => 'updated'], wp_get_referer()));
        exit;
    }

    /**
     * Handle save settings
     */
    public function handle_save_settings() {
        check_admin_referer('sst_affiliate_settings');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        // Save general settings
        update_option('sst_affiliate_default_commission', sanitize_text_field($_POST['default_commission']));
        update_option('sst_affiliate_cookie_duration', absint($_POST['cookie_duration']));
        update_option('sst_affiliate_form_id', sanitize_text_field($_POST['form_id']));

        // Zapier settings
        update_option('sst_affiliate_zapier_enabled', isset($_POST['zapier_enabled']) ? '1' : '0');
        update_option('sst_zapier_webhook_url', sanitize_text_field($_POST['zapier_webhook_url']));

        // Email settings
        update_option('sst_affiliate_admin_email', sanitize_email($_POST['admin_email']));
        update_option('sst_affiliate_notify_admin', isset($_POST['notify_admin']) ? '1' : '0');
        update_option('sst_affiliate_notify_applicant', isset($_POST['notify_applicant']) ? '1' : '0');
        update_option('sst_affiliate_notify_on_sale', isset($_POST['notify_on_sale']) ? '1' : '0');
        update_option('sst_affiliate_notify_on_payment', isset($_POST['notify_on_payment']) ? '1' : '0');

        // Coupon settings
        update_option('sst_affiliate_coupon_enabled', isset($_POST['coupon_enabled']) ? '1' : '0');
        update_option('sst_affiliate_coupon_type', sanitize_text_field($_POST['coupon_type']));
        update_option('sst_affiliate_coupon_amount', floatval($_POST['coupon_amount']));
        update_option('sst_affiliate_coupon_prefix', sanitize_text_field($_POST['coupon_prefix']));
        update_option('sst_affiliate_coupon_free_shipping', isset($_POST['coupon_free_shipping']) ? '1' : '0');
        update_option('sst_affiliate_coupon_individual_use', isset($_POST['coupon_individual_use']) ? '1' : '0');
        update_option('sst_affiliate_coupon_expiry', absint($_POST['coupon_expiry']));

        // Banner settings
        update_option('sst_affiliate_banner_enabled', isset($_POST['banner_enabled']) ? '1' : '0');
        update_option('sst_affiliate_banner_message', sanitize_text_field($_POST['banner_message']));
        update_option('sst_affiliate_banner_button_text', sanitize_text_field($_POST['banner_button_text']));
        update_option('sst_affiliate_banner_bg_color', sanitize_hex_color($_POST['banner_bg_color']));
        update_option('sst_affiliate_banner_text_color', sanitize_hex_color($_POST['banner_text_color']));

        wp_redirect(add_query_arg(['message' => 'saved'], wp_get_referer()));
        exit;
    }

    /**
     * Handle deactivate action
     */
    public function handle_deactivate() {
        check_admin_referer('sst_deactivate_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->deactivate($affiliate_id);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'deactivated'], wp_get_referer()));
        }
        exit;
    }

    /**
     * Handle reactivate action
     */
    public function handle_reactivate() {
        check_admin_referer('sst_reactivate_affiliate');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->reactivate($affiliate_id);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'reactivated'], wp_get_referer()));
        }
        exit;
    }

    /**
     * Handle update commission rate
     */
    public function handle_update_commission() {
        check_admin_referer('sst_update_commission');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';
        $new_rate = isset($_POST['commission_rate']) ? floatval($_POST['commission_rate']) : 10.00;

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->update_commission_rate($affiliate_id, $new_rate);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'commission_updated'], wp_get_referer()));
        }
        exit;
    }

    /**
     * Handle update coupon discount
     */
    public function handle_update_coupon() {
        check_admin_referer('sst_update_coupon');

        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }

        $affiliate_id = isset($_POST['affiliate_id']) ? sanitize_text_field($_POST['affiliate_id']) : '';
        $discount_amount = isset($_POST['discount_amount']) ? floatval($_POST['discount_amount']) : 10.00;
        $discount_type = isset($_POST['discount_type']) ? sanitize_text_field($_POST['discount_type']) : 'percent';

        $affiliate_model = new SST_Affiliate();
        $result = $affiliate_model->update_coupon_discount($affiliate_id, $discount_amount, $discount_type);

        if (is_wp_error($result)) {
            wp_redirect(add_query_arg(['error' => $result->get_error_message()], wp_get_referer()));
        } else {
            wp_redirect(add_query_arg(['message' => 'coupon_updated'], wp_get_referer()));
        }
        exit;
    }

}