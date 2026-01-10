# Edge Cases Documentation

**Last Updated:** 2026-01-09
**Purpose:** Document all edge cases, error scenarios, and system behaviors for domain routing, professional profiles, and user access.

---

## Table of Contents

1. [Domain Routing Edge Cases](#domain-routing-edge-cases)
2. [Professional Data Edge Cases](#professional-data-edge-cases)
3. [User Account Edge Cases](#user-account-edge-cases)
4. [Geo-Restriction Edge Cases](#geo-restriction-edge-cases)
5. [Database Schema Edge Cases](#database-schema-edge-cases)
6. [Template Rendering Edge Cases](#template-rendering-edge-cases)

---

## Domain Routing Edge Cases

### EC-DR-001: Unknown Domain
**Scenario:** User accesses site from domain not in brand_router.py mapping
**Current Behavior:** Falls back to 'soulfra' (brand_router.py:291)
**Log Location:** `logs/domain_routing.log`
**Expected:** User sees Soulfra homepage
**Edge Case:** If soulfra.com DNS is misconfigured, returns 500 error

### EC-DR-002: Localhost Without Port
**Scenario:** User visits `http://localhost` (no port specified)
**Current Behavior:** Browser adds default port 80, Flask running on 5001
**Log Location:** N/A
**Expected:** Connection refused
**Fix:** Always specify port: `http://localhost:5001`

### EC-DR-003: Domain Query Parameter Override
**Scenario:** User visits `http://localhost:5001?brand=cringeproof`
**Current Behavior:** Overrides default brand detection (brand_router.py:260-262)
**Log Location:** `logs/domain_routing.log`
**Expected:** Shows cringeproof content on localhost
**Use Case:** Local development testing

### EC-DR-004: Invalid Brand Parameter
**Scenario:** User visits `http://localhost:5001?brand=invalid`
**Current Behavior:** Parameter ignored, falls back to localhost default (stpetepros)
**Log Location:** `logs/domain_routing.log`
**Expected:** Shows stpetepros content
**Improvement Needed:** Log invalid brand attempts

### EC-DR-005: WWW Subdomain
**Scenario:** User visits `www.stpetepros.com`
**Current Behavior:** Correctly routes to stpetepros (brand_router.py:270)
**Log Location:** `logs/domain_routing.log`
**Expected:** Works same as `stpetepros.com`
**Note:** DNS must point www subdomain to server

---

## Professional Data Edge Cases

### EC-PD-001: Missing Address Field
**Scenario:** Professional created without address field
**Current Behavior (BEFORE FIX):** Templates show blank/undefined
**Current Behavior (AFTER FIX):** prove_it_works.py now includes address
**Log Location:** `logs/professionals_errors.log`
**Expected:** Template shows "Address not provided" fallback
**Fix Applied:** Updated prove_it_works.py line 246 to include address

### EC-PD-002: Missing Phone Number
**Scenario:** Professional created without phone
**Current Behavior:** Templates show blank
**Log Location:** `logs/professionals_errors.log`
**Expected:** Template shows "Contact via email" message
**Improvement Needed:** Add fallback UI in templates

### EC-PD-003: Missing Email
**Scenario:** Professional created without email
**Current Behavior:** Database constraint allows NULL
**Log Location:** `logs/professionals_errors.log`
**Expected:** Validation error during creation
**Improvement Needed:** Add NOT NULL constraint or validation

### EC-PD-004: Invalid Email Format
**Scenario:** Professional email is "notanemail"
**Current Behavior:** Stored in database, renders as mailto: link
**Log Location:** `logs/professionals_errors.log`
**Expected:** Validation error during creation
**Improvement Needed:** Add email format validation

### EC-PD-005: Missing Bio
**Scenario:** Professional created with empty bio
**Current Behavior:** Profile shows empty "About" section
**Log Location:** `logs/professionals_errors.log`
**Expected:** Show "Bio coming soon" message
**Improvement Needed:** Add minimum bio length requirement

### EC-PD-006: Professional Not Found
**Scenario:** User visits `/professional/999` (non-existent ID)
**Current Behavior:** stpetepros_routes.py:162 returns 404 with flash message
**Log Location:** `logs/route_access.log`
**Expected:** "Professional not found" error page
**Status:** Working as designed

### EC-PD-007: Unverified Professional
**Scenario:** Professional has verified=0 in database
**Current Behavior:** Profile page shows, but no verified badge
**Log Location:** N/A
**Expected:** Show "Verification pending" status
**Question:** Should unverified pros be publicly visible?

---

## User Account Edge Cases

### EC-UA-001: No User Account Linked
**Scenario:** Professional created with user_id=NULL
**Current Behavior:** Professional exists but can't log in to edit profile
**Log Location:** `logs/auth_errors.log`
**Expected:** Professional can be created, but needs account to manage
**Status:** Working as designed (professionals seeded before user signup)

### EC-UA-002: User Account With No Professional Profile
**Scenario:** User logs in but has no professional_id
**Current Behavior:** User can browse but can't access professional dashboard
**Log Location:** `logs/auth_errors.log`
**Expected:** Show "Create Professional Profile" prompt
**Improvement Needed:** Add profile creation flow

### EC-UA-003: Multiple Professionals Per User
**Scenario:** User wants to manage 2+ businesses
**Current Behavior:** Database allows multiple professionals with same user_id
**Log Location:** N/A
**Expected:** User sees dashboard with all their businesses
**Improvement Needed:** Multi-business dashboard UI

---

## Geo-Restriction Edge Cases

### EC-GR-001: Localhost Access to Geo-Restricted Domain
**Scenario:** User on localhost accesses stpetepros
**Current Behavior:** Allowed (brand_router.py:209-210)
**Log Location:** `logs/geo_access.log`
**Expected:** Access granted for development
**Status:** Working as designed

### EC-GR-002: Geo Override Parameter
**Scenario:** User visits `http://localhost:5001?geo_override=true`
**Current Behavior:** Bypasses geo-restriction check (brand_router.py:198-201)
**Log Location:** `logs/geo_access.log`
**Expected:** Development access granted
**Security:** Only works on localhost/local IPs

### EC-GR-003: Production Geo-Restriction
**Scenario:** User from California accesses stpetepros.com
**Current Behavior:** **NOT ENFORCED** - TODO comment at brand_router.py:212
**Log Location:** `logs/geo_access.log`
**Expected (Future):** Show "Geographic Restriction" page
**Status:** Documented but not implemented

### EC-GR-004: VPN/Proxy Detection
**Scenario:** User uses VPN to appear in Tampa Bay
**Current Behavior:** No VPN detection
**Log Location:** `logs/geo_access.log`
**Expected:** Accept IP at face value
**Note:** Not implementing VPN detection (privacy respect)

---

## Database Schema Edge Cases

### EC-DB-001: professionals vs professional_profile
**Scenario:** Code documents `professional_profile` table
**Reality:** Database has `professionals` table (different schema)
**Log Location:** `logs/database_errors.log`
**Impact:** Confusion, code/docs mismatch
**Fix Applied:** All code now uses `professionals` table
**Files Updated:** prove_it_works.py, stpetepros_routes.py

### EC-DB-002: Tutorial Table Missing
**Scenario:** Code references `tutorial` table
**Reality:** Table doesn't exist in database
**Log Location:** `logs/database_errors.log`
**Impact:** Tutorial features non-functional
**Status:** Feature not yet implemented

### EC-DB-003: professional_reviews Table
**Scenario:** stpetepros_routes.py:166 queries professional_reviews
**Reality:** Unclear if table exists
**Log Location:** `logs/database_errors.log`
**Impact:** Reviews may not display
**Needs:** Database schema verification

---

## Template Rendering Edge Cases

### EC-TR-001: Jinja2 Undefined Variables
**Scenario:** Template references `{{ professional['website'] }}` but website is NULL
**Current Behavior:** Renders empty string
**Log Location:** `logs/template_errors.log`
**Expected:** Show nothing or "Not provided"
**Status:** Working, but could be more explicit

### EC-TR-002: Missing Template File
**Scenario:** Route tries to render non-existent template
**Current Behavior:** Flask raises TemplateNotFound error (500)
**Log Location:** `logs/flask_errors.log`
**Expected:** 500 error page
**Status:** Standard Flask behavior

### EC-TR-003: Tailwind CDN Failure
**Scenario:** cdn.tailwindcss.com is down
**Current Behavior:** Pages load with no styling
**Log Location:** Browser console
**Expected:** Fallback to unstyled but functional HTML
**Improvement Needed:** Consider self-hosting Tailwind CSS

### EC-TR-004: Empty Categories Dict
**Scenario:** Homepage template expects `categories` dict but none passed
**Current Behavior:** Jinja2 shows 0 for all categories
**Log Location:** `logs/template_errors.log`
**Expected:** Query database to get actual counts
**Improvement Needed:** Pass category counts from route

---

## Logging Recommendations

### Log Files Structure
```
logs/
  ├── domain_routing.log       # Domain detection and routing decisions
  ├── professionals_errors.log # Missing/invalid professional data
  ├── route_access.log        # 404s, unauthorized access attempts
  ├── geo_access.log          # Geo-restriction checks and overrides
  ├── database_errors.log     # Schema mismatches, query failures
  ├── auth_errors.log         # Login failures, permission errors
  ├── template_errors.log     # Template rendering issues
  └── flask_errors.log        # General Flask errors
```

### Log Format
```
[TIMESTAMP] [LEVEL] [MODULE] [EDGE_CASE_ID] MESSAGE
Example:
[2026-01-09 14:52:03] [WARNING] [domain_routing] [EC-DR-004] Invalid brand parameter: "xyz"
[2026-01-09 14:53:12] [ERROR] [professional_data] [EC-PD-001] Professional 15 missing address field
```

---

## Testing Checklist

### Domain Routing
- [ ] Test localhost with no port
- [ ] Test localhost:5001
- [ ] Test ?brand= parameter with valid brands
- [ ] Test ?brand= parameter with invalid brand
- [ ] Test www subdomain routing
- [ ] Test non-existent domain

### Professional Profiles
- [ ] Access existing professional (ID 11-20)
- [ ] Access non-existent professional (ID 999)
- [ ] Create professional with missing fields
- [ ] View professional with NULL address
- [ ] View professional with NULL phone
- [ ] View professional with unverified status

### Geo-Restrictions
- [ ] Access stpetepros from localhost
- [ ] Access stpetepros with ?geo_override=true
- [ ] Access stpetepros from production (TODO: implement)
- [ ] Access non-geo-restricted brands

### Templates
- [ ] Verify Tailwind CSS loads
- [ ] Test with missing professional data
- [ ] Test category counts on homepage
- [ ] Test empty review list
- [ ] Test QR code display

---

## Improvement Priorities

1. **HIGH PRIORITY**
   - Implement edge_case_logger.py
   - Add template fallbacks for missing data
   - Verify all database tables exist
   - Add email format validation

2. **MEDIUM PRIORITY**
   - Implement geo-restriction for production
   - Add multi-business user dashboard
   - Self-host Tailwind CSS
   - Create missing data admin alerts

3. **LOW PRIORITY**
   - Implement VPN detection (if needed)
   - Add professional approval workflow
   - Generate category counts dynamically

---

## Questions for User

1. Should unverified professionals be publicly visible?
2. Do you want geo-restriction enforced in production? (requires IP geolocation API)
3. Should users be able to manage multiple professional profiles?
4. What's the minimum required data for a professional profile?
5. Should we implement email/phone verification?

---

**Generated by:** Claude Code
**Edge Cases Tracked:** 29
**Next Review Date:** 2026-01-16
