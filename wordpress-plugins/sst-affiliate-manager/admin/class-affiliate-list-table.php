<?php
/**
 * Affiliate List Table
 * WordPress-style table for displaying affiliates
 */

if (!defined('ABSPATH')) exit;

if (!class_exists('WP_List_Table')) {
    require_once(ABSPATH . 'wp-admin/includes/class-wp-list-table.php');
}

class SST_Affiliate_List_Table extends WP_List_Table {

    private $affiliate_model;

    public function __construct() {
        parent::__construct([
            'singular' => 'affiliate',
            'plural' => 'affiliates',
            'ajax' => false
        ]);

        $this->affiliate_model = new SST_Affiliate();
    }

    /**
     * Get columns
     */
    public function get_columns() {
        return [
            'cb' => '<input type="checkbox" />',
            'affiliate_id' => 'Affiliate ID',
            'name' => 'Name',
            'email' => 'Email',
            'phone' => 'Phone',
            'company' => 'Company',
            'coupon_code' => 'Coupon Code',
            'coupon_usage' => 'Uses',
            'commission_rate' => 'Commission',
            'status' => 'Status',
            'created_at' => 'Applied'
        ];
    }

    /**
     * Get sortable columns
     */
    public function get_sortable_columns() {
        return [
            'affiliate_id' => ['affiliate_id', false],
            'name' => ['first_name', false],
            'email' => ['email', false],
            'status' => ['status', false],
            'created_at' => ['created_at', true] // true = already sorted
        ];
    }

    /**
     * Column default
     */
    public function column_default($item, $column_name) {
        return isset($item->$column_name) ? esc_html($item->$column_name) : '—';
    }

    /**
     * Column checkbox
     */
    public function column_cb($item) {
        return sprintf('<input type="checkbox" name="affiliate[]" value="%s" />', $item->affiliate_id);
    }

    /**
     * Column Affiliate ID
     */
    public function column_affiliate_id($item) {
        $view_url = add_query_arg([
            'page' => 'sst-affiliates',
            'action' => 'view',
            'id' => $item->affiliate_id
        ], admin_url('admin.php'));

        return sprintf('<strong><a href="%s">%s</a></strong>', esc_url($view_url), esc_html($item->affiliate_id));
    }

    /**
     * Column Name
     */
    public function column_name($item) {
        $name = esc_html($item->first_name . ' ' . $item->last_name);
        $view_url = add_query_arg([
            'page' => 'sst-affiliates',
            'action' => 'view',
            'id' => $item->affiliate_id
        ], admin_url('admin.php'));

        return sprintf('<a href="%s">%s</a>', esc_url($view_url), $name);
    }

    /**
     * Column Coupon Code
     */
    public function column_coupon_code($item) {
        if (empty($item->coupon_code)) {
            return '<span style="color: #999;">—</span>';
        }

        $coupon_id = wc_get_coupon_id_by_code($item->coupon_code);
        if ($coupon_id) {
            $edit_url = admin_url('post.php?post=' . $coupon_id . '&action=edit');
            return sprintf(
                '<code style="background: #f0f0f1; padding: 2px 6px; border-radius: 3px;">%s</code> <a href="%s" target="_blank" title="Edit in WooCommerce"><span class="dashicons dashicons-edit" style="font-size: 14px; vertical-align: middle;"></span></a>',
                esc_html($item->coupon_code),
                esc_url($edit_url)
            );
        }

        return '<code style="background: #f0f0f1; padding: 2px 6px; border-radius: 3px;">' . esc_html($item->coupon_code) . '</code>';
    }

    /**
     * Column Coupon Usage
     */
    public function column_coupon_usage($item) {
        if (empty($item->coupon_code)) {
            return '<span style="color: #999;">—</span>';
        }

        if (!class_exists('WooCommerce')) {
            return '<span style="color: #999;">—</span>';
        }

        $coupon = new WC_Coupon($item->coupon_code);
        if (!$coupon->get_id()) {
            return '<span style="color: #999;">0</span>';
        }

        $usage_count = $coupon->get_usage_count();
        return '<strong>' . esc_html($usage_count) . '</strong>';
    }

    /**
     * Column Commission Rate
     */
    public function column_commission_rate($item) {
        return esc_html($item->commission_rate) . '%';
    }

    /**
     * Column Status
     */
    public function column_status($item) {
        $status_colors = [
            'pending' => '#f0ad4e',
            'approved' => '#5cb85c',
            'rejected' => '#d9534f'
        ];

        $color = isset($status_colors[$item->status]) ? $status_colors[$item->status] : '#999';
        return sprintf(
            '<span style="display: inline-block; padding: 4px 10px; border-radius: 12px; background: %s; color: white; font-size: 11px; font-weight: bold; text-transform: uppercase;">%s</span>',
            $color,
            esc_html($item->status)
        );
    }

    /**
     * Column Created At
     */
    public function column_created_at($item) {
        $date = new DateTime($item->created_at);
        return $date->format('M j, Y');
    }

    /**
     * Get views (status filters)
     */
    public function get_views() {
        $current_status = isset($_GET['status']) ? $_GET['status'] : '';

        $total = $this->affiliate_model->count();
        $pending = $this->affiliate_model->count('pending');
        $approved = $this->affiliate_model->count('approved');
        $rejected = $this->affiliate_model->count('rejected');

        $views = [];

        $views['all'] = sprintf(
            '<a href="%s" class="%s">All <span class="count">(%d)</span></a>',
            admin_url('admin.php?page=sst-affiliates'),
            $current_status === '' ? 'current' : '',
            $total
        );

        $views['pending'] = sprintf(
            '<a href="%s" class="%s">Pending <span class="count">(%d)</span></a>',
            add_query_arg('status', 'pending', admin_url('admin.php?page=sst-affiliates')),
            $current_status === 'pending' ? 'current' : '',
            $pending
        );

        $views['approved'] = sprintf(
            '<a href="%s" class="%s">Approved <span class="count">(%d)</span></a>',
            add_query_arg('status', 'approved', admin_url('admin.php?page=sst-affiliates')),
            $current_status === 'approved' ? 'current' : '',
            $approved
        );

        $views['rejected'] = sprintf(
            '<a href="%s" class="%s">Rejected <span class="count">(%d)</span></a>',
            add_query_arg('status', 'rejected', admin_url('admin.php?page=sst-affiliates')),
            $current_status === 'rejected' ? 'current' : '',
            $rejected
        );

        return $views;
    }

    /**
     * Prepare items
     */
    public function prepare_items() {
        $per_page = 20;
        $current_page = $this->get_pagenum();
        $status = isset($_GET['status']) ? sanitize_text_field($_GET['status']) : '';

        // Get sorting
        $orderby = isset($_GET['orderby']) ? sanitize_text_field($_GET['orderby']) : 'created_at';
        $order = isset($_GET['order']) ? sanitize_text_field($_GET['order']) : 'DESC';

        // Get affiliates
        $args = [
            'status' => $status,
            'orderby' => $orderby,
            'order' => $order,
            'limit' => $per_page,
            'offset' => ($current_page - 1) * $per_page
        ];

        $this->items = $this->affiliate_model->get_all($args);

        // Set pagination
        $total_items = $this->affiliate_model->count($status);

        $this->set_pagination_args([
            'total_items' => $total_items,
            'per_page' => $per_page,
            'total_pages' => ceil($total_items / $per_page)
        ]);

        // Set columns
        $this->_column_headers = [
            $this->get_columns(),
            [],
            $this->get_sortable_columns()
        ];
    }
}
