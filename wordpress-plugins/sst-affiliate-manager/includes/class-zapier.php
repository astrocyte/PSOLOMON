<?php
/**
 * Zapier Integration (Optional)
 * Sends affiliate data to Zapier webhook
 */

if (!defined('ABSPATH')) exit;

class SST_Affiliate_Zapier {

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        // No hooks needed - called manually when enabled
    }

    /**
     * Send affiliate data to Zapier
     */
    public function send_to_zapier($data, $affiliate_id, $entry_id = null) {
        // Check if Zapier is enabled
        if (get_option('sst_affiliate_zapier_enabled', '1') != '1') {
            return;
        }

        $webhook_url = get_option('sst_zapier_webhook_url', '');

        if (empty($webhook_url)) {
            error_log('SST Affiliate: Zapier enabled but no webhook URL configured');
            return;
        }

        // Prepare payload
        $payload = [
            'affiliate_id' => $affiliate_id,
            'entry_id' => $entry_id,
            'timestamp' => current_time('mysql'),
            'first_name' => $data['first_name'],
            'last_name' => $data['last_name'],
            'email' => $data['email'],
            'phone' => $data['phone'],
            'company' => $data['company'],
            'referral_source' => $data['referral_source'],
            'motivation' => $data['motivation'],
            'site_url' => get_site_url()
        ];

        // Send to Zapier
        $response = wp_remote_post($webhook_url, [
            'method' => 'POST',
            'timeout' => 15,
            'headers' => [
                'Content-Type' => 'application/json',
            ],
            'body' => json_encode($payload),
        ]);

        // Log errors
        if (is_wp_error($response)) {
            error_log('SST Affiliate Zapier Error: ' . $response->get_error_message());
        } else {
            $status_code = wp_remote_retrieve_response_code($response);
            if ($status_code != 200) {
                error_log('SST Affiliate Zapier: Received status code ' . $status_code);
            } else {
                error_log('SST Affiliate: Sent to Zapier successfully - ' . $affiliate_id);
            }
        }
    }
}
