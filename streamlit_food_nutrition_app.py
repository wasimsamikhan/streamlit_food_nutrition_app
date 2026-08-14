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

# --- Upload CSV ---
cons_file = st.file_uploader(
    "Upload your long-format CSV",
    type=["csv"]
)

input_df = None

if cons_file is not None:
    try:
        input_df = pd.read_csv(cons_file)

        st.success(
            f"CSV loaded successfully: "
            f"{len(input_df):,} rows × {len(input_df.columns):,} columns"
        )

        st.dataframe(
            input_df.head(50),
            height=500,
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Could not read the CSV file: {e}")


# --- Select columns from the already-long CSV ---
if input_df is not None:

    st.header("2) Confirm input columns")

    all_columns = input_df.columns.tolist()

    household_col = st.selectbox(
        "Household column",
        all_columns,
        index=all_columns.index("Household")
        if "Household" in all_columns else 0
    )

    person_col = st.selectbox(
        "Person column",
        all_columns,
        index=all_columns.index("Person")
        if "Person" in all_columns else 1
    )

    aef_col = st.selectbox(
        "Adult Equivalent Fraction (AEF)",
        all_columns,
        index=all_columns.index("Adult_Equivalent_Fraction")
        if "Adult_Equivalent_Fraction" in all_columns else 2
    )

    food_code_col = st.selectbox(
        "Food Code",
        all_columns,
        index=all_columns.index("Food_Code")
        if "Food_Code" in all_columns else 3
    )

    quantity_col = st.selectbox(
        "Food Quantity",
        all_columns,
        index=all_columns.index("Food_Quantity")
        if "Food_Quantity" in all_columns else 4
    )


# --- Inside Compute results ---
if st.button("Compute results", type="primary"):

    if input_df is None:
        st.error("Please upload your CSV first.")
        st.stop()

    if mapping_df is None:
        st.error("Nutrition mapping file was not loaded.")
        st.stop()

    # Work directly from uploaded long-format CSV
    data = input_df.copy()
    mapping = mapping_df.copy()

    # Excel structure
    map_code_col = mapping.columns[0]
    food_name_en_col = mapping.columns[1]
    food_name_bn_col = mapping.columns[2]
    nutrient_cols = list(mapping.columns[3:])

    # Clean input
    data[aef_col] = pd.to_numeric(data[aef_col], errors="coerce")
    data[quantity_col] = pd.to_numeric(
        data[quantity_col], errors="coerce"
    ).fillna(0)

    data[food_code_col] = pd.to_numeric(
        data[food_code_col], errors="coerce"
    )

    data = data[data[food_code_col].notna()].copy()

    data[food_code_col] = (
        data[food_code_col]
        .astype("Int64")
        .astype(str)
    )

    # Clean Excel food codes
    mapping[map_code_col] = pd.to_numeric(
        mapping[map_code_col],
        errors="coerce"
    )

    mapping = mapping[mapping[map_code_col].notna()].copy()

    mapping[map_code_col] = (
        mapping[map_code_col]
        .astype("Int64")
        .astype(str)
    )

    # Clean nutrients
    for col in nutrient_cols:
        mapping[col] = pd.to_numeric(
            mapping[col],
            errors="coerce"
        ).fillna(0)

    # Merge
    merged = pd.merge(
        data,
        mapping[
            [map_code_col, food_name_en_col, food_name_bn_col]
            + nutrient_cols
        ],
        left_on=food_code_col,
        right_on=map_code_col,
        how="left"
    )

    # Calculate actual intake from per-100g values
    merged["Food_Quantity_Clean"] = pd.to_numeric(
        merged[quantity_col],
        errors="coerce"
    ).fillna(0)

    for col in nutrient_cols:
        merged[col] = (
            merged["Food_Quantity_Clean"] / 100
        ) * pd.to_numeric(
            merged[col],
            errors="coerce"
        ).fillna(0)

    # -------------------------------------------------
    # HOUSEHOLD TOTAL
    # -------------------------------------------------

    household_total = (
        merged.groupby(
            [
                household_col,
                food_name_bn_col,
                food_name_en_col
            ],
            dropna=False
        )[["Food_Quantity_Clean"] + nutrient_cols]
        .sum()
        .reset_index()
        .rename(
            columns={"Food_Quantity_Clean": "Food_Quantity"}
        )
    )

    household_aef = (
        data[[household_col, aef_col]]
        .drop_duplicates(subset=[household_col])
    )

    household_total = household_total.merge(
        household_aef,
        on=household_col,
        how="left"
    )

    household_total = household_total[
        [
            household_col,
            aef_col,
            food_name_bn_col,
            food_name_en_col,
            "Food_Quantity"
        ] + nutrient_cols
    ]

    # -------------------------------------------------
    # AVERAGE HOUSEHOLD = TOTAL / AEF
    # -------------------------------------------------

    average_household = household_total.copy()

    for col in ["Food_Quantity"] + nutrient_cols:
        average_household[col] = (
            average_household[col]
            / average_household[aef_col]
        )

    average_household = average_household.rename(
        columns={
            "Food_Quantity":
            "Food_Quantity_per_Adult_Equivalent"
        }
    )

    # -------------------------------------------------
    # PERSON-WISE TOTAL
    # -------------------------------------------------

    person_total = (
        merged.groupby(
            [
                household_col,
                person_col,
                food_name_bn_col,
                food_name_en_col
            ],
            dropna=False
        )[["Food_Quantity_Clean"] + nutrient_cols]
        .sum()
        .reset_index()
        .rename(
            columns={"Food_Quantity_Clean": "Food_Quantity"}
        )
    )

    person_aef = (
        data[
            [
                household_col,
                person_col,
                aef_col
            ]
        ]
        .drop_duplicates(
            subset=[household_col, person_col]
        )
    )

    person_total = person_total.merge(
        person_aef,
        on=[household_col, person_col],
        how="left"
    )

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

    # -------------------------------------------------
    # DISPLAY EVERYTHING
    # -------------------------------------------------

    st.dataframe(
        household_total,
        height=700,
        use_container_width=True
    )

    st.dataframe(
        average_household,
        height=700,
        use_container_width=True
    )

    st.dataframe(
        person_total,
        height=700,
        use_container_width=True
    )

    # -------------------------------------------------
    # COMPLETE DOWNLOADS — NO HEAD()
    # -------------------------------------------------

    st.download_button(
        "Download Household Total CSV",
        household_total.to_csv(index=False).encode("utf-8-sig"),
        "household_total_consumption.csv",
        "text/csv"
    )

    st.download_button(
        "Download Average Household CSV",
        average_household.to_csv(index=False).encode("utf-8-sig"),
        "average_household_consumption.csv",
        "text/csv"
    )

    st.download_button(
        "Download Person-wise CSV",
        person_total.to_csv(index=False).encode("utf-8-sig"),
        "person_wise_consumption.csv",
        "text/csv"
    )
# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
"All uploaded and calculated rows are retained. "
"The displayed tables are scrollable, and the download "
"buttons export the complete datasets without row limits."
)
