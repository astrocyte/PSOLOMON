# Affiliate Manager Enhancements - December 3, 2025

## New Features

### 1. Deactivate/Reactivate Affiliates
Instead of permanently deleting affiliates (which destroys history and breaks tracking), you can now **deactivate** and **reactivate** them.

#### Why Use Deactivate Instead of Delete?
- **Preserves commission history** - All past sales and commissions remain tracked
- **Maintains referral data** - Historical referrals stay intact for reporting
- **Reversible** - Can reactivate if needed
- **Keeps coupon code** - Disables the coupon but doesn't delete it

#### How It Works

**Deactivate:**
```php
$affiliate = new SST_Affiliate();
$affiliate->deactivate('AFF-001');
```

**What happens:**
1. Affiliate status changes from `approved` to `inactive`
2. WooCommerce coupon is disabled (expiry set to yesterday)
3. Affiliate can no longer earn commissions
4. All historical data remains intact

**Reactivate:**
```php
$affiliate = new SST_Affiliate();
$affiliate->reactivate('AFF-001');
```

**What happens:**
1. Affiliate status changes from `inactive` to `approved`
2. WooCommerce coupon is re-enabled (expiry removed or extended)
3. Affiliate can start earning commissions again

#### Admin Dashboard Usage
*(UI implementation pending)*

In the affiliate detail page, you'll see buttons:
- **Deactivate** - For approved affiliates
- **Reactivate** - For inactive affiliates
- **Delete** - Permanent deletion (use sparingly!)

### 2. Custom Commission Rates Per Affiliate

Instead of a global 10% commission rate, you can now set **custom commission rates** for individual affiliates.

#### Use Cases
- **Premium partners** - Give 15% to high-performing affiliates
- **Promotional rates** - Offer 20% temporarily to boost signups
- **Volume-based** - Increase commission based on referral volume
- **Strategic partnerships** - Custom rates for specific organizations

#### How to Set Custom Rates

**Via Code:**
```php
$affiliate = new SST_Affiliate();
$affiliate->update_commission_rate('AFF-001', 15.50); // 15.5%
```

**Via Admin Dashboard:**
*(UI implementation pending)*

In the affiliate edit screen, you'll have a field:
```
Commission Rate: [15.50] %
Default: 10.00%
```

#### Database Structure
The `commission_rate` field already exists in the `wp_sst_affiliates` table:
```sql
commission_rate DECIMAL(5,2) DEFAULT 10.00
```

Supports rates from 0.00% to 99.99%

### 3. Custom Coupon Discount Per Affiliate

You can now customize the **discount amount** each affiliate's coupon offers to customers.

#### Use Cases
- **Premium affiliates** - Offer bigger discounts (15% vs 10%)
- **Limited-time promotions** - Temporarily increase discount
- **Fixed amount** discounts - $50 off instead of percentage
- **Strategic partners** - Custom discount rates for specific audiences

#### How to Set Custom Discounts

**Via Code:**
```php
$affiliate = new SST_Affiliate();

// Set 15% discount (percentage)
$affiliate->update_coupon_discount('AFF-001', 15, 'percent');

// Or set $50 fixed discount
$affiliate->update_coupon_discount('AFF-001', 50, 'fixed_cart');
```

**Via Admin Dashboard:**
*(UI implementation pending)*

In the affiliate edit screen:
```
Coupon Discount:
  Type: [Percentage ▼] or [Fixed Amount ▼]
  Amount: [15.00]
```

#### Discount Types
- **`percent`** - Percentage discount (e.g., 10%)
- **`fixed_cart`** - Fixed dollar amount (e.g., $50)

## API Reference

### SST_Affiliate Class

#### `deactivate($affiliate_id)`
Deactivate an affiliate (keeps data, disables coupon)

**Parameters:**
- `$affiliate_id` (string) - The affiliate ID (e.g., 'AFF-001')

**Returns:**
- `true` on success
- `WP_Error` on failure

**Example:**
```php
$result = $affiliate->deactivate('AFF-001');
if (is_wp_error($result)) {
    echo 'Error: ' . $result->get_error_message();
}
```

---

#### `reactivate($affiliate_id)`
Reactivate an inactive affiliate

**Parameters:**
- `$affiliate_id` (string) - The affiliate ID

**Returns:**
- `true` on success
- `WP_Error` on failure

**Errors:**
- `not_found` - Affiliate doesn't exist
- `invalid_status` - Only inactive affiliates can be reactivated

---

#### `update_commission_rate($affiliate_id, $new_rate)`
Update commission rate for specific affiliate

