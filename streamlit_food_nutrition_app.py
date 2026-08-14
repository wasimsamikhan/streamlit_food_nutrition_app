import streamlit as st
import pandas as pd

# ============================================================
# FOOD CONSUMPTION & NUTRITION CALCULATOR
# ============================================================
#
# INPUT CSV:
# Household | Person | Adult_Equivalent_Fraction | Food_Code | Food_Quantity
#
# The app calculates:
# 1. Household TOTAL across ALL foods -> one row per household
# 2. Average household TOTAL / AEF -> one row per household
# 3. Person TOTAL across ALL foods -> one row per person
#
# Nutrition Excel:
#   Column 1 = Food code
#   Column 2 = English food name
#   Column 3 = Bengali food name / translation
#   Column 4 onward = nutrient values per 100 g
# ============================================================

st.set_page_config(
    page_title="Food → Nutrition Calculator",
    layout="wide"
)

st.title("Food Consumption & Nutrition Calculator")

st.markdown("""
### Input CSV format

```text
Household,Person,Adult_Equivalent_Fraction,Food_Code,Food_Quantity
1034,1,5,30,100
1034,1,5,247,60
1034,1,5,357,50
1034,2,5,30,80
```

Each row represents one food eaten by one person.

The app will combine all food rows so that:

- **Household Total** = one row per household, all foods combined
- **Average Household** = household total ÷ AEF, one row per household
- **Person Total** = one row per person within each household, all foods combined
""")

# ============================================================
# NUTRITION DATABASE
# ============================================================

mapping_url = (
    "https://raw.githubusercontent.com/"
    "wasimsamikhan/streamlit_food_nutrition_app/"
    "main/Food%20and%20Nutrition.xlsx"
)

st.header("1) Nutrition database")

mapping_df = None

try:
    mapping_df = pd.read_excel(
        mapping_url,
        header=0
    )

    mapping_df = mapping_df.dropna(
        axis=1,
        how="all"
    )

    if len(mapping_df.columns) < 4:
        st.error(
            "The nutrition Excel must contain at least 4 columns."
        )
        mapping_df = None
    else:
        st.success(
            f"COMPLETE Excel loaded: "
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
        f"Failed to load the nutrition Excel from GitHub: {e}"
    )

# ============================================================
# UPLOAD LONG-FORMAT CSV
# ============================================================

st.header("2) Upload long-format food consumption CSV")

cons_file = st.file_uploader(
    "Upload your CSV",
    type=["csv"]
)

input_df = None

if cons_file is not None:

    try:
        input_df = pd.read_csv(cons_file)

        st.success(
            f"COMPLETE CSV loaded: "
            f"{len(input_df):,} rows × "
            f"{len(input_df.columns):,} columns"
        )

        st.dataframe(
            input_df.head(50),
            height=500,
            use_container_width=True
        )

    except Exception as e:
        st.error(
            f"Could not read the CSV file: {e}"
        )

# ============================================================
# SELECT COLUMNS
# ============================================================

if input_df is not None:

    st.header("3) Confirm input columns")

    all_columns = input_df.columns.tolist()

    household_col = st.selectbox(
        "Household column",
        all_columns,
        index=(
            all_columns.index("Household")
            if "Household" in all_columns else 0
        )
    )

    person_col = st.selectbox(
        "Person column",
        all_columns,
        index=(
            all_columns.index("Person")
            if "Person" in all_columns
            else min(1, len(all_columns) - 1)
        )
    )

    aef_col = st.selectbox(
        "Adult Equivalent Fraction (AEF) column",
        all_columns,
        index=(
            all_columns.index("Adult_Equivalent_Fraction")
            if "Adult_Equivalent_Fraction" in all_columns
            else min(2, len(all_columns) - 1)
        )
    )

    food_code_col = st.selectbox(
        "Food Code column",
        all_columns,
        index=(
            all_columns.index("Food_Code")
            if "Food_Code" in all_columns
            else min(3, len(all_columns) - 1)
        )
    )

    quantity_col = st.selectbox(
        "Food Quantity / grams column",
        all_columns,
        index=(
            all_columns.index("Food_Quantity")
            if "Food_Quantity" in all_columns
            else min(4, len(all_columns) - 1)
        )
    )

