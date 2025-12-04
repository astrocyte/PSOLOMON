<?php
/**
 * QR Code Generator
 * Generates QR codes for affiliate referral links
 */

if (!defined('ABSPATH')) exit;

class SST_QR_Generator {

    private $upload_dir;

    public function __construct() {
        $upload = wp_upload_dir();
        $this->upload_dir = $upload['basedir'] . '/sst-qr-codes';

        // Create directory if it doesn't exist
        if (!file_exists($this->upload_dir)) {
            wp_mkdir_p($this->upload_dir);
        }
    }

    /**
     * Generate QR code for referral link
     * Using Google Charts API as simple solution (no PHP dependencies needed)
     */
    public function generate($url, $affiliate_id) {
        $filename = 'qr-' . $affiliate_id . '.png';
        $filepath = $this->upload_dir . '/' . $filename;

        // Use Google Charts API to generate QR code
        $qr_url = 'https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=' . urlencode($url) . '&choe=UTF-8';

        // Download QR code image
        $response = wp_remote_get($qr_url, ['timeout' => 30]);

        if (is_wp_error($response)) {
            error_log('QR Code generation error: ' . $response->get_error_message());
            return false;
        }

        $image_data = wp_remote_retrieve_body($response);

        if (empty($image_data)) {
            error_log('QR Code generation: Empty response');
            return false;
        }

        // Save to file
        $result = file_put_contents($filepath, $image_data);

        if ($result === false) {
            error_log('QR Code save error: Could not write to ' . $filepath);
            return false;
        }

        return $filepath;
    }

    /**
     * Get QR code URL
     */
    public function get_qr_url($qr_code_path) {
        if (empty($qr_code_path) || !file_exists($qr_code_path)) {
            return false;
        }

        $upload = wp_upload_dir();
        $url = str_replace($upload['basedir'], $upload['baseurl'], $qr_code_path);
        return $url;
    }

    /**
     * Delete QR code
     */
    public function delete($qr_code_path) {
        if (!empty($qr_code_path) && file_exists($qr_code_path)) {
            return unlink($qr_code_path);
        }
        return false;
    }
}
