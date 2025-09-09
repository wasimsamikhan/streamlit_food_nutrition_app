# Streamlit app: Wide-format food data → Nutrition mapping and totals (with manual column selection)
# Save this file as streamlit_food_nutrition_app.py and run with:
# pip install streamlit pandas openpyxl
# streamlit run streamlit_food_nutrition_app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title='Wide → Nutrition Mapper', layout='wide')
st.title('Wide-format Food Data → Nutrition Mapper')

st.markdown("""
Upload your **wide-format CSV** where each food_code column is followed by its quantity column.
Example:
```
Household, Person_id, food_code1, quantity, food_code2, quantity
1, 1, 30, 100, 234, 78
1, 2, 251, 60, 145, 58
```
""")

# --- Upload wide-format CSV ---
st.header('1) Upload wide-format consumption CSV')
cons_file = st.file_uploader('Upload your CSV', type=['csv'])

if cons_file:
    df_wide = pd.read_csv(cons_file)
    st.success('CSV loaded successfully')
    st.write('Preview:')
    st.dataframe(df_wide.head(10))
else:
    df_wide = None

# --- Select key columns ---
if df_wide is not None:
    st.header('2) Select household, person, food, and quantity columns')
    all_columns = df_wide.columns.tolist()

    household_col = st.selectbox('Select household column', options=all_columns)
    person_col = st.selectbox('Select person column', options=all_columns)

    food_cols = st.multiselect('Select all food code columns', options=all_columns)
    qty_cols = st.multiselect('Select all quantity columns (in same order as food codes)', options=all_columns)

# --- Load nutrition mapping from GitHub ---
st.header('3) Nutrition mapping (Excel from GitHub)')
mapping_url = "https://github.com/your-username/your-repo/raw/main/Food%20and%20Nutrition.xlsx"

try:
    mapping_df = pd.read_excel(mapping_url, header=0)
    mapping_df = mapping_df.dropna(axis=1, how='all')
    st.success('Nutrition mapping loaded successfully')
    st.write('Preview:')
    st.dataframe(mapping_df.head(10))
except Exception as e:
    st.error(f"Failed to load mapping: {e}")
    mapping_df = None

# --- Convert wide to long format ---
st.header('4) Convert to long format')
df_long = None
if df_wide is not None and food_cols and qty_cols:
    if len(food_cols) != len(qty_cols):
        st.error('Number of food code columns must match number of quantity columns!')
    else:
        long_data = []
        for _, row in df_wide.iterrows():
            household = row[household_col]
            person = row[person_col]
            for f_col, q_col in zip(food_cols, qty_cols):
                if pd.notna(row[f_col]) and pd.notna(row[q_col]):
                    long_data.append({
                        'household_id': household,
                        'person_id': person,
                        'food_code': row[f_col],
                        'grams': row[q_col]
                    })
        df_long = pd.DataFrame(long_data)
        st.success(f'Converted to long format with {len(df_long)} rows')
        st.dataframe(df_long.head(20))

# --- Process and compute ---
st.header('5) Compute household & person-wise nutrition totals')
if st.button('Compute results'):
    if df_long is None:
        st.error('Please complete previous steps first.')
    elif mapping_df is None:
        st.error('Nutrition mapping file not loaded.')
    else:
        map_code_col = mapping_df.columns[0]
        food_name_en_col = mapping_df.columns[1]
        food_name_bn_col = mapping_df.columns[2]
        nutrient_cols = mapping_df.columns[3:]

        df_long['food_code'] = df_long['food_code'].astype(str).str.strip()
        mapping_df[map_code_col] = mapping_df[map_code_col].astype(str).str.strip()

        merged = pd.merge(df_long,
                          mapping_df[[map_code_col, food_name_en_col, food_name_bn_col] + list(nutrient_cols)],
                          left_on='food_code', right_on=map_code_col, how='left')

        # Calculate nutrient intake per row
        for col in nutrient_cols:
            merged[col] = (merged['grams'].astype(float) / 100.0) * merged[col].astype(float)

        # --- Household-level totals ---
        household_totals = merged.groupby(['household_id', food_name_bn_col, food_name_en_col])[[*nutrient_cols]].sum().reset_index()

        # --- Person-level totals ---
        person_totals = merged.groupby(['person_id', food_name_bn_col, food_name_en_col])[[*nutrient_cols]].sum().reset_index()

        st.subheader('Household-level totals')
        st.dataframe(household_totals.head(50))

        st.subheader('Person-level totals')
        st.dataframe(person_totals.head(50))

        # Download buttons
        household_csv = household_totals.to_csv(index=False).encode('utf-8')
        person_csv = person_totals.to_csv(index=False).encode('utf-8')

        st.download_button('Download Household-level CSV',
                           data=household_csv, file_name='household_totals.csv', mime='text/csv')
        st.download_button('Download Person-level CSV',
                           data=person_csv, file_name='person_totals.csv', mime='text/csv')

st.caption('This app converts wide-format food data to long format, lets you select the relevant columns, and outputs two CSVs: household-level totals and person-level totals.')
