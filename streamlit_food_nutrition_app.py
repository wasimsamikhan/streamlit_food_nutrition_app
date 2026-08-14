# ============================================================
# STREAMLIT FOOD CONSUMPTION & NUTRITION CALCULATOR
# ============================================================
#
# INPUT CSV FORMAT:
#
# Household | Person | Adult_Equivalent_Fraction | Food_Code | Food_Quantity
#
# Example:
#
# Household,Person,Adult_Equivalent_Fraction,Food_Code,Food_Quantity
# 1,1,5,30,100
# 1,1,5,247,60
# 1,2,5,357,50
# 1,3,5,30,80
#
# The Excel nutrition database contains:
#
# Column 1 = Food code
# Column 2 = English food name
# Column 3 = Bengali food name / translation
# Column 4 onward = nutrients per 100 g
#
# OUTPUTS:
#
# 1. Household total consumption CSV
# 2. Average household consumption CSV
# 3. Person-wise consumption CSV
#
# ============================================================

import streamlit as st
import pandas as pd


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Food → Nutrition Calculator",
    layout="wide"
)

st.title("Food Consumption & Nutrition Calculator")

st.markdown("""
### Required CSV format

Upload a **long-format CSV** with exactly five columns:

1. **Household**
2. **Person**
3. **Adult_Equivalent_Fraction**
4. **Food_Code**
5. **Food_Quantity**

Example:

```text
Household,Person,Adult_Equivalent_Fraction,Food_Code,Food_Quantity
1,1,5,30,100
1,1,5,247,60
1,2,5,357,50
1,3,5,30,80
""") 
# ============================================================
# GITHUB NUTRITION FILE
# ============================================================

mapping_url = (
"https://github.com/wasimsamikhan/"
"streamlit_food_nutrition_app/raw/main/"
"Food%20and%20Nutrition.xlsx"
)

# ============================================================
# 1. UPLOAD CSV
# ============================================================

st.header("1) Upload food consumption CSV")

cons_file = st.file_uploader(
"Upload your long-format CSV",
type=["csv"]
)

df_long = None

if cons_file is not None:

    try:


        df_long = pd.read_csv(cons_file)
    
    
        st.success(
            f"CSV loaded successfully: "
            f"{len(df_long):,} rows × "
            f"{len(df_long.columns):,} columns"
        )
    
    
        st.write("### Uploaded data preview")
    
    
        st.dataframe(
            df_long.head(50),
            height=500,
            use_container_width=True
        )
    
    
        st.info(
            f"The uploaded CSV contains {len(df_long):,} rows. "
            "All rows will be retained during processing."
        )
    

    except Exception as e:


        st.error(
            f"Could not read the CSV file: {e}"
        )
    
    
        df_long = None
# ============================================================
# 2. VALIDATE / SELECT INPUT COLUMNS
# ============================================================

if df_long is not None:

    st.header("2) Confirm input columns")


all_columns = df_long.columns.tolist()


st.write(
    "Select the corresponding columns below. "
    "This allows the app to work even if your headers "
    "have slightly different names."
)


household_col = st.selectbox(
    "Household column",
    options=all_columns,
    index=(
        all_columns.index("Household")
        if "Household" in all_columns
        else 0
    )
)


person_col = st.selectbox(
    "Person column",
    options=all_columns,
    index=(
        all_columns.index("Person")
        if "Person" in all_columns
        else min(1, len(all_columns) - 1)
    )
)


aef_col = st.selectbox(
    "Adult Equivalent Fraction (AEF) column",
    options=all_columns,
    index=(
        all_columns.index("Adult_Equivalent_Fraction")
        if "Adult_Equivalent_Fraction" in all_columns
        else min(2, len(all_columns) - 1)
    )
)


food_code_col = st.selectbox(
    "Food Code column",
    options=all_columns,
    index=(
        all_columns.index("Food_Code")
        if "Food_Code" in all_columns
        else min(3, len(all_columns) - 1)
    )
)


