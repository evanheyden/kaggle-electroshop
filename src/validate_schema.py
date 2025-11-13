"""
Schema & Keys Validation for ElectroShop Dataset
Step 1: Assert uniqueness and validate domains according to data_contract.yaml

Author: Erik (Data Quality & Leakage Lead)
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates dataset against schema defined in data_contract.yaml"""
    
    def __init__(self, contract_path: str):
        """
        Initialize validator with data contract.
        
        Args:
            contract_path: Path to data_contract.yaml
        """
        with open(contract_path, 'r') as f:
            self.contract = yaml.safe_load(f)
        
        self.violations = []
        
    def validate_primary_keys(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate uniqueness of primary keys (Session_ID) within and across days.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results
        """
        logger.info("Validating primary keys...")
        results = {
            'passed': True,
            'issues': []
        }
        
        # Check Session_ID uniqueness globally
        session_dupes = df['Session_ID'].duplicated().sum()
        if session_dupes > 0:
            results['passed'] = False
            results['issues'].append(
                f"FAIL: {session_dupes} duplicate Session_IDs found globally"
            )
            self.violations.append({
                'check': 'primary_key_global',
                'column': 'Session_ID',
                'violations': session_dupes
            })
        else:
            results['issues'].append("✅ Session_ID is globally unique")
        
        # Check Session_ID uniqueness within each day
        day_dupes = df.groupby('Day')['Session_ID'].apply(
            lambda x: x.duplicated().sum()
        )
        if day_dupes.sum() > 0:
            results['passed'] = False
            problematic_days = day_dupes[day_dupes > 0]
            results['issues'].append(
                f"FAIL: Session_ID duplicates within days: {problematic_days.to_dict()}"
            )
            self.violations.append({
                'check': 'primary_key_within_day',
                'column': 'Session_ID',
                'violations': day_dupes.sum(),
                'problematic_days': problematic_days.to_dict()
            })
        else:
            results['issues'].append("✅ Session_ID is unique within each day")
        
        # Check if 'id' column exists and is unique
        if 'id' in df.columns:
            id_dupes = df['id'].duplicated().sum()
            if id_dupes > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {id_dupes} duplicate 'id' values found"
                )
                self.violations.append({
                    'check': 'id_uniqueness',
                    'column': 'id',
                    'violations': id_dupes
                })
            else:
                results['issues'].append("✅ 'id' is unique")
        
        return results
    
    def validate_numeric_range(self, df: pd.DataFrame, column: str, 
                               spec: Dict) -> Dict[str, Any]:
        """
        Validate numeric column against range/bounds specifications.
        
        Args:
            df: DataFrame to validate
            column: Column name
            spec: Column specification from contract
            
        Returns:
            Dict with validation results
        """
        if column not in df.columns:
            return {
                'passed': False,
                'issues': [f"FAIL: Column '{column}' not found in dataset"]
            }
        
        results = {
            'passed': True,
            'issues': []
        }
        
        # Get non-null values
        values = df[column].dropna()
        
        if len(values) == 0:
            results['issues'].append(f"⚠️  {column}: all values are null")
            return results
        
        # Check range constraint
        if 'range' in spec:
            min_val, max_val = spec['range']
            out_of_range = ((values < min_val) | (values > max_val)).sum()
            if out_of_range > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {column} has {out_of_range} values outside range [{min_val}, {max_val}]"
                )
                results['issues'].append(
                    f"  Range found: [{values.min()}, {values.max()}]"
                )
                self.violations.append({
                    'check': 'range',
                    'column': column,
                    'expected': f"[{min_val}, {max_val}]",
                    'violations': out_of_range,
                    'actual_range': f"[{values.min()}, {values.max()}]"
                })
            else:
                results['issues'].append(
                    f"✅ {column} is within range [{min_val}, {max_val}]"
                )
        
        # Check >= constraint
        if 'ge' in spec:
            min_val = spec['ge']
            violations = (values < min_val).sum()
            if violations > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {column} has {violations} values < {min_val}"
                )
                self.violations.append({
                    'check': 'ge',
                    'column': column,
                    'expected': f">= {min_val}",
                    'violations': violations,
                    'min_found': values.min()
                })
            else:
                results['issues'].append(f"✅ {column} >= {min_val}")
        
        # Check > constraint
        if 'gt' in spec:
            min_val = spec['gt']
            violations = (values <= min_val).sum()
            if violations > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {column} has {violations} values <= {min_val}"
                )
                self.violations.append({
                    'check': 'gt',
                    'column': column,
                    'expected': f"> {min_val}",
                    'violations': violations,
                    'min_found': values.min()
                })
            else:
                results['issues'].append(f"✅ {column} > {min_val}")
        
        return results
    
    def validate_categorical(self, df: pd.DataFrame, column: str, 
                            spec: Dict) -> Dict[str, Any]:
        """
        Validate categorical column against allowed values.
        
        Args:
            df: DataFrame to validate
            column: Column name
            spec: Column specification from contract
            
        Returns:
            Dict with validation results
        """
        if column not in df.columns:
            return {
                'passed': False,
                'issues': [f"FAIL: Column '{column}' not found in dataset"]
            }
        
        results = {
            'passed': True,
            'issues': []
        }
        
        if 'allowed' not in spec:
            return results
        
        allowed = set(spec['allowed'])
        values = df[column].dropna()
        unique_values = set(values.unique())
        
        # Check for unexpected values
        unexpected = unique_values - allowed
        if unexpected:
            results['passed'] = False
            count = df[column].isin(unexpected).sum()
            results['issues'].append(
                f"FAIL: {column} has {len(unexpected)} unexpected values: {unexpected}"
            )
            results['issues'].append(f"  {count} rows affected")
            self.violations.append({
                'check': 'categorical_allowed',
                'column': column,
                'expected': sorted(allowed),
                'unexpected_values': sorted(unexpected),
                'violations': count
            })
        else:
            results['issues'].append(
                f"✅ {column} contains only allowed values: {allowed}"
            )
        
        # Report if some allowed values are missing (info only)
        missing = allowed - unique_values
        if missing:
            results['issues'].append(
                f"ℹ️  {column}: allowed but not present: {missing}"
            )
        
        return results
    
    def validate_dtype(self, df: pd.DataFrame, column: str, 
                      expected_dtype: str) -> Dict[str, Any]:
        """
        Validate column data type.
        
        Args:
            df: DataFrame to validate
            column: Column name
            expected_dtype: Expected dtype from contract
            
        Returns:
            Dict with validation results
        """
        if column not in df.columns:
            return {
                'passed': False,
                'issues': [f"FAIL: Column '{column}' not found in dataset"]
            }
        
        results = {
            'passed': True,
            'issues': []
        }
        
        actual_dtype = df[column].dtype
        
        # Map contract dtypes to pandas dtypes
        dtype_mapping = {
            'int': ['int64', 'int32', 'int16', 'int8', 'Int64', 'Int32'],
            'float': ['float64', 'float32', 'Float64'],
            'string': ['object', 'string'],
            'category': ['object', 'string', 'category'],
            'bool': ['bool', 'boolean']
        }
        
        if expected_dtype in dtype_mapping:
            allowed_dtypes = dtype_mapping[expected_dtype]
            if str(actual_dtype) not in allowed_dtypes:
                results['passed'] = False
                results['issues'].append(
                    f"⚠️  {column}: expected {expected_dtype}, got {actual_dtype}"
                )
        
        return results
    
    def validate_nulls(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate null handling according to contract.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results and null statistics
        """
        logger.info("Validating null constraints...")
        results = {
            'passed': True,
            'issues': [],
            'null_stats': {}
        }
        
        for col_name, col_spec in self.contract['columns'].items():
            if col_name not in df.columns:
                continue
            
            null_count = df[col_name].isna().sum()
            null_pct = (null_count / len(df)) * 100
            
            results['null_stats'][col_name] = {
                'count': null_count,
                'percentage': null_pct,
                'allow_null': col_spec.get('allow_null', False)
            }
            
            # Check if nulls are allowed
            if not col_spec.get('allow_null', False) and null_count > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {col_name} has {null_count} nulls ({null_pct:.2f}%) but nulls not allowed"
                )
                self.violations.append({
                    'check': 'null_constraint',
                    'column': col_name,
                    'violations': null_count,
                    'percentage': null_pct
                })
        
        return results
    
    def validate_finite_numbers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check for inf/-inf values in numeric columns.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results
        """
        logger.info("Validating finite numbers constraint...")
        results = {
            'passed': True,
            'issues': []
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                results['passed'] = False
                results['issues'].append(
                    f"FAIL: {col} has {inf_count} inf/-inf values"
                )
                self.violations.append({
                    'check': 'finite_numbers',
                    'column': col,
                    'violations': inf_count
                })
        
        if results['passed']:
            results['issues'].append("✅ All numeric columns have finite values only")
        
        return results
    
    def validate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all validation checks.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with complete validation results
        """
        logger.info(f"Starting schema validation for {len(df)} rows...")
        
        all_results = {
            'primary_keys': self.validate_primary_keys(df),
            'columns': {},
            'nulls': self.validate_nulls(df),
            'finite_numbers': self.validate_finite_numbers(df)
        }
        
        # Validate each column according to spec
        for col_name, col_spec in self.contract['columns'].items():
            if col_name not in df.columns:
                all_results['columns'][col_name] = {
                    'passed': False,
                    'issues': [f"Column '{col_name}' missing from dataset"]
                }
                continue
            
            col_results = {
                'passed': True,
                'issues': []
            }
            
            # Validate dtype
            dtype_result = self.validate_dtype(df, col_name, col_spec['dtype'])
            col_results['issues'].extend(dtype_result['issues'])
            if not dtype_result['passed']:
                col_results['passed'] = False
            
            # Validate numeric constraints
            if col_spec['dtype'] in ['int', 'float']:
                range_result = self.validate_numeric_range(df, col_name, col_spec)
                col_results['issues'].extend(range_result['issues'])
                if not range_result['passed']:
                    col_results['passed'] = False
            
            # Validate categorical constraints
            if 'allowed' in col_spec:
                cat_result = self.validate_categorical(df, col_name, col_spec)
                col_results['issues'].extend(cat_result['issues'])
                if not cat_result['passed']:
                    col_results['passed'] = False
            
            all_results['columns'][col_name] = col_results
        
        return all_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "="*80)
        print("SCHEMA VALIDATION SUMMARY")
        print("="*80)
        
        # Primary keys
        print("\n🔑 PRIMARY KEYS:")
        for issue in results['primary_keys']['issues']:
            print(f"  {issue}")
        
        # Columns
        print("\n📋 COLUMN VALIDATION:")
        for col_name, col_result in results['columns'].items():
            if col_result['passed']:
                print(f"  ✅ {col_name}")
            else:
                print(f"  ❌ {col_name}")
                for issue in col_result['issues']:
                    print(f"    {issue}")
        
        # Nulls summary
        print("\n🔍 NULL VALUES SUMMARY:")
        null_stats = results['nulls']['null_stats']
        high_null_cols = {
            k: v for k, v in null_stats.items() 
            if v['percentage'] > 1.0
        }
        if high_null_cols:
            for col, stats in sorted(
                high_null_cols.items(), 
                key=lambda x: x[1]['percentage'], 
                reverse=True
            ):
                allowed = "✅" if stats['allow_null'] else "❌"
                print(
                    f"  {col}: {stats['count']} ({stats['percentage']:.2f}%) {allowed}"
                )
        
        # Finite numbers
        print("\n🔢 FINITE NUMBERS:")
        for issue in results['finite_numbers']['issues']:
            print(f"  {issue}")
        
        # Overall status
        print("\n" + "="*80)
        total_violations = len(self.violations)
        if total_violations == 0:
            print("✅ ALL CHECKS PASSED - Dataset conforms to schema")
        else:
            print(f"❌ VALIDATION FAILED - {total_violations} violation(s) found")
        print("="*80 + "\n")
    
    def save_violations_report(self, output_path: str):
        """Save detailed violations to CSV."""
        if self.violations:
            violations_df = pd.DataFrame(self.violations)
            violations_df.to_csv(output_path, index=False)
            logger.info(f"Violations report saved to {output_path}")
        else:
            logger.info("No violations to report")


def main():
    """Main validation script."""
    # Paths
    project_root = Path(__file__).parent.parent
    contract_path = project_root / "configs" / "data_contract.yaml"
    train_path = project_root / "data" / "raw" / "dsba-m-1-challenge-purchase-prediction" / "train_dataset_M1_with_id.csv"
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {train_path}")
    df = pd.read_csv(train_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Validate
    validator = SchemaValidator(str(contract_path))
    results = validator.validate_all(df)
    
    # Print summary
    validator.print_summary(results)
    
    # Save reports
    violations_path = reports_dir / "schema_key_violations.csv"
    validator.save_violations_report(str(violations_path))
    
    # Save null overview
    null_stats = results['nulls']['null_stats']
    null_df = pd.DataFrame([
        {
            'column': col,
            'null_count': stats['count'],
            'null_percentage': stats['percentage'],
            'allow_null': stats['allow_null']
        }
        for col, stats in null_stats.items()
    ]).sort_values('null_percentage', ascending=False)
    
    null_overview_path = reports_dir / "nulls_overview.csv"
    null_df.to_csv(null_overview_path, index=False)
    logger.info(f"Null overview saved to {null_overview_path}")


if __name__ == "__main__":
    main()
