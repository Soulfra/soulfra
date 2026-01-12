# 💳 Stripe Setup Guide

How to configure Stripe payments for the Bodega Payment System.

---

## Overview

The Bodega Payment System uses **Stripe Payment Links** - no API keys in client code needed!

### Why Stripe Payment Links?

✅ **No client-side API keys** - Payment Links are already public URLs
✅ **No backend required** - Stripe hosts the checkout page
✅ **PCI compliant** - Stripe handles all card data
✅ **Mobile optimized** - Works on any device
✅ **Test mode available** - Test before going live

---

## Quick Start (2 Minutes)

### Step 1: Create Stripe Account

1. Sign up: https://dashboard.stripe.com/register
2. Verify email
3. Complete business details
4. Done! You're in **test mode** by default

### Step 2: Create a Payment Link

1. Go to: https://dashboard.stripe.com/payment-links
2. Click **"New"** button
3. Configure:
   - **Product name:** "Professional Service" (or your service name)
   - **Price:** $25.00 (or your price)
   - **Currency:** USD
   - **Quantity:** Customer can adjust (optional)
4. Click **"Create link"**
5. Copy the link - it looks like:
   ```
   https://buy.stripe.com/test_abc123xyz789
   ```

### Step 3: Use in Bodega System

**Test mode (default):**
```html
https://stpetepros.com/pay-bodega.html?stripe=test_abc123xyz789&amount=25.00&item=Plumbing+Service
```

**Live mode (after activation):**
```html
https://stpetepros.com/pay-bodega.html?stripe=abc123xyz789&amount=25.00&item=Plumbing+Service
```

**Generate QR code:**
1. Open: https://stpetepros.com/stpetepros-qr.html
2. Select "Stripe (Bodega Receipt)"
3. Paste Payment Link ID: `test_abc123xyz789`
4. Amount: `25.00`
5. Description: `Plumbing Service`
6. Click "Generate QR Codes"
7. Download and print!

---

## Test Mode vs Live Mode

### Test Mode (Default)

**What it is:**
- Fake payments for testing
- No real money charged
- Link ID starts with `test_`
- Safe to experiment

**Test card:**
```
Card number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/34)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

**More test cards:** https://stripe.com/docs/testing

### Live Mode (Production)

**What it is:**
- Real payments
- Real money charged
- Link ID has NO `test_` prefix
- Requires Stripe account activation

**To activate:**
1. Complete business verification
2. Add bank account for payouts
3. Activate account
4. Create new Payment Links in live mode

---

## Creating Payment Links for Different Services

### Example 1: Hourly Service ($50/hour)

```
Product: Plumbing - Hourly Rate
Price: $50.00
Quantity: Customer chooses hours

Payment Link: https://buy.stripe.com/test_hourly123
QR URL: https://stpetepros.com/pay-bodega.html?stripe=test_hourly123&amount=50.00&item=Plumbing+-+Hourly
```

### Example 2: Fixed Service ($125)

```
Product: Drain Cleaning
Price: $125.00
Quantity: Fixed (1)

Payment Link: https://buy.stripe.com/test_drain123
QR URL: https://stpetepros.com/pay-bodega.html?stripe=test_drain123&amount=125.00&item=Drain+Cleaning
```

### Example 3: Consultation ($25)

```
Product: Initial Consultation
Price: $25.00
Quantity: Fixed (1)

Payment Link: https://buy.stripe.com/test_consult123
QR URL: https://stpetepros.com/pay-bodega.html?stripe=test_consult123&amount=25.00&item=Consultation
```

---

## URL Parameters Explained

The bodega receipt page accepts these URL parameters:

### Required Parameters

**`stripe`** - Stripe Payment Link ID
```
?stripe=test_abc123xyz789
?stripe=abc123xyz789 (live mode)
```

**`amount`** - Amount to charge (displays on receipt)
```
?amount=25.00
?amount=125.50
```

**`item`** - Service description (displays on receipt)
```
?item=Plumbing+Service
?item=Electrical+Repair
```
*Note: Use `+` or `%20` for spaces*

### Optional Parameters

**`venmo`** - Venmo username (fallback payment option)
```
&venmo=john-smith
```

**`cashapp`** - Cash App cashtag (fallback payment option)
```
&cashapp=JohnSmith
```

**`paypal`** - PayPal username (fallback payment option)
```
&paypal=john.smith
```

**`paid=true`** - Show receipt as already paid
```
&paid=true
```

### Full Example

```
https://stpetepros.com/pay-bodega.html?stripe=test_abc123xyz789&amount=75.00&item=AC+Repair&venmo=john-plumber&paid=false
```

---

## No API Keys Needed!

### Traditional Stripe Integration

**Requires:**
- Stripe Publishable Key (pk_live_xxx)
- Stripe Secret Key (sk_live_xxx)
- Backend server
- Webhook handling
- Security concerns

### Our Approach (Stripe Payment Links)

**Requires:**
- Just the Payment Link ID
- No backend needed
- No API keys in code
- Stripe handles everything

**How it works:**
1. Customer scans QR code
2. Opens bodega receipt page (static HTML)
3. Clicks "Pay Now"
4. Stripe Payment Link opens (hosted by Stripe)
5. Customer enters card details on Stripe's page
6. Payment processed by Stripe
7. Redirects back to receipt with "PAID" stamp

**Security:**
- No sensitive data on your site
- Stripe handles all card data
- PCI compliance automatic
- No backend to hack

---

## Webhooks (Optional - For Automation)

### Why Use Webhooks?

Without webhooks:
- ✅ Payments work fine
- ❌ No automatic "PAID" stamp
- ❌ No email receipts
- ❌ No payment tracking

With webhooks:
- ✅ Automatic "PAID" stamp
- ✅ Email receipts sent
- ✅ Payment tracking in database
- ✅ Analytics and reporting

### Setup Webhooks (Cloudflare Workers)

**Step 1: Deploy Cloudflare Worker**

See `cloudflare-worker/README.md` for deployment instructions.

**Step 2: Create Webhook in Stripe**

1. Go to: https://dashboard.stripe.com/webhooks
2. Click **"Add endpoint"**
3. Endpoint URL: `https://your-worker.workers.dev/webhooks/stripe`
4. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
5. Click **"Add endpoint"**
6. Copy webhook signing secret (starts with `whsec_`)