quantity_col = st.selectbox(
    "Food Quantity / Grams column",
    options=all_columns,
    index=(
        all_columns.index("Food_Quantity")
        if "Food_Quantity" in all_columns
        else min(4, len(all_columns) - 1)
    )
)
# ============================================================
# 3. LOAD NUTRITION EXCEL FROM GITHUB
# ============================================================

st.header("3) Nutrition database")

mapping_df = None

    try:

    mapping_df = pd.read_excel(
        mapping_url,
        header=0
    )
    
    
    # Remove columns that are completely empty.
    mapping_df = mapping_df.dropna(
        axis=1,
        how="all"
    )
    
    
    st.success(
        f"Nutrition Excel loaded successfully: "
        f"{len(mapping_df):,} food records × "
        f"{len(mapping_df.columns):,} columns"
    )
    
    
    st.write("### Nutrition database preview")
    
    
    st.dataframe(
        mapping_df.head(20),
        height=500,
        use_container_width=True
    )

    except Exception as e:

    st.error(
        f"Failed to load nutrition mapping from GitHub: {e}"
    )
    
    
    mapping_df = None
# ============================================================
# 4. PROCESS DATA
# ============================================================

st.header("4) Calculate household and person nutrition")

if st.button(
"Compute results",
type="primary"
):
# --------------------------------------------------------
# BASIC VALIDATION
# --------------------------------------------------------

if df_long is None:

    st.error(
        "Please upload your CSV file first."
    )

    st.stop()

if mapping_df is None:

    st.error(
        "The nutrition Excel file could not be loaded."
    )

    st.stop()

# --------------------------------------------------------
# CHECK THAT THE EXCEL HAS AT LEAST 4 COLUMNS
# --------------------------------------------------------

if len(mapping_df.columns) < 4:

    st.error(
        "The nutrition Excel must contain at least "
        "four columns: food code, English name, "
        "translation, and at least one nutrient."
    )

    st.stop()

# --------------------------------------------------------
# CREATE CLEAN COPY
# --------------------------------------------------------

data = df_long.copy()
mapping = mapping_df.copy()

# --------------------------------------------------------
# IDENTIFY EXCEL COLUMNS
# --------------------------------------------------------

map_code_col = mapping.columns[0]

food_name_en_col = mapping.columns[1]

food_name_bn_col = mapping.columns[2]

nutrient_cols = list(
    mapping.columns[3:]
)

# --------------------------------------------------------
# CLEAN HOUSEHOLD / PERSON / AEF
# --------------------------------------------------------

data[household_col] = data[household_col]

data[person_col] = data[person_col]

data[aef_col] = pd.to_numeric(
    data[aef_col],
    errors="coerce"
)

data[quantity_col] = pd.to_numeric(
    data[quantity_col],
    errors="coerce"
)

# Empty quantity = zero consumption
data[quantity_col] = (
    data[quantity_col]
    .fillna(0)
)

# --------------------------------------------------------
# FOOD CODE CLEANING
# --------------------------------------------------------

# Convert uploaded food codes to numeric first.
# This handles codes such as:
#
# 30
# 30.0
# "30"
# "30 "
#
data[food_code_col] = pd.to_numeric(
    data[food_code_col],
    errors="coerce"
)

# Remove rows with no food code.
data = data[
    data[food_code_col].notna()
].copy()

# Food codes should be integer-like.
data[food_code_col] = (
    data[food_code_col]
    .astype("Int64")
    .astype(str)
)

# Clean mapping food codes.
mapping[map_code_col] = pd.to_numeric(
    mapping[map_code_col],
    errors="coerce"
)

mapping = mapping[
    mapping[map_code_col].notna()
].copy()

mapping[map_code_col] = (
    mapping[map_code_col]
    .astype("Int64")
    .astype(str)
)

