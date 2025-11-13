# Step 1: Schema & Keys Validation - Summary Report

**Author:** Erik (Data Quality & Leakage Lead)  
**Date:** November 11, 2025  
**Status:** ⚠️ VALIDATION FAILED - 11 violations found

---

## Executive Summary

Schema validation has been completed on the ElectroShop training dataset (13,735 rows). The validation identified **11 critical data quality issues** that must be addressed before proceeding with modeling:

### Critical Issues Found:
1. ❌ **279 duplicate Session_IDs** (globally unique constraint violated)
2. ❌ **211 duplicate Session_IDs within days** (within-day uniqueness violated)
3. ❌ **54 invalid Time_of_Day values** (case/typo issues: e.g., "M0rning", "AfterNoon")
4. ❌ **Multiple required columns contain nulls** (Session_ID, Price, Category, etc.)

### What Passed:
- ✅ All numeric ranges are valid (Age, Day, Discount, Price, etc.)
- ✅ Binary/categorical values are correct (Purchase, Gender, Category, Device_Type)
- ✅ No infinite values in numeric columns
- ✅ The `id` column is globally unique

---

## Detailed Findings

### 1. Primary Key Violations

#### Session_ID Uniqueness (CRITICAL)
- **Expected:** Session_ID should be globally unique
- **Found:** 279 duplicate Session_IDs across the dataset
- **Impact:** Cannot use Session_ID as primary key; data integrity compromised

#### Session_ID Within-Day Uniqueness
- **Expected:** Session_ID should be unique within each day
- **Found:** 211 duplicate Session_IDs within specific days
- **Affected Days:** 60+ days have duplicates (range: 1-7 duplicates per day)
- **Most affected:** Days 5, 40, 67, 69 (5-7 duplicates each)

**Recommendation:** 
- Investigate root cause of duplicates
- Consider using `id` column as primary key instead
- Create composite key: (Day, Session_ID) if appropriate

---

### 2. Categorical Value Issues

#### Time_of_Day Inconsistencies (HIGH PRIORITY)
- **Expected values:** `morning`, `afternoon`, `evening`
- **Found:** 54 invalid variants due to case issues and typos
- **Examples of invalid values:**
  - `M0rning`, `m0rning` (zero instead of 'o')
  - `MOrnINg`, `MOrning`, `Morning` (case inconsistencies)
  - `afterno0n`, `aftern00n` (zeros instead of 'o')
  - `AfterNoon`, `afternOOn` (case inconsistencies)
  - `Evening`, `EVening`, `eveNing` (case inconsistencies)
- **Rows affected:** 92 rows (0.67% of dataset)

**Recommendation:**
- Apply case-insensitive standardization: `.str.lower()`
- Fix typos: replace `'0'` with `'o'`
- Add data cleaning step in preprocessing

---

### 3. Null/Missing Values

#### Required Columns with Nulls (Policy Violation)

According to `data_contract.yaml`, the following columns should NOT contain nulls but do:

| Column | Null Count | Null % | Allow Null | Status |
|--------|-----------|--------|------------|--------|
| **Price** | 634 | 4.62% | ❌ No | ❌ FAIL |
| **Category** | 287 | 2.09% | ❌ No | ❌ FAIL |
| **Session_ID** | 280 | 2.04% | ❌ No | ❌ FAIL |
| **Items_In_Cart** | 280 | 2.04% | ❌ No | ❌ FAIL |
| **Time_of_Day** | 279 | 2.03% | ❌ No | ❌ FAIL |
| **Device_Type** | 278 | 2.02% | ❌ No | ❌ FAIL |
| **Campaign_Period** | 278 | 2.02% | ❌ No | ❌ FAIL |
| **Email_Interaction** | 264 | 1.92% | ❌ No | ❌ FAIL |

#### Columns Allowed to Have Nulls (No Issue)

| Column | Null Count | Null % | Allow Null | Status |
|--------|-----------|--------|------------|--------|
| Age | 2087 | 15.19% | ✅ Yes | ✅ OK |
| Payment_Method | 2052 | 14.94% | ✅ Yes | ✅ OK |
| Referral_Source | 2021 | 14.71% | ✅ Yes | ✅ OK |
| Reviews_Read | 291 | 2.12% | ✅ Yes | ✅ OK |
| Socioeconomic_Status_Score | 275 | 2.00% | ✅ Yes | ✅ OK |
| Discount | 273 | 1.99% | ✅ Yes | ✅ OK |
| Engagement_Score | 272 | 1.98% | ✅ Yes | ✅ OK |
| Gender | 260 | 1.89% | ✅ Yes | ✅ OK |

