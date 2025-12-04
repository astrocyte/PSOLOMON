<?php
/**
 * Affiliate Model Class - Enhanced Version
 * Business logic for affiliate operations with deactivation and custom settings
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

            // Use custom commission rate if set, otherwise use default
            $commission_rate = !empty($affiliate->commission_rate) ? $affiliate->commission_rate : 10.00;

            $coupon_code = $coupon_manager->generate_coupon(
                $affiliate_id,
                $full_name,
                $commission_rate,
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
     * Deactivate affiliate
     * Preserves data and history but disables active participation
     */
    public function deactivate($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        // Update status to inactive
        $result = $this->db->update_status($affiliate_id, 'inactive');

        if ($result === false) {
            return new WP_Error('update_failed', 'Failed to deactivate affiliate');
        }

        // Disable the WooCommerce coupon (don't delete it)
        if (!empty($affiliate->coupon_code)) {
            $coupon_manager = new SST_Coupon_Manager();
            $coupon_manager->disable_coupon($affiliate->coupon_code);
            error_log('SST Affiliate: Disabled coupon ' . $affiliate->coupon_code . ' for ' . $affiliate_id);
        }

        return true;
    }

    /**
     * Reactivate affiliate
     * Re-enables a previously deactivated affiliate
     */
    public function reactivate($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        if ($affiliate->status !== 'inactive') {
            return new WP_Error('invalid_status', 'Only inactive affiliates can be reactivated');
        }

        // Update status back to approved
        $result = $this->db->update_status($affiliate_id, 'approved');

        if ($result === false) {
            return new WP_Error('update_failed', 'Failed to reactivate affiliate');
        }

        // Re-enable the WooCommerce coupon
        if (!empty($affiliate->coupon_code)) {
            $coupon_manager = new SST_Coupon_Manager();
            $coupon_manager->enable_coupon($affiliate->coupon_code);
            error_log('SST Affiliate: Re-enabled coupon ' . $affiliate->coupon_code . ' for ' . $affiliate_id);
        }

        return true;
    }

    /**
     * Update commission rate for specific affiliate
     *
     * @param string $affiliate_id The affiliate ID
     * @param float $new_rate New commission rate (e.g., 15.50 for 15.5%)
     * @return bool|WP_Error Success or error
     */
    public function update_commission_rate($affiliate_id, $new_rate) {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        // Validate rate (0-100)
        if ($new_rate < 0 || $new_rate > 100) {
            return new WP_Error('invalid_rate', 'Commission rate must be between 0 and 100');
        }

        $result = $this->db->update_affiliate($affiliate_id, [
            'commission_rate' => $new_rate
        ]);

        if ($result === false) {
            return new WP_Error('update_failed', 'Failed to update commission rate');
        }

        error_log(sprintf('SST Affiliate: Updated commission rate for %s to %.2f%%', $affiliate_id, $new_rate));
        return true;
    }

    /**
     * Update coupon discount for specific affiliate
     *
     * @param string $affiliate_id The affiliate ID
     * @param float $new_discount New discount amount
     * @param string $discount_type Type: 'percent' or 'fixed_cart'
     * @return bool|WP_Error Success or error
     */
    public function update_coupon_discount($affiliate_id, $new_discount, $discount_type = 'percent') {
        $affiliate = $this->db->get_affiliate($affiliate_id);
        if (!$affiliate) {
            return new WP_Error('not_found', 'Affiliate not found');
        }

        if (empty($affiliate->coupon_code)) {
            return new WP_Error('no_coupon', 'This affiliate does not have a coupon code');
        }

        // Validate discount
        if ($new_discount < 0) {
            return new WP_Error('invalid_discount', 'Discount must be positive');
        }

        if ($discount_type === 'percent' && $new_discount > 100) {
            return new WP_Error('invalid_discount', 'Percentage discount cannot exceed 100%');
        }

        // Update the WooCommerce coupon
        $coupon_manager = new SST_Coupon_Manager();
        $result = $coupon_manager->update_coupon($affiliate->coupon_code, $new_discount, $discount_type);

        if (is_wp_error($result)) {
            return $result;
        }

        error_log(sprintf('SST Affiliate: Updated coupon %s for %s to %.2f %s',
            $affiliate->coupon_code, $affiliate_id, $new_discount, $discount_type));

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
     * Delete affiliate (permanent - use deactivate() instead for safety)
     */
    public function delete($affiliate_id) {
        $affiliate = $this->db->get_affiliate($affiliate_id);

        // Delete associated coupon if it exists
        if ($affiliate && !empty($affiliate->coupon_code)) {
            $coupon_manager = new SST_Coupon_Manager();
            $coupon_manager->delete_coupon($affiliate->coupon_code);
            error_log('SST Affiliate: Deleted coupon ' . $affiliate->coupon_code . ' for ' . $affiliate_id);
        }

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