# --------------------------------------------------------
# CONVERT NUTRIENT COLUMNS TO NUMERIC
# --------------------------------------------------------

for col in nutrient_cols:

    mapping[col] = pd.to_numeric(
        mapping[col],
        errors="coerce"
    )

    # Empty nutrient values are treated as zero.
    mapping[col] = (
        mapping[col]
        .fillna(0)
    )

# --------------------------------------------------------
# MERGE CONSUMPTION WITH NUTRITION DATABASE
# --------------------------------------------------------

mapping_subset = mapping[
    [
        map_code_col,
        food_name_en_col,
        food_name_bn_col
    ] + nutrient_cols
].copy()

merged = pd.merge(
    data,
    mapping_subset,
    left_on=food_code_col,
    right_on=map_code_col,
    how="left"
)

# --------------------------------------------------------
# CHECK UNMATCHED FOOD CODES
# --------------------------------------------------------

unmatched = merged[
    merged[food_name_en_col].isna()
].copy()

if len(unmatched) > 0:

    unmatched_codes = (
        unmatched[food_code_col]
        .drop_duplicates()
        .tolist()
    )

    st.warning(
        f"{len(unmatched):,} consumption rows "
        f"contain food codes not found in the Excel database."
    )

    st.write(
        "### Unmatched food codes"
    )

    st.dataframe(
        pd.DataFrame(
            {
                "Food_Code": unmatched_codes
            }
        ),
        use_container_width=True
    )

# --------------------------------------------------------
# CALCULATE NUTRIENT INTAKE
#
# Excel nutrient values = amount per 100 g
#
# Intake =
#
# Food quantity / 100 × nutrient value per 100 g
#
# --------------------------------------------------------

merged["Food_Quantity_Clean"] = (
    pd.to_numeric(
        merged[quantity_col],
        errors="coerce"
    )
    .fillna(0)
)

for col in nutrient_cols:

    merged[col] = (
        merged["Food_Quantity_Clean"] / 100.0
    ) * pd.to_numeric(
        merged[col],
        errors="coerce"
    ).fillna(0)

# ========================================================
# 5. HOUSEHOLD TOTAL CONSUMPTION
# ========================================================
#
# Each household + each food.
#
# Example:
#
# Household 1 | Rice | 500 g | 650 kcal | ...
#
# ========================================================

household_total = (
    merged
    .groupby(
        [
            household_col,
            food_name_bn_col,
            food_name_en_col
        ],
        dropna=False
    )
    [
        ["Food_Quantity_Clean"] + nutrient_cols
    ]
    .sum()
    .reset_index()
)

household_total = household_total.rename(
    columns={
        "Food_Quantity_Clean": "Food_Quantity"
    }
)

# Add AEF to household output.
#
# AEF should be the same for all records
# belonging to a household.
#

household_aef = (
    data[
        [
            household_col,
            aef_col
        ]
    ]
    .drop_duplicates()
)

household_total = household_total.merge(
    household_aef,
    on=household_col,
    how="left"
)

# Put columns in sensible order.
household_total = household_total[
    [
        household_col,
        aef_col,
        food_name_bn_col,
        food_name_en_col,
        "Food_Quantity"
    ] + nutrient_cols
]

# ========================================================
# 6. AVERAGE HOUSEHOLD CONSUMPTION
# ========================================================
#
# Household total / AEF
#
# Example:
#
# Household total protein = 50 g
# Household AEF = 4.5
#
# Average household protein =
#
# 50 / 4.5 = 11.11 g per adult equivalent
#
# ========================================================

average_household = household_total.copy()

# Identify columns that should be divided by AEF.
divide_cols = [
    "Food_Quantity"
] + nutrient_cols

for col in divide_cols:

    average_household[
        col
    ] = (
        pd.to_numeric(
            average_household[col],
            errors="coerce"
        )
        /
        pd.to_numeric(
            average_household[aef_col],
            errors="coerce"
        )
    )