# ============================================================
# COMPUTE
# ============================================================

st.header("4) Calculate totals")

if st.button(
    "Compute results",
    type="primary"
):

    if input_df is None:
        st.error("Please upload your CSV first.")
        st.stop()

    if mapping_df is None:
        st.error("Nutrition Excel could not be loaded.")
        st.stop()

    data = input_df.copy()
    mapping = mapping_df.copy()

    # --------------------------------------------------------
    # EXCEL STRUCTURE
    # --------------------------------------------------------

    map_code_col = mapping.columns[0]
    food_name_en_col = mapping.columns[1]
    food_name_bn_col = mapping.columns[2]
    nutrient_cols = list(mapping.columns[3:])

    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

    data[quantity_col] = pd.to_numeric(
        data[quantity_col],
        errors="coerce"
    ).fillna(0)

    data[aef_col] = pd.to_numeric(
        data[aef_col],
        errors="coerce"
    )

    data[food_code_col] = pd.to_numeric(
        data[food_code_col],
        errors="coerce"
    )

    data = data[
        data[food_code_col].notna()
    ].copy()

    data[food_code_col] = (
        data[food_code_col]
        .astype("Int64")
        .astype(str)
    )

    # --------------------------------------------------------
    # CLEAN EXCEL
    # --------------------------------------------------------

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

    # One database record per food code.
    mapping = mapping.drop_duplicates(
        subset=[map_code_col],
        keep="first"
    )

    # Numeric nutrients; blanks become zero.
    for col in nutrient_cols:
        mapping[col] = pd.to_numeric(
            mapping[col],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    merged = pd.merge(
        data,
        mapping[
            [
                map_code_col,
                food_name_en_col,
                food_name_bn_col
            ] + nutrient_cols
        ],
        left_on=food_code_col,
        right_on=map_code_col,
        how="left"
    )

    # --------------------------------------------------------
    # SHOW UNMATCHED CODES
    # --------------------------------------------------------

    unmatched = merged[
        merged[food_name_en_col].isna()
    ]

    if len(unmatched) > 0:

        codes = (
            unmatched[food_code_col]
            .drop_duplicates()
            .tolist()
        )

        st.warning(
            f"{len(unmatched):,} input food rows could not be "
            "matched to the nutrition database."
        )

        st.dataframe(
            pd.DataFrame({
                "Unmatched_Food_Code": codes
            }),
            use_container_width=True
        )

    # --------------------------------------------------------
    # NUTRIENT INTAKE
    # --------------------------------------------------------
    #
    # Excel value = nutrient per 100 g
    #
    # Intake = quantity / 100 × nutrient per 100 g
    # --------------------------------------------------------

    merged["Food_Quantity_Clean"] = pd.to_numeric(
        merged[quantity_col],
        errors="coerce"
    ).fillna(0)

    for col in nutrient_cols:

        merged[col] = (
            merged["Food_Quantity_Clean"] / 100.0
        ) * pd.to_numeric(
            merged[col],
            errors="coerce"
        ).fillna(0)

    # ========================================================
    # A. HOUSEHOLD TOTAL
    #
    # ONE ROW PER HOUSEHOLD.
    #
    # ALL FOODS OF THAT HOUSEHOLD ARE SUMMED TOGETHER.
    # ========================================================

    household_total = (
        merged
        .groupby(
            household_col,
            dropna=False
        )[
            ["Food_Quantity_Clean"] + nutrient_cols
        ]
        .sum()
        .reset_index()
    )

    household_total = household_total.rename(
        columns={
            "Food_Quantity_Clean":
                "Total_Food_Quantity"
        }
    )

    # Add household AEF.
    household_aef = (
        data[
            [
                household_col,
                aef_col
            ]
        ]
        .dropna(
            subset=[aef_col]
        )
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
            "Total_Food_Quantity"
        ] + nutrient_cols
    ]

    # ========================================================
    # B. AVERAGE HOUSEHOLD
    #
    # ONE ROW PER HOUSEHOLD.
    #
    # Every household total is divided by its AEF.
    # ========================================================

    average_household = household_total.copy()

    valid_aef = (
        pd.to_numeric(
            average_household[aef_col],
            errors="coerce"
        )
        .replace(0, pd.NA)
    )

    for col in (
        ["Total_Food_Quantity"] +
        nutrient_cols
    ):

        average_household[col] = (
            pd.to_numeric(
                average_household[col],
                errors="coerce"
            )
            / valid_aef
        )

    average_household = average_household.rename(
        columns={
            "Total_Food_Quantity":
                "Food_Quantity_per_Adult_Equivalent"
        }
    )

    # ========================================================
    # C. PERSON TOTAL
    #
    # ONE ROW PER PERSON WITHIN EACH HOUSEHOLD.
    #
    # ALL FOODS EATEN BY THAT PERSON ARE SUMMED TOGETHER.
    #
    # Household + Person is the unique identifier.
    # ========================================================

    person_total = (
        merged
        .groupby(
            [
                household_col,
                person_col
            ],
            dropna=False
        )[
            ["Food_Quantity_Clean"] + nutrient_cols
        ]
        .sum()
        .reset_index()
    )

    person_total = person_total.rename(
        columns={
            "Food_Quantity_Clean":
                "Total_Food_Quantity"
        }
    )

    # Add AEF.
    person_aef = (
        data[
            [
                household_col,
                person_col,
                aef_col
            ]
        ]
        .dropna(
            subset=[aef_col]
        )
        .drop_duplicates(
            subset=[
                household_col,
                person_col
            ],
            keep="first"
        )
    )

    person_total = person_total.merge(
        person_aef,
        on=[
            household_col,
            person_col
        ],
        how="left"
    )

    person_total = person_total[
        [
            household_col,
            person_col,
            aef_col,
            "Total_Food_Quantity"
        ] + nutrient_cols
    ]

    # ========================================================
    # DISPLAY
    # ========================================================

    st.success(
        "Calculation completed."
    )

    st.metric(
        "Number of households",
        f"{len(household_total):,}"
    )

    st.metric(
        "Number of persons",
        f"{len(person_total):,}"
    )

    # --------------------------------------------------------
    # HOUSEHOLD TOTAL
    # --------------------------------------------------------

    st.subheader(
        "1. Household total — ALL foods combined"
    )

    st.dataframe(
        household_total,
        height=600,
        use_container_width=True
    )

    # --------------------------------------------------------
    # AVERAGE HOUSEHOLD
    # --------------------------------------------------------

    st.subheader(
        "2. Average household — Household total ÷ AEF"
    )

    st.dataframe(
        average_household,
        height=600,
        use_container_width=True
    )

    # --------------------------------------------------------
    # PERSON TOTAL
    # --------------------------------------------------------

    st.subheader(
        "3. Person total — ALL foods combined"
    )

    st.dataframe(
        person_total,
        height=600,
        use_container_width=True
    )

    # ========================================================
    # COMPLETE DOWNLOADS
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

    st.subheader(
        "Download complete results"
    )

    st.download_button(
        label=(
            f"Download Household Total CSV "
            f"({len(household_total):,} households)"
        ),
        data=household_csv,
        file_name="household_total_consumption.csv",
        mime="text/csv"
    )

    st.download_button(
        label=(
            f"Download Average Household CSV "
            f"({len(average_household):,} households)"
        ),
        data=average_household_csv,
        file_name="average_household_consumption.csv",
        mime="text/csv"
    )

    st.download_button(
        label=(
            f"Download Person Total CSV "
            f"({len(person_total):,} persons)"
        ),
        data=person_csv,
        file_name="person_total_consumption.csv",
        mime="text/csv"
    )

st.markdown("---")

st.caption(
    "Household results contain one row per household. "
    "Person results contain one row per person within household. "
    "All foods are summed together within each household/person."
)
