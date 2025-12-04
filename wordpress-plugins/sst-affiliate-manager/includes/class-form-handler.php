<?php
/**
 * WPForms Integration Handler
 * Processes affiliate form submissions
 */

if (!defined('ABSPATH')) exit;

class SST_Affiliate_Form_Handler {

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        // Hook into WPForms - REMOVED the problematic form_data filter
        add_action('wpforms_process_complete', [$this, 'process_submission'], 10, 4);
    }

    /**
     * Process form submission
     */
    public function process_submission($fields, $entry, $form_data, $entry_id) {
        $affiliate_form_id = get_option('sst_affiliate_form_id', '5066');

        if (!isset($form_data['id']) || absint($form_data['id']) !== absint($affiliate_form_id)) {
            return;
        }

        // Extract data from WPForms fields
        $data = [
            'first_name' => isset($fields[0]['first']) ? $fields[0]['first'] : '',
            'last_name' => isset($fields[0]['last']) ? $fields[0]['last'] : '',
            'email' => isset($fields[1]['value']) ? $fields[1]['value'] : '',
            'phone' => isset($fields[2]['value']) ? $fields[2]['value'] : '',
            'company' => isset($fields[3]['value']) ? $fields[3]['value'] : '',
            'referral_source' => isset($fields[4]['value']) ? $fields[4]['value'] : '',
            'motivation' => isset($fields[5]['value']) ? $fields[5]['value'] : '',
        ];

        // Create affiliate in database
        $affiliate = new SST_Affiliate();
        $result = $affiliate->create($data);

        if (is_wp_error($result)) {
            error_log('SST Affiliate Error: ' . $result->get_error_message());
            return;
        }

        // Send to Zapier if enabled
        if (get_option('sst_affiliate_zapier_enabled', '1') == '1') {
            $zapier = SST_Affiliate_Zapier::get_instance();
            $zapier->send_to_zapier($data, $result, $entry_id);
        }

        error_log('SST Affiliate: Created affiliate ' . $result);
    }
}