# Rename the quantity to make its meaning clear.
average_household = average_household.rename(
    columns={
        "Food_Quantity":
            "Food_Quantity_per_Adult_Equivalent"
    }
)

# ========================================================
# 7. PERSON-WISE CONSUMPTION
# ========================================================
#
# Person + each food item.
#
# Household number is retained so the person can still
# be linked to the household.
#
# ========================================================

person_total = (
    merged
    .groupby(
        [
            household_col,
            person_col,
            food_name_bn_col,
            food_name_en_col
        ],
        dropna=False
    )
    [
        ["Food_Quantity_Clean"] + nutrient_cols
    ]
    .sum()
    .reset_index()
)

person_total = person_total.rename(
    columns={
        "Food_Quantity_Clean": "Food_Quantity"
    }
)

# Add AEF to person-level output.
person_aef = (
    data[
        [
            household_col,
            person_col,
            aef_col
        ]
    ]
    .drop_duplicates()
)

person_total = person_total.merge(
    person_aef,
    on=[
        household_col,
        person_col
    ],
    how="left"
)

# Put columns in logical order.
person_total = person_total[
    [
        household_col,
        person_col,
        aef_col,
        food_name_bn_col,
        food_name_en_col,
        "Food_Quantity"
    ] + nutrient_cols
]

# ========================================================
# 8. SHOW RESULTS
# ========================================================

st.success(
    "Calculation completed successfully."
)

st.write(
    f"Household × food records: "
    f"**{len(household_total):,}**"
)

st.write(
    f"Average household × food records: "
    f"**{len(average_household):,}**"
)

st.write(
    f"Person × food records: "
    f"**{len(person_total):,}**"
)

# --------------------------------------------------------
# HOUSEHOLD TOTAL
# --------------------------------------------------------

st.subheader(
    "1. Total household consumption"
)

st.dataframe(
    household_total,
    height=700,
    use_container_width=True
)

# --------------------------------------------------------
# AVERAGE HOUSEHOLD
# --------------------------------------------------------

st.subheader(
    "2. Average household consumption per Adult Equivalent"
)

st.dataframe(
    average_household,
    height=700,
    use_container_width=True
)

# --------------------------------------------------------
# PERSON
# --------------------------------------------------------

st.subheader(
    "3. Person-wise consumption"
)

st.dataframe(
    person_total,
    height=700,
    use_container_width=True
)

# ========================================================
# 9. COMPLETE CSV DOWNLOADS
# ========================================================
#
# IMPORTANT:
#
# There is NO .head() here.
#
# Therefore every row in the dataframe is exported.
#
# ========================================================

household_csv = (
    household_total
    .to_csv(
        index=False
    )
    .encode("utf-8-sig")
)

average_household_csv = (
    average_household
    .to_csv(
        index=False
    )
    .encode("utf-8-sig")
)

person_csv = (
    person_total
    .to_csv(
        index=False
    )
    .encode("utf-8-sig")
)

# ========================================================
# DOWNLOAD BUTTONS
# ========================================================

st.subheader(
    "Download complete results"
)

st.download_button(
    label=(
        f"Download Household Total CSV "
        f"({len(household_total):,} rows)"
    ),
    data=household_csv,
    file_name="household_total_consumption.csv",
    mime="text/csv"
)

st.download_button(
    label=(
        f"Download Average Household CSV "
        f"({len(average_household):,} rows)"
    ),
    data=average_household_csv,
    file_name="average_household_consumption.csv",
    mime="text/csv"
)

st.download_button(
    label=(
        f"Download Person-wise CSV "
        f"({len(person_total):,} rows)"
    ),
    data=person_csv,
    file_name="person_wise_consumption.csv",
    mime="text/csv"
)
============================================================
FOOTER
============================================================

st.markdown("---")

st.caption(
"All uploaded and calculated rows are retained. "
"The displayed tables are scrollable, and the download "
"buttons export the complete datasets without row limits."
)