**Recommendation:**
- **Price nulls (4.62%):** Impute with median by Category
- **Category nulls (2.09%):** Investigate patterns; consider mode imputation or "Unknown" category
- **Session_ID/Device_Type/Time_of_Day nulls (~2%):** These likely represent corrupt rows; consider dropping
- Create binary `missing_X` indicator features for all columns with >1% missingness

---

### 4. Data Type Issues (Minor)

Several integer columns are stored as `float64` due to null presence:
- Age, Gender, Reviews_Read, Discount, Category, Items_In_Cart, Email_Interaction

**Recommendation:** After imputation, convert back to integer types using pandas nullable integer dtype (`Int64`)

---

### 5. What Validated Successfully ✅

#### Numeric Ranges
- ✅ Age: [18, 65]
- ✅ Day: [1, 100] (train covers days 1-70)
- ✅ Discount: [0, 100]
- ✅ Price: > 0 (for non-null values)
- ✅ Items_In_Cart: ≥ 0
- ✅ Reviews_Read: ≥ 0
- ✅ All score columns: ≥ 0

#### Categorical Domains
- ✅ Purchase: {0, 1}
- ✅ Gender: {0, 1} (plus nulls)
- ✅ Category: {0, 1, 2, 3, 4} (plus nulls)
- ✅ Email_Interaction: {0, 1} (plus nulls)
- ✅ Device_Type: {Mobile, Desktop, Tablet} (plus nulls)

#### Data Quality
- ✅ No completely null rows
- ✅ No +inf/-inf values in numeric columns
- ✅ `id` column is globally unique

---

## Reproducibility

### Files Generated
1. **`reports/schema_key_violations.csv`** - Detailed violation records (11 violations)
2. **`reports/nulls_overview.csv`** - Null statistics for all columns
3. **`src/validate_schema.py`** - Validation script (can be re-run anytime)
4. **`src/tests/test_schema.py`** - PyTest suite (31 tests)

### How to Run Validation

#### Quick Validation
```bash
cd /path/to/kaggle-electroshop
source .venv/bin/activate

# Run validation script
make validate

# Or directly:
python src/validate_schema.py
```

#### Run Test Suite
```bash
# Run all tests with verbose output
make test

# Or directly:
pytest src/tests/test_schema.py -v
```

#### Current Test Results
- **Total tests:** 31
- **Passed:** 20 (64.5%)
- **Failed:** 11 (35.5%)

---

## Next Steps & Recommendations

### Immediate Actions (Must-Do)
1. **Fix Session_ID duplicates**
   - Investigate cause of duplicates
   - Decide on deduplication strategy or use `id` as primary key
   
2. **Standardize Time_of_Day**
   - Add preprocessing: `df['Time_of_Day'].str.lower().str.replace('0', 'o')`
   
3. **Handle required column nulls**
   - Price: Impute with category-specific median
   - Category: Investigate patterns, impute with mode or create "Unknown" (5)
   - Session_ID nulls: Drop rows (only 280 rows, ~2%)
   
4. **Create missing indicators**
   - Add binary flags: `missing_Price`, `missing_Category`, etc. for all >1% missing
   
5. **Lock temporal splits** (next priority)
   - Train: Days 1-60
   - Validation: Days 61-70  
   - Test: Days 71-100

### Nice-to-Have
- Set up Great Expectations suite for continuous validation
- Add CI/CD hook to block commits with bad data
- Automate validation in preprocessing pipeline

---

## Appendix: Validation Architecture

### Data Contract (`configs/data_contract.yaml`)
Defines schema, constraints, and leakage policy:
- Column types, ranges, allowed values
- Null policies
- Primary keys
- Leakage prevention rules

### Validator (`src/validate_schema.py`)
- Validates all contract rules
- Generates detailed violation reports
- Creates null overview statistics
- Can be run standalone or in pipeline

### Test Suite (`src/tests/test_schema.py`)
- 31 automated tests covering:
  - Primary key uniqueness
  - Numeric ranges
  - Categorical domains
  - Null constraints
  - Data quality checks
- Integrates with CI/CD pipelines

---

## Contact

For questions about data quality validation:
- **Erik** - Data Quality & Leakage Lead
- See `src/validate_schema.py` for implementation details
- Run `make help` for available commands
