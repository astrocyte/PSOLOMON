# Affiliate Manager Testing Guide
**Version:** 2.0
**Last Updated:** December 3, 2025

---

## Testing Environment

### Staging Server
- **URL:** https://staging.sst.nyc/wp-admin
- **Admin Page:** Affiliates → All Affiliates
- **Database Prefix:** `wp_`
- **Tables Created:** ✅ December 3, 2025

### Production Server
- **URL:** https://sst.nyc/wp-admin
- **Admin Page:** Affiliates → All Affiliates
- **Database Prefix:** `zush_`
- **Tables Created:** ✅ December 3, 2025

---

## Pre-Testing Setup

### 1. Verify Plugin is Active
```bash
# Production
wp plugin list | grep sst-affiliate-manager

# Should show: active
```

### 2. Verify Database Tables Exist
```bash
# Production (use zush_ prefix)
wp db query "SHOW TABLES LIKE 'zush_sst_%'" --allow-root

# Expected tables:
# - zush_sst_affiliates
# - zush_sst_affiliate_referrals
# - zush_sst_affiliate_commissions
```

### 3. Create Test Affiliate (if none exist)
Visit https://sst.nyc/partner/ or https://staging.sst.nyc/partner/ and submit the affiliate application form.

---

## Testing Scenarios

### Scenario 1: Deactivate Affiliate

**Steps:**
1. Navigate to Affiliates → All Affiliates
2. Click on an approved affiliate
3. Scroll to "Actions" section
4. Click "💤 Deactivate Affiliate"
5. Confirm the action

**Expected Results:**
- ✅ Success message: "Affiliate deactivated successfully. Coupon has been disabled."
- ✅ Status badge changes from "Approved" to "Inactive" (gray)
- ✅ "Deactivate" button is replaced with "Reactivate" button
- ✅ Coupon expiry set to yesterday in WooCommerce

**Database Verification:**
```bash
wp db query "SELECT affiliate_id, status, coupon_code FROM zush_sst_affiliates WHERE affiliate_id = 'AFF-001'" --allow-root
# Status should be: inactive
```

**WooCommerce Verification:**
- Go to WooCommerce → Coupons
- Find the affiliate's coupon
- Check that it shows "Expired" or expiry date is in the past

---

### Scenario 2: Reactivate Affiliate

**Steps:**
1. Navigate to an inactive affiliate
2. Click "✅ Reactivate Affiliate"
3. Confirm the action

**Expected Results:**
- ✅ Success message: "Affiliate reactivated successfully. Coupon has been re-enabled."
- ✅ Status badge changes from "Inactive" to "Approved" (green)
- ✅ "Reactivate" button is replaced with "Deactivate" button
- ✅ Coupon expiry removed or extended in WooCommerce

**Database Verification:**
```bash
wp db query "SELECT affiliate_id, status FROM zush_sst_affiliates WHERE affiliate_id = 'AFF-001'" --allow-root
# Status should be: approved
```

---

### Scenario 3: Update Commission Rate

**Steps:**
1. Navigate to affiliate detail page
2. Scroll to "💰 Commission Settings" section
3. Change commission rate (e.g., from 10.00 to 15.00)
4. Click "Update Commission Rate"

**Expected Results:**
- ✅ Success message: "Commission rate updated successfully!"
- ✅ Form shows new rate
- ✅ "Current" text displays new rate

**Database Verification:**
```bash
wp db query "SELECT affiliate_id, commission_rate FROM zush_sst_affiliates WHERE affiliate_id = 'AFF-001'" --allow-root
# commission_rate should be: 15.00
```

**Validation Tests:**
- Try negative rate (should fail gracefully)
- Try rate > 100 (should fail gracefully)
- Try non-numeric input (should sanitize to 0)

---

### Scenario 4: Update Coupon Discount (Percentage)

**Steps:**
1. Navigate to affiliate detail page
2. Scroll to "🎟️ Coupon Settings" section
3. Select "Percentage (%)" from dropdown
4. Change amount (e.g., from 10 to 15)
5. Click "Update Coupon Discount"

**Expected Results:**
- ✅ Success message: "Coupon discount updated successfully!"
- ✅ "Current Discount" shows new percentage
- ✅ WooCommerce coupon updated

**WooCommerce Verification:**
```bash
wp wc shop_coupon list --search="PS-" --allow-root
# Find the coupon and verify discount amount
```

---

### Scenario 5: Update Coupon Discount (Fixed Amount)

**Steps:**
1. Navigate to affiliate detail page
2. Select "Fixed Amount ($)" from dropdown
3. Enter amount (e.g., 50)
4. Click "Update Coupon Discount"

**Expected Results:**
- ✅ Success message: "Coupon discount updated successfully!"
- ✅ "Current Discount" shows "$50 (fixed)"
- ✅ WooCommerce coupon type changed to "fixed_cart"

---

### Scenario 6: Status Badge Display

**Test all status badges:**

