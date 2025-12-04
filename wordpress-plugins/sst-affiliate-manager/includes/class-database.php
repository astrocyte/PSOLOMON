<?php
/**
 * Database Management Class
 * Handles all database operations for affiliate management
 */

if (!defined('ABSPATH')) exit;

class SST_Affiliate_Database {

    private static $instance = null;
    private $table_affiliates;
    private $table_referrals;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        global $wpdb;
        $this->table_affiliates = $wpdb->prefix . 'sst_affiliates';
        $this->table_referrals = $wpdb->prefix . 'sst_affiliate_referrals';
    }

    /**
     * Create database tables
     */
    public static function create_tables() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();

        $table_affiliates = $wpdb->prefix . 'sst_affiliates';
        $table_referrals = $wpdb->prefix . 'sst_affiliate_referrals';

        $sql_affiliates = "CREATE TABLE IF NOT EXISTS $table_affiliates (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            affiliate_id VARCHAR(20) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            company VARCHAR(200),
            referral_source VARCHAR(100),
            motivation TEXT,
            referral_link VARCHAR(255) UNIQUE,
            qr_code_path VARCHAR(255),
            coupon_code VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            commission_rate DECIMAL(5,2) DEFAULT 10.00,
            created_at DATETIME NOT NULL,
            approved_at DATETIME,
            approved_by BIGINT(20),
            notes TEXT,
            KEY idx_affiliate_id (affiliate_id),
            KEY idx_email (email),
            KEY idx_status (status),
            KEY idx_coupon (coupon_code)
        ) $charset_collate;";

        $sql_referrals = "CREATE TABLE IF NOT EXISTS $table_referrals (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            affiliate_id VARCHAR(20) NOT NULL,
            student_email VARCHAR(100),
            course_id BIGINT(20),
            order_id BIGINT(20),
            commission_amount DECIMAL(10,2),
            commission_status VARCHAR(20) DEFAULT 'pending',
            referred_at DATETIME NOT NULL,
            converted_at DATETIME,
            KEY idx_affiliate_id (affiliate_id),
            KEY idx_status (commission_status)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql_affiliates);
        dbDelta($sql_referrals);

        // Update database version
        update_option('sst_affiliate_db_version', SST_AFFILIATE_VERSION);
    }

    /**
     * Get next affiliate ID
     */
    public function get_next_affiliate_id() {
        global $wpdb;
        // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared -- table name is internally controlled, not user input
        $last_id = $wpdb->get_var("SELECT MAX(CAST(SUBSTRING(affiliate_id, 5) AS UNSIGNED)) FROM {$this->table_affiliates}");
        $next_num = $last_id ? ($last_id + 1) : 1;
        return sprintf('AFF-%03d', $next_num);
    }

    /**
     * Insert new affiliate
     */
    public function insert_affiliate($data) {
        global $wpdb;

        $affiliate_id = $this->get_next_affiliate_id();
        $referral_link = home_url('/?ref=' . $affiliate_id);

        $insert_data = [
            'affiliate_id' => $affiliate_id,
            'first_name' => sanitize_text_field($data['first_name']),
            'last_name' => sanitize_text_field($data['last_name']),
            'email' => sanitize_email($data['email']),
            'phone' => sanitize_text_field($data['phone']),
            'company' => isset($data['company']) ? sanitize_text_field($data['company']) : '',
            'referral_source' => isset($data['referral_source']) ? sanitize_text_field($data['referral_source']) : '',
            'motivation' => isset($data['motivation']) ? sanitize_textarea_field($data['motivation']) : '',
            'referral_link' => $referral_link,
            'status' => 'pending',
            'commission_rate' => get_option('sst_affiliate_default_commission', '10.00'),
            'created_at' => current_time('mysql')
        ];

        $result = $wpdb->insert($this->table_affiliates, $insert_data);

        if ($result) {
            return $affiliate_id;
        }

        return false;
    }

    /**
     * Get affiliate by ID
     */
    public function get_affiliate($affiliate_id) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$this->table_affiliates} WHERE affiliate_id = %s",
            $affiliate_id
        ));
    }

    /**
     * Get affiliate by email
     */
    public function get_affiliate_by_email($email) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$this->table_affiliates} WHERE email = %s",
            $email
        ));
    }

    /**
     * Update affiliate
     */
    public function update_affiliate($affiliate_id, $data) {
        global $wpdb;
        return $wpdb->update(
            $this->table_affiliates,
            $data,
            ['affiliate_id' => $affiliate_id]
        );
    }

    /**
     * Update affiliate status
     */
    public function update_status($affiliate_id, $status, $user_id = null) {
        global $wpdb;

        $update_data = [
            'status' => $status
        ];

        if ($status === 'approved' && $user_id) {
            $update_data['approved_at'] = current_time('mysql');
            $update_data['approved_by'] = $user_id;
        }

        return $wpdb->update(
            $this->table_affiliates,
            $update_data,
            ['affiliate_id' => $affiliate_id]
        );
    }

    /**
     * Get affiliates with filters
     */
    public function get_affiliates($args = []) {
        global $wpdb;

        $defaults = [
            'status' => '',
            'orderby' => 'created_at',
            'order' => 'DESC',
            'limit' => 20,
            'offset' => 0
        ];

        $args = wp_parse_args($args, $defaults);

        $where = "1=1";
        if (!empty($args['status'])) {
            $where .= $wpdb->prepare(" AND status = %s", $args['status']);
        }

        $orderby = sanitize_sql_orderby($args['orderby'] . ' ' . $args['order']);
        $limit = absint($args['limit']);
        $offset = absint($args['offset']);

        $query = "SELECT * FROM {$this->table_affiliates}
                  WHERE $where
                  ORDER BY $orderby
                  LIMIT $limit OFFSET $offset";

        return $wpdb->get_results($query);
    }

    /**
     * Get affiliate count by status
     */
    public function count_affiliates($status = '') {
        global $wpdb;

        if (empty($status)) {
            return $wpdb->get_var("SELECT COUNT(*) FROM {$this->table_affiliates}");
        }

        return $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM {$this->table_affiliates} WHERE status = %s",
            $status
        ));
    }

    /**
     * Delete affiliate
     */
    public function delete_affiliate($affiliate_id) {
        global $wpdb;
        return $wpdb->delete($this->table_affiliates, ['affiliate_id' => $affiliate_id]);
    }

    /**
     * Get table name for affiliates
     */
    public function get_table_name() {
        return $this->table_affiliates;
    }
}
