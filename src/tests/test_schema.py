"""
PyTest suite for schema validation.
Run with: pytest src/tests/test_schema.py -v
Or with make: make validate
"""

import pytest
import pandas as pd
import yaml
from pathlib import Path
import numpy as np


@pytest.fixture(scope="module")
def data_contract():
    """Load data contract."""
    contract_path = Path(__file__).parent.parent.parent / "configs" / "data_contract.yaml"
    with open(contract_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def train_df():
    """Load training data."""
    train_path = Path(__file__).parent.parent.parent / "data" / "raw" / \
                  "dsba-m-1-challenge-purchase-prediction" / "train_dataset_M1_with_id.csv"
    return pd.read_csv(train_path)


@pytest.fixture(scope="module")
def test_df():
    """Load test data if available."""
    test_path = Path(__file__).parent.parent.parent / "data" / "raw" / \
                "dsba-m-1-challenge-purchase-prediction" / "test_dataset_M1_with_id.csv"
    if test_path.exists():
        return pd.read_csv(test_path)
    return None


class TestPrimaryKeys:
    """Test primary key constraints."""
    
    def test_id_unique(self, train_df):
        """Test that 'id' column is globally unique."""
        assert train_df['id'].is_unique, \
            f"Found {train_df['id'].duplicated().sum()} duplicate IDs"
    
    def test_session_id_globally_unique(self, train_df):
        """Test that Session_ID is globally unique."""
        dupes = train_df['Session_ID'].duplicated().sum()
        assert dupes == 0, \
            f"Found {dupes} duplicate Session_IDs globally"
    
    def test_session_id_unique_within_day(self, train_df):
        """Test that Session_ID is unique within each day."""
        day_dupes = train_df.groupby('Day')['Session_ID'].apply(
            lambda x: x.duplicated().sum()
        )
        total_dupes = day_dupes.sum()
        assert total_dupes == 0, \
            f"Found {total_dupes} duplicate Session_IDs within days"


class TestNumericRanges:
    """Test numeric column ranges."""
    
    def test_age_range(self, train_df):
        """Test Age is within [18, 65]."""
        valid_ages = train_df['Age'].dropna()
        assert valid_ages.min() >= 18, f"Age min is {valid_ages.min()}"
        assert valid_ages.max() <= 65, f"Age max is {valid_ages.max()}"
    
    def test_day_range(self, train_df):
        """Test Day is within [1, 100]."""
        assert train_df['Day'].min() >= 1, f"Day min is {train_df['Day'].min()}"
        assert train_df['Day'].max() <= 100, f"Day max is {train_df['Day'].max()}"
    
    def test_discount_range(self, train_df):
        """Test Discount is within [0, 100]."""
        valid_discounts = train_df['Discount'].dropna()
        assert valid_discounts.min() >= 0, f"Discount min is {valid_discounts.min()}"
        assert valid_discounts.max() <= 100, f"Discount max is {valid_discounts.max()}"
    
    def test_price_positive(self, train_df):
        """Test Price is > 0."""
        valid_prices = train_df['Price'].dropna()
        assert (valid_prices > 0).all(), \
            f"Found {(valid_prices <= 0).sum()} prices <= 0"
    
    def test_reviews_read_non_negative(self, train_df):
        """Test Reviews_Read >= 0."""
        valid_reviews = train_df['Reviews_Read'].dropna()
        assert (valid_reviews >= 0).all(), \
            f"Found {(valid_reviews < 0).sum()} negative review counts"
    
    def test_items_in_cart_non_negative(self, train_df):
        """Test Items_In_Cart >= 0."""
        valid_items = train_df['Items_In_Cart'].dropna()
        assert (valid_items >= 0).all(), \
            f"Found {(valid_items < 0).sum()} negative item counts"
    
    def test_scores_non_negative(self, train_df):
        """Test score columns >= 0."""
        for col in ['Socioeconomic_Status_Score', 'Engagement_Score']:
            valid_scores = train_df[col].dropna()
            assert (valid_scores >= 0).all(), \
                f"Found {(valid_scores < 0).sum()} negative {col} values"


class TestCategoricalValues:
    """Test categorical column allowed values."""
    
    def test_purchase_binary(self, train_df):
        """Test Purchase is 0 or 1."""
        allowed = {0, 1}
        unique_vals = set(train_df['Purchase'].unique())
        assert unique_vals.issubset(allowed), \
            f"Purchase has unexpected values: {unique_vals - allowed}"
    
    def test_gender_binary(self, train_df):
        """Test Gender is 0 or 1 (or null)."""
        allowed = {0, 1}
        unique_vals = set(train_df['Gender'].dropna().unique())
        assert unique_vals.issubset(allowed), \
            f"Gender has unexpected values: {unique_vals - allowed}"
    
    def test_category_values(self, train_df):
        """Test Category is in {0, 1, 2, 3, 4}."""
        allowed = {0, 1, 2, 3, 4}
        unique_vals = set(train_df['Category'].dropna().unique())
        assert unique_vals.issubset(allowed), \
            f"Category has unexpected values: {unique_vals - allowed}"
    
    def test_time_of_day_values(self, train_df):
        """Test Time_of_Day is in {morning, afternoon, evening}."""
        allowed = {"morning", "afternoon", "evening"}
        unique_vals = set(train_df['Time_of_Day'].dropna().unique())
        unexpected = unique_vals - allowed
        assert len(unexpected) == 0, \
            f"Time_of_Day has {len(unexpected)} unexpected values: {unexpected}"
    
    def test_email_interaction_binary(self, train_df):
        """Test Email_Interaction is 0 or 1."""
        allowed = {0, 1}
        unique_vals = set(train_df['Email_Interaction'].dropna().unique())
        assert unique_vals.issubset(allowed), \
            f"Email_Interaction has unexpected values: {unique_vals - allowed}"
    
    def test_device_type_values(self, train_df):
        """Test Device_Type is in {Mobile, Desktop, Tablet}."""
        allowed = {"Mobile", "Desktop", "Tablet"}
        unique_vals = set(train_df['Device_Type'].dropna().unique())
        assert unique_vals.issubset(allowed), \
            f"Device_Type has unexpected values: {unique_vals - allowed}"


class TestNullConstraints:
    """Test null/missing value constraints."""
    
    @pytest.mark.parametrize("column", [
        'Session_ID', 'Day', 'Purchase', 'Price', 'Category',
        'Items_In_Cart', 'Time_of_Day', 'Email_Interaction',
        'Device_Type', 'Campaign_Period'
    ])
    def test_required_columns_no_nulls(self, train_df, column):
        """Test that required columns have no nulls."""
        null_count = train_df[column].isna().sum()
        assert null_count == 0, \
            f"{column} has {null_count} null values but nulls not allowed"


class TestFiniteNumbers:
    """Test numeric columns contain only finite values."""
    
    def test_no_inf_values(self, train_df):
        """Test no inf/-inf in numeric columns."""
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            inf_count = np.isinf(train_df[col]).sum()
            assert inf_count == 0, \
                f"{col} has {inf_count} inf/-inf values"


class TestSchemaCompleteness:
    """Test that all contract columns exist."""
    
    def test_all_contract_columns_exist(self, train_df, data_contract):
        """Test that all columns from contract exist in dataset."""
        contract_cols = set(data_contract['columns'].keys())
        df_cols = set(train_df.columns)
        
        # Check core columns exist
        missing = contract_cols - df_cols
        
        # Allow some derived or optional columns to be missing
        allowed_missing = {'id', 'AB_Bucket', 'Price_Sine', 'PM_RS_Combo'}
        unexpected_missing = missing - allowed_missing
        
        assert len(unexpected_missing) == 0, \
            f"Missing contract columns: {unexpected_missing}"


class TestDataQuality:
    """General data quality tests."""
    
    def test_no_completely_null_rows(self, train_df):
        """Test there are no completely null rows."""
        completely_null = train_df.isna().all(axis=1).sum()
        assert completely_null == 0, \
            f"Found {completely_null} completely null rows"
    
    def test_minimum_row_count(self, train_df):
        """Test dataset has minimum expected rows."""
        min_expected = 1000
        assert len(train_df) >= min_expected, \
            f"Dataset has only {len(train_df)} rows, expected >= {min_expected}"


# Test summary function
def test_suite_summary(train_df):
    """Print test suite summary."""
    print("\n" + "="*60)
    print("DATA VALIDATION TEST SUITE SUMMARY")
    print("="*60)
    print(f"Dataset shape: {train_df.shape}")
    print(f"Total rows: {len(train_df):,}")
    print(f"Total columns: {len(train_df.columns)}")
    print("="*60)
