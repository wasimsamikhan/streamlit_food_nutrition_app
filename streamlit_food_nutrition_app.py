import streamlit as st
import pandas as pd

st.set_page_config(page_title="Food → Nutrition Calculator", layout="wide")

st.title("Food Consumption & Nutrition Calculator")

st.markdown("""
### Input CSV format

Upload a long-format CSV with:

- Household
- Person
- Adult_Equivalent_Fraction
- Food_Code
- Food_Quantity

Example:

```text
Household,Person,Adult_Equivalent_Fraction,Food_Code,Food_Quantity
1,1,5,30,100
1,1,5,247,60
1,2,5,357,50
1,3,5,30,80
```

The nutrition Excel database is loaded automatically from GitHub.

Excel structure:

- Column 1 = Food code
- Column 2 = English food name
- Column 3 = Bengali food name / translation
- Column 4 onward = nutrient values per 100 g
""")

# ============================================================
# NUTRITION DATABASE
# ============================================================

mapping_url = (
    "https://github.com/wasimsamikhan/"
    "streamlit_food_nutrition_app/raw/main/"
    "Food%20and%20Nutrition.xlsx"
)

st.header("1) Nutrition database")

mapping_df = None

try:
    mapping_df = pd.read_excel(mapping_url, header=0)
    mapping_df = mapping_df.dropna(axis=1, how="all")

    if len(mapping_df.columns) < 4:
        st.error(
            "The nutrition Excel must contain at least 4 columns."
        )
        mapping_df = None
    else:
        st.success(
            f"Nutrition database loaded successfully: "
            f"{len(mapping_df):,} food records × "
            f"{len(mapping_df.columns):,} columns"
        )

        st.dataframe(
            mapping_df.head(20),
            height=500,
            use_container_width=True
        )

except Exception as e:
    st.error(
        f"Failed to load the nutrition Excel file from GitHub: {e}"
    )

# ============================================================
# UPLOAD LONG-FORMAT CSV
# ============================================================

st.header("2) Upload food consumption CSV")

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
            f"{len(input_df):,} rows × "
            f"{len(input_df.columns):,} columns"
        )

        st.dataframe(
            input_df.head(50),
            height=500,
            use_container_width=True
        )

        st.info(
            f"Total rows in uploaded CSV: "
            f"{len(input_df):,}"
        )

    except Exception as e:
        st.error(f"Could not read the CSV file: {e}")

# ============================================================
# SELECT / CONFIRM INPUT COLUMNS
# ============================================================

