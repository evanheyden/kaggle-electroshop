import pandas as pd
from pathlib import Path
import numpy as np
import argparse

def preprocess_dataset(input_path: str, output_path: str, dataset_name: str = "dataset"):
    """
    Preprocess a dataset (train or test) with the same transformations.
    
    Args:
        input_path: Path to the raw CSV file
        output_path: Path to save the preprocessed CSV file
        dataset_name: Name of the dataset (for logging purposes)
    """
    print(f"\n{'='*60}")
    print(f"Processing {dataset_name}")
    print(f"{'='*60}\n")
    
    # Load raw data
    df = pd.read_csv(input_path)
    print(f"Loaded {dataset_name}: {df.shape[0]:,} rows, {df.shape[1]} columns")

    # Record before true count
    before_recompute = int(df['Campaign_Period'].sum())

    # recompute Campaign_Period per definition: Day in [25,50] or [75,90]
    df['Campaign_Period'] = df['Day'].between(25, 50) | df['Day'].between(75, 90)
    df['Campaign_Period'] = df['Campaign_Period'].astype(bool)

    # sanity check
    after_recompute = int(df['Campaign_Period'].sum())
    print("Before vs after", before_recompute, after_recompute)

    # Drop rows with null Session_ID (potentially impute surrogate Session_IDs later)
    before = len(df)
    df = df[df['Session_ID'].notna()].copy()
    df['Session_ID'] = df['Session_ID'].astype('string').str.strip()
    after = len(df)

    print(f"Dropped {before - after} rows with null Session_ID.")
    assert df['Session_ID'].notna().all()
    assert not df['Session_ID'].duplicated().any(), "Session_ID must be globally unique."


    ## Impute Payment_Method and Referral_Source from PM_RS_Combo
    # Check null counts before
    pm_null_before = df['Payment_Method'].isna().sum()
    rs_null_before = df['Referral_Source'].isna().sum()

    print("Nulls before:")
    print("  Payment_Method:", pm_null_before)
    print("  Referral_Source:", rs_null_before)

    # Sample combo values (optional quick check)
    print("\nPM_RS_Combo sample:", df['PM_RS_Combo'].dropna().head().tolist())

    # Rows where we can fill
    pm_null_with_combo = df[df['Payment_Method'].isna() & df['PM_RS_Combo'].notna()]
    rs_null_with_combo = df[df['Referral_Source'].isna() & df['PM_RS_Combo'].notna()]

    print("\nFillable from PM_RS_Combo:")
    print("  Payment_Method:", len(pm_null_with_combo))
    print("  Referral_Source:", len(rs_null_with_combo))

    # Extract values from PM_RS_Combo
    df['PM_from_combo'] = df['PM_RS_Combo'].astype('string').str.split(':', expand=True)[0]
    df['RS_from_combo'] = df['PM_RS_Combo'].astype('string').str.split(':', expand=True)[1]

    # Fill missing
    df['Payment_Method'] = df['Payment_Method'].fillna(df['PM_from_combo'])
    df['Referral_Source'] = df['Referral_Source'].fillna(df['RS_from_combo'])

    # Check null counts after
    pm_null_after = df['Payment_Method'].isna().sum()
    rs_null_after = df['Referral_Source'].isna().sum()

    print("\nNulls after:")
    print("  Payment_Method:", pm_null_after)
    print("  Referral_Source:", rs_null_after)

    # Cleanup
    df = df.drop(columns=['PM_from_combo', 'RS_from_combo'])

    # Final distributions
    print("\nFinal value counts:\n")
    print("Payment_Method:")
    print(df['Payment_Method'].value_counts(dropna=False))

    print("\nReferral_Source:")
    print(df['Referral_Source'].value_counts(dropna=False))


    # Clean Time_of_Day: case-insensitive standardization and fix '0'->'o'
    orig = df['Time_of_Day'].astype('string')
    normalized = orig.str.strip().str.lower().str.replace('0', 'o', regex=False)
    allowed = {'morning', 'afternoon', 'evening'}

    # how many values changed due to normalization (case/zeros)
    changed_mask = orig.notna() & (orig != normalized)
    n_changed = int(changed_mask.sum())


    # keep only allowed values, set others to <NA>
    normalized = normalized.where(normalized.isin(allowed))
    n_invalid_remaining = int(normalized.isna().sum())

    df['Time_of_Day'] = normalized

    print(f"Time_of_Day: standardized {n_changed} values; {n_invalid_remaining} rows set to NaN/unrecognized.")
    assert df['Time_of_Day'].dropna().isin(allowed).all()

    # Convert string categorical columns to category dtype for better memory efficiency
    categorical_string_cols = ['Time_of_Day', 'Device_Type']
    for col in categorical_string_cols:
        if col in df.columns:
            # Convert to category dtype (keeps NaN as NaN)
            df[col] = df[col].astype('category')
            print(f"{col}: converted to category dtype with {df[col].cat.categories.tolist()} categories")

    # Verify the change
    print(f"\nTime_of_Day dtype: {df['Time_of_Day'].dtype}")
    print(f"Device_Type dtype: {df['Device_Type'].dtype}")


    # Normalize Payment_Method typos (lowercase + regex) and map to canonical categories.

    # create cleaned lowercase token (remove punctuation/whitespace)
    pm = df['Payment_Method'].astype('string').str.lower().str.strip()
    pm_clean = pm.str.replace(r'[^a-z0-9]+', '', regex=True)

    # map common typo patterns to canonical labels
    conds = [
        pm_clean.str.contains(r'pay.*pal', na=False),
        pm_clean.str.contains(r'cre.*it|^cred', na=False),
        pm_clean.str.contains(r'cas.*h|^cash', na=False),
        pm_clean.str.contains(r'bank', na=False)
    ]
    choices = ['PayPal', 'Credit', 'Cash', 'Bank']

    # Use 'Unknown' as default instead of np.nan to avoid dtype conflict
    df['Payment_Method_norm'] = np.select(conds, choices, default='Unknown')
    # Set 'Unknown' back to NaN where original was NaN
    df.loc[df['Payment_Method'].isna(), 'Payment_Method_norm'] = pd.NA

    # quick sanity check
    df['Payment_Method_norm'].value_counts(dropna=False)

    # replace Payment_Method with Payment_Method_norm
    df['Payment_Method'] = df['Payment_Method_norm']

    # drop Payment_Method_norm
    df = df.drop(columns=['Payment_Method_norm'])


    # Normalize Referral_Source: lowercase, strip whitespace, fix '0'->'o'
    rs = df['Referral_Source'].astype('string').str.lower().str.strip()
    rs_clean = rs.str.replace('0', 'o', regex=False).str.replace('-', '_', regex=False).str.replace(' ', '', regex=False)

    # Map to canonical labels
    conds = [
        rs_clean.str.contains(r'social.*media', na=False),
        rs_clean.str.contains(r'direct', na=False),
        rs_clean.str.contains(r'search.*engine', na=False),
        rs_clean.str.contains(r'^ads?$|^ad$', na=False),
        rs_clean.str.contains(r'email', na=False)
    ]
    choices = ['Social_media', 'Direct', 'Search_engine', 'Ads', 'Email']

    # Use 'Unknown' as default, then set back to NaN where original was NaN
    df['Referral_Source_norm'] = np.select(conds, choices, default='Unknown')
    df.loc[df['Referral_Source'].isna(), 'Referral_Source_norm'] = pd.NA

    # Replace original with normalized version
    df['Referral_Source'] = df['Referral_Source_norm']
    df = df.drop(columns=['Referral_Source_norm'])

    # Verify standardization
    print("Standardized Referral_Source values:")
    print(df['Referral_Source'].value_counts(dropna=False))

    # Drop Price_Sine and PM_RS_Combo (can reintroduce later if needed)
    df = df.drop(columns=['PM_RS_Combo'])

    # Save preprocessed dataset
    df.to_csv(output_path, index=False)
    print(f"\nSaved preprocessed data to {output_path}")
    print(f"Final shape: {df.shape[0]:,} rows, {df.shape[1]} columns\n")
    
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess train or test dataset")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="dataset",
        help="Name of the dataset (for logging)"
    )
    
    args = parser.parse_args()
    
    # Run preprocessing
    preprocess_dataset(args.input, args.output, args.name)
