<?php
/**
 * Single Affiliate Detail View - Enhanced
 */

if (!defined('ABSPATH')) exit;

// Display messages
if (isset($_GET['message'])) {
    $message = sanitize_text_field($_GET['message']);
    $messages = [
        'approved' => 'Affiliate approved successfully!',
        'updated' => 'Affiliate updated successfully!',
        'deactivated' => 'Affiliate deactivated successfully. Coupon has been disabled.',
        'reactivated' => 'Affiliate reactivated successfully. Coupon has been re-enabled.',
        'commission_updated' => 'Commission rate updated successfully!',
        'coupon_updated' => 'Coupon discount updated successfully!'
    ];

    if (isset($messages[$message])) {
        echo '<div class="notice notice-success is-dismissible"><p>' . esc_html($messages[$message]) . '</p></div>';
    }
}

if (isset($_GET['error'])) {
    echo '<div class="notice notice-error is-dismissible"><p>' . esc_html($_GET['error']) . '</p></div>';
}

// Get coupon info if exists
$coupon_info = null;
if (!empty($affiliate->coupon_code) && class_exists('WooCommerce')) {
    $coupon_manager = new SST_Coupon_Manager();
    $coupon_info = $coupon_manager->get_coupon_stats($affiliate->coupon_code);
}
?>

