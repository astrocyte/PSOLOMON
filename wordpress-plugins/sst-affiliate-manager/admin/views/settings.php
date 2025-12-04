<?php
/**
 * Settings Page View
 */

if (!defined('ABSPATH')) exit;

// Display message
if (isset($_GET['message']) && $_GET['message'] === 'saved') {
    echo '<div class="notice notice-success is-dismissible"><p>Settings saved successfully!</p></div>';
}

// Get current settings
$default_commission = get_option('sst_affiliate_default_commission', '10.00');
$cookie_duration = get_option('sst_affiliate_cookie_duration', '60');
$form_id = get_option('sst_affiliate_form_id', '5066');
$zapier_enabled = get_option('sst_affiliate_zapier_enabled', '1');
$zapier_webhook_url = get_option('sst_zapier_webhook_url', '');
$admin_email = get_option('sst_affiliate_admin_email', get_option('admin_email'));
$notify_admin = get_option('sst_affiliate_notify_admin', '1');
$notify_applicant = get_option('sst_affiliate_notify_applicant', '1');
?>

<div class="wrap">
    <h1>SST Affiliate Manager Settings</h1>

    <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
        <input type="hidden" name="action" value="sst_save_settings">
        <?php wp_nonce_field('sst_affiliate_settings'); ?>

        <h2>General Settings</h2>
        <table class="form-table">
            <tr>
                <th scope="row">
                    <label for="default_commission">Default Commission Rate</label>
                </th>
                <td>
                    <input type="number" id="default_commission" name="default_commission" value="<?php echo esc_attr($default_commission); ?>" step="0.01" min="0" max="100" class="small-text">%
                    <p class="description">New affiliates will start with this commission rate. You can adjust individual rates later.</p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="cookie_duration">Referral Cookie Duration</label>
                </th>
                <td>
                    <input type="number" id="cookie_duration" name="cookie_duration" value="<?php echo esc_attr($cookie_duration); ?>" min="1" max="365" class="small-text"> days
                    <p class="description">How long to track referrals after someone clicks an affiliate link. (Phase 2 feature)</p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="form_id">WPForms Form ID</label>
                </th>
                <td>
                    <input type="text" id="form_id" name="form_id" value="<?php echo esc_attr($form_id); ?>" class="small-text">
                    <p class="description">The WPForms form ID for affiliate applications. (Staging: 5066, Production: 5025)</p>
                </td>
            </tr>
        </table>

        <h2>Zapier Integration (Optional)</h2>
        <table class="form-table">
            <tr>
                <th scope="row">
                    Enable Zapier
                </th>
                <td>
                    <label>
                        <input type="checkbox" name="zapier_enabled" value="1" <?php checked($zapier_enabled, '1'); ?>>
                        Send affiliate applications to Zapier webhook
                    </label>
                    <p class="description">
                        When enabled, applications will be saved to WordPress <strong>AND</strong> sent to Zapier.<br>
                        When disabled, applications will only be saved to WordPress (recommended for most users).
                    </p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="zapier_webhook_url">Zapier Webhook URL</label>
                </th>
                <td>
                    <input type="url" id="zapier_webhook_url" name="zapier_webhook_url" value="<?php echo esc_attr($zapier_webhook_url); ?>" class="regular-text" placeholder="https://hooks.zapier.com/hooks/catch/...">
                    <p class="description">
                        Get this URL from Zapier: Create a Zap → "Webhooks by Zapier" → "Catch Hook"
                    </p>
                </td>
            </tr>
        </table>

        <h2>WooCommerce Coupon Generation</h2>
        <table class="form-table">
            <tr>
                <th scope="row">
                    Enable Coupon Generation
                </th>
                <td>
                    <?php $coupon_enabled = get_option('sst_affiliate_coupon_enabled', '1'); ?>
                    <label>
                        <input type="checkbox" name="coupon_enabled" value="1" <?php checked($coupon_enabled, '1'); ?>>
                        Automatically generate WooCommerce coupons when affiliates are approved
                    </label>
                    <p class="description">
                        <?php if (class_exists('WooCommerce')): ?>
                            ✅ WooCommerce is active
                        <?php else: ?>
                            ⚠️ WooCommerce is not active. Please install and activate WooCommerce to use coupon generation.
                        <?php endif; ?>
                    </p>
                </td>
            </tr>
            <?php
            $coupon_type = get_option('sst_affiliate_coupon_type', 'percent');
            $coupon_amount = get_option('sst_affiliate_coupon_amount', '10');
            $coupon_prefix = get_option('sst_affiliate_coupon_prefix', 'AFFILIATE');
            $coupon_free_shipping = get_option('sst_affiliate_coupon_free_shipping', '0');
            $coupon_individual_use = get_option('sst_affiliate_coupon_individual_use', '1');
            $coupon_expiry = get_option('sst_affiliate_coupon_expiry', '0');
            ?>
            <tr>
                <th scope="row">
                    <label for="coupon_type">Discount Type</label>
                </th>
                <td>
                    <select id="coupon_type" name="coupon_type">
                        <option value="percent" <?php selected($coupon_type, 'percent'); ?>>Percentage Discount</option>
                        <option value="fixed_cart" <?php selected($coupon_type, 'fixed_cart'); ?>>Fixed Cart Discount</option>
                    </select>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="coupon_amount">Discount Amount</label>
                </th>
                <td>
                    <input type="number" id="coupon_amount" name="coupon_amount" value="<?php echo esc_attr($coupon_amount); ?>" step="0.01" min="0" class="small-text">
                    <span id="discount-symbol">%</span>
                    <p class="description">The discount amount for affiliate coupons.</p>
                    <script>
                    document.getElementById('coupon_type').addEventListener('change', function() {
                        document.getElementById('discount-symbol').textContent = this.value === 'percent' ? '%' : '$';
                    });
                    </script>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="coupon_prefix">Coupon Code Prefix</label>
                </th>
                <td>
                    <input type="text" id="coupon_prefix" name="coupon_prefix" value="<?php echo esc_attr($coupon_prefix); ?>" class="regular-text">
                    <p class="description">Generated coupons will be: PREFIX-AFF001, PREFIX-AFF002, etc.</p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    Coupon Options
                </th>
                <td>
                    <label>
                        <input type="checkbox" name="coupon_free_shipping" value="1" <?php checked($coupon_free_shipping, '1'); ?>>
                        Grant free shipping
                    </label>
                    <br>
                    <label>
                        <input type="checkbox" name="coupon_individual_use" value="1" <?php checked($coupon_individual_use, '1'); ?>>
                        Individual use only (cannot be combined with other coupons)
                    </label>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="coupon_expiry">Coupon Expiry</label>
                </th>
                <td>
                    <input type="number" id="coupon_expiry" name="coupon_expiry" value="<?php echo esc_attr($coupon_expiry); ?>" min="0" class="small-text"> days
                    <p class="description">0 = no expiry. Coupons will expire this many days after creation.</p>
                </td>
            </tr>
        </table>

        <h2>Affiliate Banner</h2>
        <table class="form-table">
            <?php
            $banner_enabled = get_option('sst_affiliate_banner_enabled', '1');
            $banner_message = get_option('sst_affiliate_banner_message', 'Earn at least 10% commission! Join our affiliate program.');
            $banner_button_text = get_option('sst_affiliate_banner_button_text', 'Become an Affiliate');
            $banner_bg_color = get_option('sst_affiliate_banner_bg_color', '#667eea');
            $banner_text_color = get_option('sst_affiliate_banner_text_color', '#ffffff');
            ?>
            <tr>
                <th scope="row">
                    Enable Banner
                </th>
                <td>
                    <label>
                        <input type="checkbox" name="banner_enabled" value="1" <?php checked($banner_enabled, '1'); ?>>
                        Show affiliate banner on your site
                    </label>
                    <p class="description">Add shortcode [sst_affiliate_banner] to any page or use widget. (Coming soon)</p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="banner_message">Banner Message</label>
                </th>
                <td>
                    <input type="text" id="banner_message" name="banner_message" value="<?php echo esc_attr($banner_message); ?>" class="large-text">
                </td>
            </tr>
            <tr>
                <th scope="row">
                    <label for="banner_button_text">Button Text</label>
                </th>
                <td>
                    <input type="text" id="banner_button_text" name="banner_button_text" value="<?php echo esc_attr($banner_button_text); ?>" class="regular-text">
                </td>
            </tr>
            <tr>
                <th scope="row">
                    Colors
                </th>
                <td>
                    <label>
                        Background Color:
                        <input type="color" name="banner_bg_color" value="<?php echo esc_attr($banner_bg_color); ?>">
                    </label>
                    <br>
                    <label>
                        Text Color:
                        <input type="color" name="banner_text_color" value="<?php echo esc_attr($banner_text_color); ?>">
                    </label>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    Banner Preview
                </th>
                <td>
                    <div id="banner-preview" style="background: <?php echo esc_attr($banner_bg_color); ?>; color: <?php echo esc_attr($banner_text_color); ?>; padding: 20px; border-radius: 8px; text-align: center;">
                        <p style="margin: 0 0 15px 0; font-size: 16px; color: inherit;"><span id="preview-message"><?php echo esc_html($banner_message); ?></span></p>
                        <a href="#" style="display: inline-block; padding: 12px 30px; background: rgba(255,255,255,0.2); color: inherit; text-decoration: none; border-radius: 6px; font-weight: bold;"><span id="preview-button"><?php echo esc_html($banner_button_text); ?></span></a>
                    </div>
                    <script>
                    // Live preview
                    document.getElementById('banner_message').addEventListener('input', function() {
                        document.getElementById('preview-message').textContent = this.value;
                    });
                    document.getElementById('banner_button_text').addEventListener('input', function() {
                        document.getElementById('preview-button').textContent = this.value;
                    });
                    document.querySelector('input[name="banner_bg_color"]').addEventListener('input', function() {
                        document.getElementById('banner-preview').style.background = this.value;
                    });
                    document.querySelector('input[name="banner_text_color"]').addEventListener('input', function() {
                        document.getElementById('banner-preview').style.color = this.value;
                    });
                    </script>
                </td>
            </tr>
        </table>

        <h2>Email Notifications</h2>
        <table class="form-table">
            <tr>
                <th scope="row">
                    <label for="admin_email">Admin Email</label>
                </th>
                <td>
                    <input type="email" id="admin_email" name="admin_email" value="<?php echo esc_attr($admin_email); ?>" class="regular-text">
                    <p class="description">Receive notifications at this email address when new applications are submitted.</p>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    Admin Notifications
                </th>
                <td>
                    <label>
                        <input type="checkbox" name="notify_admin" value="1" <?php checked($notify_admin, '1'); ?>>
                        Notify admin when new application is submitted
                    </label>
                </td>
            </tr>
            <tr>
                <th scope="row">
                    Affiliate Notifications
                </th>
                <td>
                    <?php
                    $notify_on_sale = get_option('sst_affiliate_notify_on_sale', '1');
                    $notify_on_payment = get_option('sst_affiliate_notify_on_payment', '1');
                    ?>
                    <label>
                        <input type="checkbox" name="notify_applicant" value="1" <?php checked($notify_applicant, '1'); ?>>
                        Send approval email when affiliate is approved
                    </label>
                    <br>
                    <label>
                        <input type="checkbox" name="notify_on_sale" value="1" <?php checked($notify_on_sale, '1'); ?>>
                        Notify affiliate when someone uses their coupon (new sale)
                    </label>
                    <br>
                    <label>
                        <input type="checkbox" name="notify_on_payment" value="1" <?php checked($notify_on_payment, '1'); ?>>
                        Notify affiliate when commission payment is made
                    </label>
                    <p class="description">
                        💡 Affiliate email notifications use WordPress wp_mail(). Make sure your site can send emails properly.
                    </p>
                </td>
            </tr>
        </table>

        <?php submit_button('Save Settings'); ?>
    </form>

    <hr>

    <h2>System Status</h2>
    <table class="form-table">
        <tr>
            <th>Database Tables</th>
            <td>
                <?php
                global $wpdb;
                $table = $wpdb->prefix . 'sst_affiliates';
                $exists = $wpdb->get_var("SHOW TABLES LIKE '$table'") === $table;
                echo $exists ? '<span style="color: green;">✓ Installed</span>' : '<span style="color: red;">✗ Not installed</span>';
                ?>
            </td>
        </tr>
        <tr>
            <th>Total Affiliates</th>
            <td>
                <?php
                $affiliate_model = new SST_Affiliate();
                echo esc_html($affiliate_model->count());
                ?>
            </td>
        </tr>
        <tr>
            <th>Pending Applications</th>
            <td>
                <?php echo esc_html($affiliate_model->count('pending')); ?>
            </td>
        </tr>
        <tr>
            <th>Approved Affiliates</th>
            <td>
                <?php echo esc_html($affiliate_model->count('approved')); ?>
            </td>
        </tr>
        <tr>
            <th>Application Page</th>
            <td>
                <a href="<?php echo esc_url(home_url('/partner/')); ?>" target="_blank">
                    <?php echo esc_url(home_url('/partner/')); ?>
                </a>
            </td>
        </tr>
    </table>
</div>