if input_df is not None:

    st.header("3) Confirm input columns")

    all_columns = input_df.columns.tolist()

    household_col = st.selectbox(
        "Household column",
        options=all_columns,
        index=(
            all_columns.index("Household")
            if "Household" in all_columns else 0
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
# COMPUTE RESULTS
# ============================================================

st.header("4) Calculate results")

if st.button("Compute results", type="primary"):

    if input_df is None:
        st.error("Please upload your CSV file first.")
        st.stop()

    if mapping_df is None:
        st.error("The nutrition Excel file could not be loaded.")
        st.stop()

    if len(mapping_df.columns) < 4:
        st.error(
            "The nutrition Excel file does not have the required structure."
        )
        st.stop()

    data = input_df.copy()
    mapping = mapping_df.copy()

    map_code_col = mapping.columns[0]
    food_name_en_col = mapping.columns[1]
    food_name_bn_col = mapping.columns[2]
    nutrient_cols = list(mapping.columns[3:])

    # Clean input columns
    data[aef_col] = pd.to_numeric(
        data[aef_col], errors="coerce"
    )

    data[quantity_col] = pd.to_numeric(
        data[quantity_col], errors="coerce"
    ).fillna(0)

    data[food_code_col] = pd.to_numeric(
        data[food_code_col], errors="coerce"
    )

    # Remove rows with no food code
    data = data[data[food_code_col].notna()].copy()

    # Standardize food codes
    data[food_code_col] = (
        data[food_code_col]
        .astype("Int64")
        .astype(str)
    )

    # Clean Excel food codes
    mapping[map_code_col] = pd.to_numeric(
        mapping[map_code_col], errors="coerce"
    )

    mapping = mapping[mapping[map_code_col].notna()].copy()

    mapping[map_code_col] = (
        mapping[map_code_col]
        .astype("Int64")
        .astype(str)
    )

    # Prevent duplicate food codes from multiplying rows
    mapping = mapping.drop_duplicates(
        subset=[map_code_col],
        keep="first"
    )

    # Clean nutrient columns
    for col in nutrient_cols:
        mapping[col] = pd.to_numeric(
            mapping[col], errors="coerce"
        ).fillna(0)

    # Merge
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

    # Unmatched codes
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
            f"{len(unmatched):,} consumption rows contain "
            f"food codes not found in the nutrition Excel."
        )

        st.dataframe(
            pd.DataFrame({
                "Unmatched_Food_Code": unmatched_codes
            }),
            use_container_width=True
        )

    # Nutrient intake:
    # grams / 100 × nutrient value per 100g
    merged["Food_Quantity_Clean"] = pd.to_numeric(
        merged[quantity_col], errors="coerce"
    ).fillna(0)

    for col in nutrient_cols:
        merged[col] = (
            merged["Food_Quantity_Clean"] / 100.0
        ) * pd.to_numeric(
            merged[col], errors="coerce"
        ).fillna(0)

    # ========================================================
    # HOUSEHOLD TOTAL BY FOOD
    # ========================================================

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
        .dropna(subset=[aef_col])
        .drop_duplicates(
            subset=[household_col],
            keep="first"
        )
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

    # ========================================================
    # AVERAGE HOUSEHOLD = TOTAL / AEF
    # ========================================================

    average_household = household_total.copy()

    valid_aef = (
        pd.to_numeric(
            average_household[aef_col],
            errors="coerce"
        )
        .replace(0, pd.NA)
    )

    for col in ["Food_Quantity"] + nutrient_cols:
        average_household[col] = (
            pd.to_numeric(
                average_household[col],
                errors="coerce"
            ) / valid_aef
        )

    average_household = average_household.rename(
        columns={
            "Food_Quantity":
                "Food_Quantity_per_Adult_Equivalent"
        }
    )

    # ========================================================
    # PERSON-WISE TOTAL BY FOOD
    # ========================================================

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
        .dropna(subset=[aef_col])
        .drop_duplicates(
            subset=[household_col, person_col],
            keep="first"
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

    # ========================================================
    # DISPLAY
    # ========================================================

    st.success("Calculation completed successfully.")

    st.write(
        f"Household records: **{len(household_total):,}**"
    )

    st.write(
        f"Average household records: **{len(average_household):,}**"
    )

    st.write(
        f"Person-wise records: **{len(person_total):,}**"
    )

    st.subheader("1. Total household consumption")

    st.dataframe(
        household_total,
        height=700,
        use_container_width=True
    )

    st.subheader(
        "2. Average household consumption per Adult Equivalent"
    )

    st.dataframe(
        average_household,
        height=700,
        use_container_width=True
    )

    st.subheader("3. Person-wise consumption")

    st.dataframe(
        person_total,
        height=700,
        use_container_width=True
    )

    # ========================================================
    # COMPLETE CSV DOWNLOADS
    # ========================================================

    household_csv = household_total.to_csv(
        index=False
    ).encode("utf-8-sig")

    average_household_csv = average_household.to_csv(
        index=False
    ).encode("utf-8-sig")

    person_csv = person_total.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.subheader("Download complete results")

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

st.markdown("---")

st.caption(
    "All rows are retained during processing. "
    "The preview tables only limit what is initially displayed; "
    "the downloaded CSV files contain the complete results."
)
