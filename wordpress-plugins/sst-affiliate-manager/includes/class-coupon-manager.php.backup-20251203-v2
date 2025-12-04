<?php
/**
 * WooCommerce Coupon Manager
 * Generates unique coupon codes for affiliates
 */

if (!defined('ABSPATH')) exit;

class SST_Coupon_Manager {

    /**
     * Generate coupon for affiliate
     *
     * @param string $affiliate_id Affiliate ID (e.g., AFF-001)
     * @param string $affiliate_name Full name for coupon description
     * @param float $commission_rate Commission percentage (e.g., 10.00)
     * @param string $first_name Affiliate first name
     * @param string $last_name Affiliate last name
     * @return string|WP_Error Coupon code or error
     */
    public function generate_coupon($affiliate_id, $affiliate_name, $commission_rate = 10.00, $first_name = '', $last_name = '') {
        // Check if WooCommerce is active
        if (!class_exists('WooCommerce')) {
            return new WP_Error('woocommerce_inactive', 'WooCommerce is not active');
        }

        // Generate coupon code (e.g., PS-JS25)
        $coupon_code = $this->generate_coupon_code($affiliate_id, $first_name, $last_name);

        // Check if coupon already exists
        $existing_coupon = $this->get_coupon_by_code($coupon_code);
        if ($existing_coupon) {
            return $coupon_code; // Return existing coupon
        }

        // Get settings
        $discount_type = get_option('sst_affiliate_coupon_type', 'percent'); // percent or fixed_cart
        $discount_amount = get_option('sst_affiliate_coupon_amount', '10');
        $free_shipping = get_option('sst_affiliate_coupon_free_shipping', '0');
        $individual_use = get_option('sst_affiliate_coupon_individual_use', '1');

        // Create WooCommerce coupon
        $coupon = new WC_Coupon();
        $coupon->set_code($coupon_code);
        $coupon->set_description(sprintf('Affiliate coupon for %s (%s) - %s%% commission', $affiliate_name, $affiliate_id, $commission_rate));
        $coupon->set_discount_type($discount_type);
        $coupon->set_amount($discount_amount);
        $coupon->set_individual_use($individual_use == '1');
        $coupon->set_usage_limit(0); // Unlimited uses
        $coupon->set_usage_limit_per_user(1); // One per customer
        $coupon->set_free_shipping($free_shipping == '1');

        // Set expiry if configured
        $expiry_days = get_option('sst_affiliate_coupon_expiry', '0');
        if ($expiry_days > 0) {
            $expiry_date = date('Y-m-d', strtotime("+{$expiry_days} days"));
            $coupon->set_date_expires($expiry_date);
        }

        // Save coupon
        $coupon_id = $coupon->save();

        if (!$coupon_id) {
            return new WP_Error('coupon_creation_failed', 'Failed to create coupon');
        }

        // Log coupon creation
        error_log(sprintf('SST Affiliate: Created coupon %s for %s', $coupon_code, $affiliate_id));

        return $coupon_code;
    }

    /**
     * Generate coupon code from affiliate name and year
     * Format: PS-JS25 (Predictive Safety - John Smith - 2025)
     * If duplicate initials exist, use borough codes: NYC, BK, BX, QN, SI
     */
    private function generate_coupon_code($affiliate_id, $first_name = '', $last_name = '') {
        // Get current year (last 2 digits)
        $year = date('y');

        // Get initials
        $first_initial = strtoupper(substr($first_name, 0, 1));
        $last_initial = strtoupper(substr($last_name, 0, 1));
        $initials = $first_initial . $last_initial;

        // Try PS prefix first
        $borough_prefixes = ['PS', 'NYC', 'BK', 'BX', 'QN', 'SI'];

        foreach ($borough_prefixes as $prefix) {
            $coupon_code = $prefix . '-' . $initials . $year;

            // Check if this code already exists
            if (!$this->coupon_code_exists($coupon_code)) {
                return $coupon_code;
            }
        }

        // Fallback: If all borough codes are taken, append number
        $counter = 1;
        while ($counter < 100) {
            $coupon_code = 'PS-' . $initials . $year . '-' . $counter;
            if (!$this->coupon_code_exists($coupon_code)) {
                return $coupon_code;
            }
            $counter++;
        }

        // Last resort: use affiliate ID
        return 'PS-' . str_replace('-', '', $affiliate_id);
    }

    /**
     * Check if coupon code already exists
     */
    private function coupon_code_exists($code) {
        $coupon_id = wc_get_coupon_id_by_code($code);
        return $coupon_id > 0;
    }

    /**
     * Get coupon by code
     */
    public function get_coupon_by_code($code) {
        $coupon_id = wc_get_coupon_id_by_code($code);
        if ($coupon_id) {
            return new WC_Coupon($coupon_id);
        }
        return false;
    }

    /**
     * Get coupon for affiliate by coupon code
     * Note: Since we no longer deterministically generate codes from affiliate_id alone,
     * you should store and retrieve the coupon_code from the affiliate record
     */
    public function get_affiliate_coupon($coupon_code) {
        return $this->get_coupon_by_code($coupon_code);
    }

    /**
     * Update coupon discount amount
     */
    public function update_coupon_amount($coupon_code, $new_amount) {
        $coupon = $this->get_coupon_by_code($coupon_code);

        if (!$coupon) {
            return new WP_Error('coupon_not_found', 'Coupon not found');
        }

        $coupon->set_amount($new_amount);
        $coupon->save();

        return true;
    }

    /**
     * Delete coupon by code
     */
    public function delete_coupon($coupon_code) {
        $coupon = $this->get_coupon_by_code($coupon_code);

        if ($coupon) {
            $coupon->delete(true); // Force delete
            return true;
        }

        return false;
    }

    /**
     * Get coupon usage stats
     */
    public function get_coupon_stats($coupon_code) {
        $coupon = $this->get_coupon_by_code($coupon_code);

        if (!$coupon) {
            return [
                'exists' => false,
                'usage_count' => 0,
                'usage_limit' => 0,
                'amount' => 0
            ];
        }

        return [
            'exists' => true,
            'code' => $coupon_code,
            'usage_count' => $coupon->get_usage_count(),
            'usage_limit' => $coupon->get_usage_limit(),
            'amount' => $coupon->get_amount(),
            'discount_type' => $coupon->get_discount_type(),
            'expiry_date' => $coupon->get_date_expires() ? $coupon->get_date_expires()->date('Y-m-d') : null
        ];
    }

    /**
     * Extract first and last name from full name
     * Helper method to split "John Smith" into ["John", "Smith"]
     */
    private function parse_full_name($full_name) {
        $parts = explode(' ', trim($full_name), 2);
        return [
            'first_name' => $parts[0] ?? '',
            'last_name' => $parts[1] ?? ''
        ];
    }

    /**
     * Check if WooCommerce is active
     */
    public function is_woocommerce_active() {
        return class_exists('WooCommerce');
    }
}