**Parameters:**
- `$affiliate_id` (string) - The affiliate ID
- `$new_rate` (float) - New commission rate (0-100)

**Returns:**
- `true` on success
- `WP_Error` on failure

**Example:**
```php
// Set to 15.5%
$result = $affiliate->update_commission_rate('AFF-001', 15.50);
```

---

#### `update_coupon_discount($affiliate_id, $new_discount, $discount_type = 'percent')`
Update coupon discount for specific affiliate

**Parameters:**
- `$affiliate_id` (string) - The affiliate ID
- `$new_discount` (float) - New discount amount
- `$discount_type` (string) - 'percent' or 'fixed_cart' (optional, default: 'percent')

**Returns:**
- `true` on success
- `WP_Error` on failure

**Errors:**
- `no_coupon` - Affiliate doesn't have a coupon code
- `invalid_discount` - Negative amount or >100% for percentage

**Example:**
```php
// 15% discount
$result = $affiliate->update_coupon_discount('AFF-001', 15, 'percent');

// $50 fixed discount
$result = $affiliate->update_coupon_discount('AFF-001', 50, 'fixed_cart');
```

### SST_Coupon_Manager Class

#### `update_coupon($coupon_code, $new_amount, $discount_type = 'percent')`
Update WooCommerce coupon discount

**Parameters:**
- `$coupon_code` (string) - The coupon code
- `$new_amount` (float) - New discount amount
- `$discount_type` (string) - 'percent' or 'fixed_cart'

---

#### `disable_coupon($coupon_code)`
Disable a coupon (sets expiry to yesterday)

**Parameters:**
- `$coupon_code` (string) - The coupon code

**Returns:**
- `true` on success
- `WP_Error` on failure

---

#### `enable_coupon($coupon_code, $days_until_expiry = 0)`
Enable a coupon

**Parameters:**
- `$coupon_code` (string) - The coupon code
- `$days_until_expiry` (int) - Days until expiry (0 = never expires)

**Returns:**
- `true` on success
- `WP_Error` on failure

## Database Schema

### Affiliates Table (`wp_sst_affiliates`)

Existing fields used by new features:
```sql
status VARCHAR(20) DEFAULT 'pending'  -- Values: pending, approved, rejected, inactive
commission_rate DECIMAL(5,2) DEFAULT 10.00
coupon_code VARCHAR(50)
```

**Status Values:**
- `pending` - Awaiting approval
- `approved` - Active affiliate
- `rejected` - Application denied
- **`inactive`** - Deactivated (new)

## Usage Examples

### Complete Affiliate Workflow

```php
$affiliate = new SST_Affiliate();

// 1. Approve new affiliate with custom commission
$affiliate->approve('AFF-001');
$affiliate->update_commission_rate('AFF-001', 12.00); // 12%

// 2. Give them a better coupon discount
$affiliate->update_coupon_discount('AFF-001', 15, 'percent'); // 15% off

// 3. Later, if needed, deactivate them
$affiliate->deactivate('AFF-001');

// 4. Reactivate if they return
$affiliate->reactivate('AFF-001');
```

### Bulk Operations

```php
// Give all approved affiliates 15% commission
$affiliates = $affiliate->get_all(['status' => 'approved']);
foreach ($affiliates as $aff) {
    $affiliate->update_commission_rate($aff->affiliate_id, 15.00);
}
```

### Promotional Campaign

```php
// Temporarily boost top performers
$top_performers = ['AFF-001', 'AFF-005', 'AFF-012'];

foreach ($top_performers as $aff_id) {
    // Increase their commission
    $affiliate->update_commission_rate($aff_id, 20.00);

    // Increase their coupon discount
    $affiliate->update_coupon_discount($aff_id, 20, 'percent');
}
```

## Admin Dashboard Integration

### ✅ IMPLEMENTED - Admin UI Complete

The admin UI has been fully implemented with all new features:

#### Affiliate Detail Page
The affiliate detail view (`/admin/views/affiliate-detail.php`) now includes:

**Status Badge:**
- Color-coded status indicators (pending, approved, rejected, inactive)
- Displayed in page header next to affiliate name

**Commission Settings Section:**
```
💰 Commission Settings
Commission Rate: [12.50] % [Update Commission Rate]
Current: 12.50% (Default: 10%)
```

**Coupon Settings Section:**
```
🎟️ Coupon Settings
Coupon Code: PS-JS25 [Copy] [Edit in WooCommerce]
Current Discount: 15%
Usage Stats: 5 times used
Update Discount:
  [Percentage ▼] [15.00] [Update Coupon Discount]
```