<div class="wrap">
    <h1>
        Affiliate: <?php echo esc_html($affiliate->affiliate_id); ?> - <?php echo esc_html($affiliate->first_name . ' ' . $affiliate->last_name); ?>
        <span class="affiliate-status-badge affiliate-status-<?php echo esc_attr($affiliate->status); ?>">
            <?php echo esc_html(ucfirst($affiliate->status)); ?>
        </span>
    </h1>

    <style>
        .affiliate-status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 3px;
            font-size: 13px;
            font-weight: 600;
            margin-left: 10px;
        }
        .affiliate-status-pending { background: #f0ad4e; color: white; }
        .affiliate-status-approved { background: #5cb85c; color: white; }
        .affiliate-status-rejected { background: #d9534f; color: white; }
        .affiliate-status-inactive { background: #6c757d; color: white; }
        .settings-section {
            background: #fff;
            border: 1px solid #ccd0d4;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .settings-section h2 {
            margin-top: 0;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .inline-form {
            display: inline-block;
            margin-left: 10px;
        }
    </style>

    <!-- Main Update Form -->
    <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
        <input type="hidden" name="action" value="sst_update_affiliate">
        <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
        <?php wp_nonce_field('sst_update_affiliate'); ?>

        <table class="form-table">
            <tr>
                <th>Status</th>
                <td>
                    <select name="status">
                        <option value="pending" <?php selected($affiliate->status, 'pending'); ?>>Pending</option>
                        <option value="approved" <?php selected($affiliate->status, 'approved'); ?>>Approved</option>
                        <option value="rejected" <?php selected($affiliate->status, 'rejected'); ?>>Rejected</option>
                        <option value="inactive" <?php selected($affiliate->status, 'inactive'); ?>>Inactive</option>
                    </select>
                    <p class="description">Change status via the form or use action buttons below.</p>
                </td>
            </tr>
        </table>

        <h2>Contact Information</h2>
        <table class="form-table">
            <tr>
                <th>Email</th>
                <td><a href="mailto:<?php echo esc_attr($affiliate->email); ?>"><?php echo esc_html($affiliate->email); ?></a></td>
            </tr>
            <tr>
                <th>Phone</th>
                <td><a href="tel:<?php echo esc_attr($affiliate->phone); ?>"><?php echo esc_html($affiliate->phone); ?></a></td>
            </tr>
            <tr>
                <th>Company</th>
                <td><?php echo esc_html($affiliate->company); ?></td>
            </tr>
        </table>

        <h2>Application Details</h2>
        <table class="form-table">
            <tr>
                <th>How they heard about us</th>
                <td><?php echo esc_html($affiliate->referral_source); ?></td>
            </tr>
            <tr>
                <th>Motivation</th>
                <td><?php echo nl2br(esc_html($affiliate->motivation)); ?></td>
            </tr>
            <tr>
                <th>Applied</th>
                <td><?php echo date('F j, Y \a\t g:i A', strtotime($affiliate->created_at)); ?></td>
            </tr>
            <?php if ($affiliate->status === 'approved' && !empty($affiliate->approved_at)): ?>
            <tr>
                <th>Approved</th>
                <td><?php echo date('F j, Y \a\t g:i A', strtotime($affiliate->approved_at)); ?></td>
            </tr>
            <?php endif; ?>
        </table>

        <h2>Admin Notes</h2>
        <table class="form-table">
            <tr>
                <th>Internal Notes</th>
                <td>
                    <textarea name="notes" rows="5" class="large-text"><?php echo esc_textarea($affiliate->notes); ?></textarea>
                    <p class="description">These notes are only visible to admins.</p>
                </td>
            </tr>
        </table>

        <p class="submit">
            <input type="submit" name="submit" class="button button-primary" value="Save Changes">
        </p>
    </form>

    <!-- Commission Settings Section -->
    <div class="settings-section">
        <h2>💰 Commission Settings</h2>
        <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
            <input type="hidden" name="action" value="sst_update_commission">
            <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
            <?php wp_nonce_field('sst_update_commission'); ?>

            <table class="form-table">
                <tr>
                    <th>Commission Rate</th>
                    <td>
                        <input type="number" name="commission_rate" value="<?php echo esc_attr($affiliate->commission_rate); ?>"
                               step="0.01" min="0" max="100" style="width: 100px;"> %
                        <input type="submit" class="button" value="Update Commission Rate">
                        <p class="description">
                            Current: <strong><?php echo esc_html($affiliate->commission_rate); ?>%</strong>
                            (Default: 10%)
                        </p>
                    </td>
                </tr>
            </table>
        </form>
    </div>

    <!-- Coupon Settings Section -->
    <?php if (!empty($affiliate->coupon_code)): ?>
    <div class="settings-section">
        <h2>🎟️ Coupon Settings</h2>
        <table class="form-table">
            <tr>
                <th>Coupon Code</th>
                <td>
                    <input type="text" value="<?php echo esc_attr($affiliate->coupon_code); ?>" readonly class="regular-text" onclick="this.select()">
                    <button type="button" class="button" onclick="navigator.clipboard.writeText('<?php echo esc_js($affiliate->coupon_code); ?>'); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy', 2000)">Copy</button>
                    <?php if ($coupon_info && $coupon_info['exists']): ?>
                    <a href="<?php echo admin_url('post.php?post=' . wc_get_coupon_id_by_code($affiliate->coupon_code) . '&action=edit'); ?>"
                       class="button" target="_blank">Edit in WooCommerce</a>
                    <?php endif; ?>
                </td>
            </tr>
            <?php if ($coupon_info && $coupon_info['exists']): ?>
            <tr>
                <th>Current Discount</th>
                <td>
                    <strong><?php echo esc_html($coupon_info['amount']); ?><?php echo $coupon_info['discount_type'] === 'percent' ? '%' : ' (fixed)'; ?></strong>
                    <?php if ($coupon_info['expiry_date']): ?>
                        <br><span style="color: <?php echo (strtotime($coupon_info['expiry_date']) < time()) ? '#d63638' : '#666'; ?>;">
                            Expires: <?php echo esc_html($coupon_info['expiry_date']); ?>
                            <?php if (strtotime($coupon_info['expiry_date']) < time()): ?>
                                <strong>(EXPIRED - Coupon Disabled)</strong>
                            <?php endif; ?>
                        </span>
                    <?php endif; ?>
                </td>
            </tr>
            <tr>
                <th>Usage Stats</th>
                <td>
                    <strong><?php echo esc_html($coupon_info['usage_count']); ?></strong> times used
                    <?php if ($coupon_info['usage_limit'] > 0): ?>
                        (Limit: <?php echo esc_html($coupon_info['usage_limit']); ?>)
                    <?php endif; ?>
                </td>
            </tr>
            <tr>
                <th>Update Discount</th>
                <td>
                    <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
                        <input type="hidden" name="action" value="sst_update_coupon">
                        <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
                        <?php wp_nonce_field('sst_update_coupon'); ?>

                        <select name="discount_type">
                            <option value="percent" <?php selected($coupon_info['discount_type'], 'percent'); ?>>Percentage (%)</option>
                            <option value="fixed_cart">Fixed Amount ($)</option>
                        </select>

                        <input type="number" name="discount_amount" value="<?php echo esc_attr($coupon_info['amount']); ?>"
                               step="0.01" min="0" max="100" style="width: 100px;">

                        <input type="submit" class="button" value="Update Coupon Discount">
                    </form>
                </td>
            </tr>
            <?php endif; ?>
        </table>

        <?php
        // Show commission stats if available
        if (class_exists('SST_Commission_Manager')) {
            $commission_manager = new SST_Commission_Manager();
            $stats = $commission_manager->get_affiliate_stats($affiliate->coupon_code);
            if ($stats['total_sales'] > 0):
        ?>
        <h3 style="margin-top: 30px;">Commission Performance</h3>
        <table class="form-table">
            <tr>
                <th>Total Sales</th>
                <td><strong>$<?php echo number_format($stats['total_sales'], 2); ?></strong></td>
            </tr>
            <tr>
                <th>Commission Earned</th>
                <td><strong>$<?php echo number_format($stats['total_commission'], 2); ?></strong></td>
            </tr>
            <tr>
                <th>Commission Paid</th>
                <td><span style="color: #5cb85c; font-weight: bold;">$<?php echo number_format($stats['commission_paid'], 2); ?></span></td>
            </tr>
            <tr>
                <th>Commission Pending</th>
                <td><span style="color: #f0ad4e; font-weight: bold;">$<?php echo number_format($stats['commission_pending'], 2); ?></span></td>
            </tr>
        </table>
        <?php
            endif;
        }
        ?>
    </div>
    <?php elseif ($affiliate->status === 'approved'): ?>
    <div class="settings-section">
        <h2>🎟️ Coupon Settings</h2>
        <p style="color: #d63638; font-weight: bold;">⚠️ Coupon not generated. WooCommerce may not be active or coupon generation failed.</p>
        <p>Coupon codes are automatically generated when you approve an affiliate.</p>
    </div>
    <?php endif; ?>

    <!-- Referral Information -->
    <div class="settings-section">
        <h2>🔗 Referral Information</h2>
        <table class="form-table">
            <tr>
                <th>Referral Link</th>
                <td>
                    <input type="text" value="<?php echo esc_attr($affiliate->referral_link); ?>" readonly class="regular-text" onclick="this.select()">
                    <button type="button" class="button" onclick="navigator.clipboard.writeText('<?php echo esc_js($affiliate->referral_link); ?>'); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy', 2000)">Copy</button>
                </td>
            </tr>
        </table>
    </div>

    <!-- Action Buttons -->
    <div class="settings-section">
        <h2>Actions</h2>

        <?php if ($affiliate->status === 'pending'): ?>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
                <input type="hidden" name="action" value="sst_approve_affiliate">
                <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
                <?php wp_nonce_field('sst_approve_affiliate'); ?>
                <button type="submit" class="button button-primary" style="background: #5cb85c; border-color: #4cae4c;"
                        onclick="return confirm('Approve this affiliate? This will generate their coupon code and send them an email.');">
                    ✅ Approve & Send Email
                </button>
            </form>

            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
                <input type="hidden" name="action" value="sst_reject_affiliate">
                <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
                <?php wp_nonce_field('sst_reject_affiliate'); ?>
                <button type="submit" class="button" style="color: #d63638;"
                        onclick="return confirm('Reject this affiliate application?');">
                    ❌ Reject Application
                </button>
            </form>
        <?php endif; ?>

        <?php if ($affiliate->status === 'approved'): ?>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
                <input type="hidden" name="action" value="sst_deactivate_affiliate">
                <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
                <?php wp_nonce_field('sst_deactivate_affiliate'); ?>
                <button type="submit" class="button" style="background: #6c757d; color: white; border-color: #5a6268;"
                        onclick="return confirm('Deactivate this affiliate? This will:\n• Keep all historical data\n• Disable their coupon code\n• Stop them from earning commissions\n• You can reactivate them later');">
                    💤 Deactivate Affiliate
                </button>
            </form>
        <?php endif; ?>

        <?php if ($affiliate->status === 'inactive'): ?>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block;">
                <input type="hidden" name="action" value="sst_reactivate_affiliate">
                <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
                <?php wp_nonce_field('sst_reactivate_affiliate'); ?>
                <button type="submit" class="button button-primary" style="background: #5cb85c; border-color: #4cae4c;"
                        onclick="return confirm('Reactivate this affiliate? This will:\n• Change status back to Approved\n• Re-enable their coupon code\n• Allow them to earn commissions again');">
                    ✅ Reactivate Affiliate
                </button>
            </form>
        <?php endif; ?>

        <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline-block; margin-left: 20px;">
            <input type="hidden" name="action" value="sst_delete_affiliate">
            <input type="hidden" name="affiliate_id" value="<?php echo esc_attr($affiliate->affiliate_id); ?>">
            <?php wp_nonce_field('sst_delete_affiliate'); ?>
            <button type="submit" class="button" style="color: #a00; border-color: #a00;"
                    onclick="return confirm('⚠️ PERMANENT DELETE\n\nThis will PERMANENTLY delete:\n• All affiliate data\n• Commission history\n• Associated coupon code\n• Referral tracking\n\nThis CANNOT be undone!\n\nConsider using Deactivate instead.\n\nAre you absolutely sure?');">
                🗑️ Delete Permanently
            </button>
        </form>
    </div>

    <p style="margin-top: 30px;">
        <a href="<?php echo admin_url('admin.php?page=sst-affiliates'); ?>" class="button">← Back to All Affiliates</a>
    </p>
</div>
