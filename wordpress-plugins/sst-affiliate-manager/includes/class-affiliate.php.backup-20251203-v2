<?php
/**
 * Affiliate Model Class
 * Business logic for affiliate operations
 */

if (!defined('ABSPATH')) exit;

class SST_Affiliate {

    private $db;

    public function __construct() {
        $this->db = SST_Affiliate_Database::get_instance();
    }

    /**
     * Create new affiliate application
     */
    public function create($data) {
        // Validate required fields
        if (empty($data['first_name']) || empty($data['last_name']) || empty($data['email']) || empty($data['phone'])) {
            return new WP_Error('missing_fields', 'Required fields are missing');
        }

        // Check if email already exists
        $existing = $this->db->get_affiliate_by_email($data['email']);
        if ($existing) {
            return new WP_Error('duplicate_email', 'An affiliate with this email already exists');
        }

        // Insert into database
        $affiliate_id = $this->db->insert_affiliate($data);

        if (!$affiliate_id) {
            return new WP_Error('insert_failed', 'Failed to create affiliate');
        }

        // Send admin notification if enabled
        if (get_option('sst_affiliate_notify_admin', '1') == '1') {
            $this->send_admin_notification($affiliate_id);
        }

        return $affiliate_id;
    }

    /**
     * Approve affiliate
     */
    public function approve($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        $user_id = get_current_user_id();
        $result = $this->db->update_status($affiliate_id, 'approved', $user_id);

        if ($result === false) {
            return new WP_Error('update_failed', 'Failed to approve affiliate');
        }

        // Generate WooCommerce coupon if enabled
        if (get_option('sst_affiliate_coupon_enabled', '1') == '1') {
            $coupon_manager = new SST_Coupon_Manager();
            $full_name = $affiliate->first_name . ' ' . $affiliate->last_name;
            $coupon_code = $coupon_manager->generate_coupon(
                $affiliate_id,
                $full_name,
                $affiliate->commission_rate,
                $affiliate->first_name,
                $affiliate->last_name
            );

            if (!is_wp_error($coupon_code)) {
                // Store coupon code in affiliate record
                $this->db->update_affiliate($affiliate_id, ['coupon_code' => $coupon_code]);
                error_log('SST Affiliate: Generated coupon ' . $coupon_code . ' for ' . $affiliate_id);
            } else {
                error_log('SST Affiliate: Failed to generate coupon - ' . $coupon_code->get_error_message());
            }
        }

        // Send approval email if enabled
        if (get_option('sst_affiliate_notify_applicant', '1') == '1') {
            $this->send_approval_email($affiliate_id);
        }

        return true;
    }

    /**
     * Reject affiliate
     */
    public function reject($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        $result = $this->db->update_status($affiliate_id, 'rejected');

        if ($result === false) {
            return new WP_Error('update_failed', 'Failed to reject affiliate');
        }

        return true;
    }

    /**
     * Send admin notification for new application
     */
    private function send_admin_notification($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) return;

        $admin_email = get_option('sst_affiliate_admin_email', get_option('admin_email'));
        $subject = '[SST.NYC] New Affiliate Application: ' . $affiliate->first_name . ' ' . $affiliate->last_name;

        $message = "A new affiliate application has been received.\n\n";
        $message .= "Affiliate ID: " . $affiliate->affiliate_id . "\n";
        $message .= "Name: " . $affiliate->first_name . " " . $affiliate->last_name . "\n";
        $message .= "Email: " . $affiliate->email . "\n";
        $message .= "Phone: " . $affiliate->phone . "\n";
        $message .= "Company: " . $affiliate->company . "\n";
        $message .= "How they heard about us: " . $affiliate->referral_source . "\n\n";
        $message .= "Motivation:\n" . $affiliate->motivation . "\n\n";
        $message .= "Review this application:\n";
        $message .= admin_url('admin.php?page=sst-affiliates&action=view&id=' . $affiliate->affiliate_id);

        wp_mail($admin_email, $subject, $message);
    }

    /**
     * Send approval email to affiliate
     */
    private function send_approval_email($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) return;

        $subject = 'Welcome to the SST.NYC Affiliate Program!';

        $message = "Hi " . $affiliate->first_name . ",\n\n";
        $message .= "Congratulations! Your affiliate application has been approved.\n\n";
        $message .= "Your Affiliate Details:\n";
        $message .= "• Affiliate ID: " . $affiliate->affiliate_id . "\n";
        $message .= "• Commission Rate: " . $affiliate->commission_rate . "%\n";
        $message .= "• Referral Link: " . $affiliate->referral_link . "\n\n";

        // Add coupon code if it exists
        $updated_affiliate = $this->db->get_affiliate($affiliate_id);
        if (!empty($updated_affiliate->coupon_code)) {
            $message .= "• Your Coupon Code: " . $updated_affiliate->coupon_code . "\n\n";
        }

        $message .= "How to Get Started:\n";
        $message .= "1. Share your referral link with construction professionals\n";
        $message .= "2. Share your unique coupon code for easy tracking\n";
        $message .= "3. When someone signs up using your link or coupon, you earn commission!\n\n";
        $message .= "Questions? Email support@sst.nyc\n\n";
        $message .= "Best regards,\n";
        $message .= "The Predictive Safety Team\n";
        $message .= "SST.NYC";

        wp_mail($affiliate->email, $subject, $message);
    }

    /**
     * Get affiliate by ID
     */
    public function get($affiliate_id) {
        return $this->db->get_affiliate($affiliate_id);
    }

    /**
     * Update affiliate
     */
    public function update($affiliate_id, $data) {
        return $this->db->update_affiliate($affiliate_id, $data);
    }

    /**
     * Delete affiliate
     */
    public function delete($affiliate_id) {
        return $this->db->delete_affiliate($affiliate_id);
    }

    /**
     * Get all affiliates with filters
     */
    public function get_all($args = []) {
        return $this->db->get_affiliates($args);
    }

    /**
     * Get affiliate count by status
     */
    public function count($status = '') {
        return $this->db->count_affiliates($status);
    }
}