**Commission Performance:**
- Total Sales: $X,XXX.XX
- Commission Earned: $XXX.XX
- Commission Paid: $XXX.XX
- Commission Pending: $XXX.XX

**Action Buttons:**
For approved affiliates:
```
[💤 Deactivate Affiliate]  [🗑️ Delete Permanently]
```

For inactive affiliates:
```
[✅ Reactivate Affiliate]  [🗑️ Delete Permanently]
```

For pending affiliates:
```
[✅ Approve & Send Email]  [❌ Reject Application]
```

**Enhanced Admin Dashboard Class:**
- Added `handle_deactivate()` - Processes deactivate action
- Added `handle_reactivate()` - Processes reactivate action
- Added `handle_update_commission()` - Updates commission rates
- Added `handle_update_coupon()` - Updates coupon discounts
- All actions use WordPress nonces for security
- All actions redirect with success/error messages

## Testing

### Test Scenarios

1. **Deactivate/Reactivate:**
   - Create affiliate → Approve → Deactivate → Verify coupon disabled → Reactivate → Verify coupon enabled

2. **Custom Commission:**
   - Set custom rate → Make test sale → Verify commission calculated with custom rate

3. **Custom Discount:**
   - Update coupon discount → Test checkout → Verify new discount applied

### Manual Testing Checklist

- [ ] Deactivate affiliate - status changes to inactive
- [ ] Deactivate affiliate - coupon becomes unusable
- [ ] Reactivate affiliate - status changes to approved
- [ ] Reactivate affiliate - coupon works again
- [ ] Update commission rate - saves to database
- [ ] Update coupon discount - WooCommerce coupon updates
- [ ] Delete affiliate - coupon is permanently deleted

## Deployment

### Files Changed
1. `/wp-content/plugins/sst-affiliate-manager/includes/class-affiliate.php`
   - Added `deactivate()`, `reactivate()`, `update_commission_rate()`, `update_coupon_discount()`
   - Enhanced `delete()` to remove associated coupon

2. `/wp-content/plugins/sst-affiliate-manager/includes/class-coupon-manager.php`
   - Added `update_coupon()`, `disable_coupon()`, `enable_coupon()`

3. `/wp-content/plugins/sst-affiliate-manager/admin/class-admin-dashboard.php`
   - Added action handlers: `handle_deactivate()`, `handle_reactivate()`, `handle_update_commission()`, `handle_update_coupon()`
   - Registered admin_post actions for new features

4. `/wp-content/plugins/sst-affiliate-manager/admin/views/affiliate-detail.php`
   - Complete UI redesign with sections for commission settings, coupon settings, and actions
   - Added status badges, copy buttons, inline forms for updates
   - Enhanced delete confirmation with strong warnings

### Deployment Steps
1. ✅ Backup existing files
2. ✅ Deploy backend functionality to staging
3. ✅ Deploy backend functionality to production
4. ✅ Add UI controls to admin dashboard
5. ✅ Deploy admin UI to staging (December 3, 2025)
6. ✅ Deploy admin UI to production (December 3, 2025)
7. ⏳ Test all functionality on staging
8. ⏳ Test all functionality on production

### Rollback Plan
Restore from backups:
```bash
# Staging
cd /home/u629344933/domains/sst.nyc/public_html/staging/wp-content/plugins/sst-affiliate-manager/includes/
cp class-affiliate.php.backup-20251203-v2 class-affiliate.php
cp class-coupon-manager.php.backup-20251203-v2 class-coupon-manager.php

# Production
cd /home/u629344933/domains/sst.nyc/public_html/wp-content/plugins/sst-affiliate-manager/includes/
cp class-affiliate.php.backup-20251203-v2 class-affiliate.php
cp class-coupon-manager.php.backup-20251203-v2 class-coupon-manager.php
```

## Future Enhancements

1. **Admin UI** - Add dashboard controls for deactivate/reactivate and custom settings
2. **Email Notifications** - Notify affiliates when deactivated or reactivated
3. **Audit Log** - Track commission rate changes and status changes
4. **Bulk Operations** - Update multiple affiliates at once via UI
5. **Scheduled Reactivation** - Auto-reactivate after X days
6. **Tiered Commissions** - Automatically increase rates based on performance
7. **A/B Testing** - Test different discount amounts for optimization

## Support

For questions or issues:
- Email: support@sst.nyc
- Check logs: `/wp-content/debug.log` for affiliate operations
- Database: Query `wp_sst_affiliates` table for status and rates