1. **Pending Affiliate**
   - Badge: Orange background, "Pending" text
   - Available actions: "Approve & Send Email", "Reject Application"

2. **Approved Affiliate**
   - Badge: Green background, "Approved" text
   - Available actions: "Deactivate Affiliate", "Delete Permanently"

3. **Rejected Affiliate**
   - Badge: Red background, "Rejected" text
   - Available actions: "Delete Permanently"

4. **Inactive Affiliate**
   - Badge: Gray background, "Inactive" text
   - Available actions: "Reactivate Affiliate", "Delete Permanently"

---

### Scenario 7: Copy Coupon Code

**Steps:**
1. Navigate to affiliate detail page
2. Click "Copy" button next to coupon code

**Expected Results:**
- ✅ Button text changes to "Copied!"
- ✅ Coupon code copied to clipboard
- ✅ Button reverts to "Copy" after 2 seconds

**Manual Verification:**
- Paste into a text editor to confirm

---

### Scenario 8: Delete Affiliate

**WARNING:** This is destructive! Test on staging only.

**Steps:**
1. Navigate to affiliate detail page
2. Click "🗑️ Delete Permanently"
3. Read confirmation dialog carefully
4. Confirm deletion

**Expected Results:**
- ✅ Affiliate removed from database
- ✅ Associated coupon deleted from WooCommerce
- ✅ Redirect to affiliate list page
- ✅ Success message: "Affiliate deleted"

**Database Verification:**
```bash
wp db query "SELECT COUNT(*) FROM zush_sst_affiliates WHERE affiliate_id = 'AFF-001'" --allow-root
# Should return: 0
```

---

## Edge Cases to Test

### 1. WooCommerce Not Active
- Deactivate WooCommerce
- Try to update coupon settings
- **Expected:** Error message about WooCommerce being inactive

### 2. Affiliate Without Coupon
- Create affiliate manually without coupon_code
- View detail page
- **Expected:** Warning message about missing coupon

### 3. Invalid Commission Rates
- Try: -5.00 (negative)
- Try: 150.00 (over 100%)
- Try: "abc" (non-numeric)
- **Expected:** Graceful handling, no errors

### 4. Concurrent Updates
- Open affiliate in two browser tabs
- Update commission rate in both
- **Expected:** Last update wins, no errors

### 5. Missing Permissions
- Test with non-admin user
- **Expected:** "Unauthorized" or redirect to login

---

## Performance Testing

### 1. Page Load Time
- Measure affiliate detail page load time
- **Target:** < 2 seconds

### 2. Database Queries
- Enable Query Monitor plugin
- Check number of queries on detail page
- **Target:** < 50 queries

---

## Browser Compatibility

Test in:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

**Features to verify:**
- Copy to clipboard works
- Status badges render correctly
- Forms submit properly
- JavaScript confirmation dialogs work

---

## Regression Testing

After testing new features, verify old features still work:

1. **Affiliate Approval**
   - Approve pending affiliate
   - Verify coupon generated
   - Verify email sent (if configured)

2. **Form Submission**
   - Submit new affiliate application
   - Verify form success message
   - Verify affiliate created in database

3. **Affiliate List**
   - View all affiliates
   - Verify sorting works
   - Verify filtering works (if implemented)

---

## Automated Testing (Future)

### Unit Tests Template
```php
class Test_Coupon_Manager extends WP_UnitTestCase {

    public function test_disable_coupon() {
        $manager = new SST_Coupon_Manager();
        $result = $manager->disable_coupon('PS-JS25');
        $this->assertNotWPError($result);
    }

    public function test_enable_coupon() {
        $manager = new SST_Coupon_Manager();
        $result = $manager->enable_coupon('PS-JS25');
        $this->assertNotWPError($result);
    }

    public function test_update_coupon() {
        $manager = new SST_Coupon_Manager();
        $result = $manager->update_coupon('PS-JS25', 15, 'percent');
        $this->assertTrue($result);
    }
}
```

---

## Bug Reporting Template

When you find a bug, report it with:

1. **Environment:** Staging or Production
2. **Affiliate ID:** (e.g., AFF-001)
3. **Steps to Reproduce:**
   - Step 1
   - Step 2
   - Step 3
4. **Expected Result:** What should happen
5. **Actual Result:** What actually happened
6. **Screenshots:** If applicable
7. **Error Log:** Check `/wp-content/debug.log`

---

## Post-Testing Checklist

After completing all tests:

- [ ] All scenarios passed on staging
- [ ] All scenarios passed on production
- [ ] Edge cases handled gracefully
- [ ] No errors in debug log
- [ ] Browser compatibility verified
- [ ] Regression tests passed
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Team notified of new features

---

## Contact

For questions or issues:
- **Developer:** Claude Code
- **Documentation:** See AFFILIATE_ENHANCEMENTS.md
- **Code Review:** See CODE_REVIEW_AFFILIATE_ENHANCEMENTS.md