**Step 3: Add Secret to GitHub**

```bash
gh secret set STRIPE_WEBHOOK_SECRET -b "whsec_abc123xyz789"
```

Or add manually at:
```
https://github.com/Soulfra/soulfra/settings/secrets/actions
```

---

## Testing Payment Flow

### Test Scenario 1: Successful Payment

1. Generate QR code with test Payment Link
2. Scan QR code with phone
3. Opens bodega receipt page
4. Click "Pay Now" button
5. Enter test card: `4242 4242 4242 4242`
6. Submit payment
7. Redirects to receipt with "PAID" stamp

**Expected:** ✅ Payment succeeds, receipt shows "PAID"

### Test Scenario 2: Declined Card

1. Use test card: `4000 0000 0000 0002` (declined)
2. Try to pay
3. Stripe shows error: "Your card was declined"
4. Customer can retry with different card

**Expected:** ❌ Payment fails gracefully with error message

### Test Scenario 3: Venmo Fallback

1. Open receipt page
2. Stripe payment fails or customer doesn't have card
3. Scroll down to "Alternative Payment Methods"
4. Click "Pay via Venmo" button
5. Venmo app opens with pre-filled amount

**Expected:** ✅ Venmo deep link works

---

## Going Live Checklist

Before switching from test mode to live mode:

- [ ] Stripe account fully activated
- [ ] Business details verified
- [ ] Bank account added for payouts
- [ ] Tax information submitted
- [ ] Create live Payment Links (remove `test_` prefix)
- [ ] Update QR codes with live Payment Link IDs
- [ ] Test one live payment with real card (small amount)
- [ ] Monitor Stripe dashboard for first 24 hours
- [ ] Setup webhook (optional but recommended)

---

## Stripe Dashboard Guide

### Where to Find Things

**Payment Links:**
```
https://dashboard.stripe.com/payment-links
```

**Payments (see who paid):**
```
https://dashboard.stripe.com/payments
```

**API Keys (for webhooks):**
```
https://dashboard.stripe.com/apikeys
```

**Webhooks:**
```
https://dashboard.stripe.com/webhooks
```

**Test Mode Toggle:**
```
Top-left corner: "Viewing test data" switch
```

---

## Pricing

### Stripe Fees

**Per transaction:**
- 2.9% + $0.30 (online payments)
- 2.7% + $0.05 (in-person with card reader)

**Example:**
```
$25 service → $0.30 + (2.9% × $25) = $1.03 fee
You receive: $23.97

$100 service → $0.30 + (2.9% × $100) = $3.20 fee
You receive: $96.80
```

### No Monthly Fees

- ✅ No setup fee
- ✅ No monthly fee
- ✅ No cancellation fee
- ✅ Only pay when you get paid

---

## Support

### Stripe Support

**Docs:** https://stripe.com/docs/payments/payment-links
**Support:** https://support.stripe.com
**Phone:** 1-888-926-2289 (US)

### Testing Resources

**Test cards:** https://stripe.com/docs/testing
**Webhook testing:** https://stripe.com/docs/webhooks/test

---

## Common Issues

### Issue: "This payment link is no longer available"

**Cause:** Payment Link was deleted or deactivated

**Fix:**
1. Create new Payment Link
2. Update QR codes with new link ID

### Issue: Payment succeeds but no "PAID" stamp

**Cause:** Webhook not configured

**Fix:**
1. Setup webhook (see above)
2. Or manually add `&paid=true` to URL after payment

### Issue: Can't switch to live mode

**Cause:** Stripe account not activated

**Fix:**
1. Complete business verification
2. Add bank account
3. Wait for Stripe approval (1-2 days)

---

## Next Steps

1. ✅ Create test Payment Link
2. ✅ Generate QR code
3. ✅ Test payment with test card
4. ✅ Verify receipt displays correctly
5. ⏭ Go live (activate Stripe account)
6. ⏭ Create live Payment Links
7. ⏭ Update QR codes
8. ⏭ Setup webhooks (optional)

---

**Ready to accept payments!** 💳

**Cost:** 2.9% + $0.30 per transaction (no monthly fees)
**Setup time:** 2 minutes
**Maintenance:** Zero
**PCI compliance:** Automatic (Stripe handles it)
