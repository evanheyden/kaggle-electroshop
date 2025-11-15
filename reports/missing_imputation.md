Here you go — a clean, readable **Markdown version** of your recommendations:

 

# Missing-Value Handling Recommendations (need to be done in time series cv to avoid leakage)

# Converting float to int needs to be done when in df as csv does not support it, see eda_general for code to do that

## 1. **Age** (15.13% NaN)

**Meaning:** User didn’t provide age / incomplete profile.
**Type:** Numeric
**Recommendation:**

* Impute with **median Age** (per train fold).
* Add **Age_missing** (0/1).
  **Why:** Age should logically exist; missingness partly reflects behavior (“doesn’t share age”).


## 2. **Payment_Method** (14.93% NaN)

**Meaning:** No payment selected yet / no past purchase / unknown.
**Type:** Categorical
**Recommendation:**

* Treat NaN as its own category (e.g. **"UnknownPayment"**).
  **Why:** “No payment yet” is behaviorally meaningful.



## 3. **Referral_Source** (14.66% NaN)

**Meaning:** Direct / unknown traffic source.
**Type:** Categorical
**Recommendation:**

* Map NaNs to **"Direct_or_Unknown"**.
  **Why:** Direct traffic is a valid marketing segment.



## 4. **Price** (4.58% NaN)

**Type:** Numeric
**Recommendation:**

* Median impute.
* Add **Price_missing** flag.
  **Why:** Core numeric; missing mostly logging errors.

 

## 5. **Reviews_Read** (2.13% NaN)

**Type:** Numeric count
**Recommendation:**

* Default: **Impute 0** + add **Reviews_Read_missing**.
  **Why:** “Didn’t view reviews page” ≈ 0 reviews.

 

## 6. **Category** (2.08% NaN)

**Type:** Categorical (0–4)
**Recommendation:**

* Treat NaN as **"UnknownCategory"**.
  **Why:** Should almost always be present → missing group is meaningful.


## 7. **Items_In_Cart** (2.07% NaN)

**Type:** Numeric count
**Recommendation:**

* Impute **0**.
* Optional: add **Items_In_Cart_missing**.
  **Why:** Missing ≈ not tracked; 0 is semantically correct.

 

## 8. **Discount** (2.01% NaN)

**Type:** Numeric (%)
**Recommendation:**

* Impute **0** (no discount).
* Optional: **Discount_missing** flag.
  **Why:** NaN rarely means “unknown discount.”

 

## 9. **Time_of_Day** (2.01% NaN)

**Type:** Categorical
**Recommendation:**

* Add **"UnknownTime"** category.
  **Why:** Logging-related missingness.

 

## 10. **Device_Type** (2.01% NaN)

**Type:** Categorical
**Recommendation:**

* Map NaNs to **"UnknownDevice"**.
  **Why:** Logging artifact; keep separate.

 

## 11. **Socioeconomic_Status_Score** (2.01% NaN)

**Type:** Numeric
**Recommendation:**

* Median impute.
* Add **SES_missing** flag.
  **Why:** Missing typically means insufficient external profile data.

 

## 12. **Engagement_Score** (1.97% NaN)

**Type:** Numeric
**Recommendation:**

* Impute **0** (no engagement).
* Optional: **Engagement_missing** flag.
  **Why:** NaN likely means no engagement history.

 

## 13. **AB_Bucket** (1.93% NaN)

**Type:** Categorical
**Recommendation:**

* Treat NaNs as **"NotInTest"**.
  **Why:** Users outside the experiment behave differently.

 

## 14. **Email_Interaction** (1.91% NaN)

**Type:** Binary {0,1}
**Recommendation:**

* Use:

  * **1 = interacted**
  * **0 = did not interact**
* Add **Email_Eligible** or **Email_Interaction_missing**.
  **Why:** NaN often means “not on email list.”

 

## 15. **Gender** (1.90% NaN)

**Type:** Binary {0,1}
**Recommendation:**

* Easiest: Leave NaN (XGBoost handles it).
* Or encode as **3-category**: male / female / unknown.
  **Why:** “Unknown” is a meaningful group.
