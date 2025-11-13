# ElectroShop Data Validation - Quick Reference

## Validation Status: ⚠️ FAILED (11 violations)

### Critical Issues Requiring Action

#### 1. Primary Key Violations
- 🔴 **279 duplicate Session_IDs** globally
- 🔴 **211 duplicate Session_IDs** within days
- ✅ `id` column is unique (use as alternative primary key)

#### 2. Data Quality Issues
- 🟡 **92 rows** with malformed Time_of_Day values (typos: M0rning, AfterNoon, etc.)
- 🔴 **634 Price nulls** (4.6%) - required column
- 🔴 **287 Category nulls** (2.1%) - required column  
- 🔴 **280 Session_ID nulls** (2.0%) - required column
- 🔴 **278+ nulls** in Device_Type, Time_of_Day, Campaign_Period - required columns

### Commands

```bash
# Activate environment
source .venv/bin/activate

# Run validation
make validate          # Full report with details
make test             # Run 31 automated tests
make all              # Both validation + tests

# View reports
cat reports/schema_key_violations.csv
cat reports/nulls_overview.csv
cat reports/schema_validation_summary.md
```

### Test Results
- **Total:** 31 tests
- **Passed:** 20 ✅
- **Failed:** 11 ❌

### Files Generated
1. `src/validate_schema.py` - Main validation script
2. `src/tests/test_schema.py` - PyTest suite (31 tests)
3. `reports/schema_key_violations.csv` - Violation details
4. `reports/nulls_overview.csv` - Missing value statistics
5. `reports/schema_validation_summary.md` - Full report
6. `Makefile` - Automation commands

### Next Priority Actions
1. ✅ Lock temporal splits (Days 1-60 train, 61-70 val, 71-100 test)
2. 🔄 Create leakage audit report
3. 🔄 Define imputation strategy
4. 🔄 Outlier profiling

### Dataset Stats
- **Rows:** 13,735
- **Columns:** 22
- **Days covered:** 1-70 (training set)
- **Purchase rate:** Check with drift analysis

---
*Last updated: November 11, 2025*
*DQ/LKG Lead: Erik*
