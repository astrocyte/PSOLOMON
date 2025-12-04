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
        // Hook into WPForms
        add_filter('wpforms_frontend_form_data', [$this, 'disable_html5_validation']);
        add_filter('wpforms_frontend_confirmation_message', [$this, 'custom_success_message'], 10, 4);
        add_action('wpforms_process_complete', [$this, 'process_submission'], 10, 4);
    }

    /**
     * Disable HTML5 email validation to allow .nyc domains
     */
    public function disable_html5_validation($form_data) {
        // Check if this is an affiliate form (you can configure form ID in settings)
        $affiliate_form_id = get_option('sst_affiliate_form_id', '5066');

        if (isset($form_data['id']) && $form_data['id'] == $affiliate_form_id) {
            if (isset($form_data['fields'])) {
                foreach ($form_data['fields'] as $field_id => $field) {
                    if ($field['type'] === 'email') {
                        $form_data['fields'][$field_id]['disable_html5'] = true;
                    }
                }
            }
        }
        return $form_data;
    }

    /**
     * Custom success message
     */
    public function custom_success_message($message, $form_data, $fields, $entry_id) {
        $affiliate_form_id = get_option('sst_affiliate_form_id', '5066');

        if ($form_data['id'] != $affiliate_form_id) {
            return $message;
        }

        $first_name = isset($fields[0]['first']) ? esc_html($fields[0]['first']) : 'there';

        $message = '
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
            <h2 style="color: white; margin: 0 0 15px 0; font-size: 28px;">Thank You, ' . $first_name . '!</h2>
            <p style="font-size: 18px; margin: 0 0 20px 0; color: #f0f0f0;">Your affiliate application has been successfully submitted!</p>

            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: white; margin: 0 0 15px 0; font-size: 20px;">What Happens Next?</h3>
                <ul style="list-style: none; padding: 0; margin: 0; text-align: left; max-width: 500px; margin: 0 auto;">
                    <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">✅ Check your email for confirmation</li>
                    <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">⏱️ We\'ll review your application within 2-3 business days</li>
                    <li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">🎁 Once approved, you\'ll receive your affiliate link & QR code</li>
                    <li style="padding: 8px 0;">💰 Start earning at least 10% commission on every referral!</li>
                </ul>
            </div>

            <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
                <p style="margin: 0; font-size: 14px; color: #f0f0f0;">Questions? Email us at <strong>support@sst.nyc</strong></p>
            </div>
        </div>
        ';

        return $message;
    }

    /**
     * Process form submission
     */
    public function process_submission($fields, $entry, $form_data, $entry_id) {
        $affiliate_form_id = get_option('sst_affiliate_form_id', '5066');

        if ($form_data['id'] != $affiliate_form_id) {
            return;
        }

        // Extract data from WPForms fields
        // Field IDs: 0 = Name, 1 = Email, 2 = Phone, 3 = Company, 4 = Referral Source, 5 = Motivation, 6 = Terms
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

        // Log success
        error_log('SST Affiliate: Created affiliate ' . $result);
    }
}
