<?php
/**
 * Admin Dashboard View
 * Displays list of all affiliates
 */

if (!defined('ABSPATH')) exit;

// Display messages
if (isset($_GET['message'])) {
    $message = sanitize_text_field($_GET['message']);
    $messages = [
        'approved' => 'Affiliate approved successfully!',
        'rejected' => 'Affiliate rejected.',
        'deleted' => 'Affiliate deleted.',
        'updated' => 'Affiliate updated successfully!'
    ];

    if (isset($messages[$message])) {
        echo '<div class="notice notice-success is-dismissible"><p>' . esc_html($messages[$message]) . '</p></div>';
    }
}

if (isset($_GET['error'])) {
    echo '<div class="notice notice-error is-dismissible"><p>' . esc_html(sanitize_text_field(wp_unslash($_GET['error']))) . '</p></div>';
}

// Create list table
$list_table = new SST_Affiliate_List_Table();
$list_table->prepare_items();
?>

<div class="wrap">
    <h1 class="wp-heading-inline">SST Affiliate Manager</h1>
    <a href="<?php echo esc_url(home_url('/partner/')); ?>" class="page-title-action" target="_blank">View Application Page</a>
    <hr class="wp-header-end">

    <?php $list_table->views(); ?>

    <form method="get">
        <input type="hidden" name="page" value="sst-affiliates">
        <?php
        $list_table->display();
        ?>
    </form>
</div>

<style>
.wp-list-table .column-affiliate_id {
    width: 90px;
}
.wp-list-table .column-name {
    width: 130px;
}
.wp-list-table .column-email {
    width: 180px;
}
.wp-list-table .column-phone {
    width: 110px;
}
.wp-list-table .column-company {
    width: 120px;
}
.wp-list-table .column-coupon_code {
    width: 110px;
}
.wp-list-table .column-coupon_usage {
    width: 50px;
    text-align: center;
}
.wp-list-table .column-commission_rate {
    width: 70px;
}
.wp-list-table .column-status {
    width: 90px;
}
.wp-list-table .column-created_at {
    width: 90px;
}
</style>
