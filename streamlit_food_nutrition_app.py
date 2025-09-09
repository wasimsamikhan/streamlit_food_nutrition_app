# Streamlit app: Wide-format food data → Nutrition mapping and totals (Household & Person-wise)
# Save this file as streamlit_food_nutrition_app.py and run with:
# pip install streamlit pandas openpyxl
# streamlit run streamlit_food_nutrition_app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title='Wide → Nutrition Mapper', layout='wide')
st.title('Wide-format Food Data → Nutrition Mapper')

st.markdown("""
Upload your **wide-format CSV** where each food_code column is followed by a grams column.
Example:
```
household_id, person_id, food_code1, grams1, food_code2, grams2
1, 1, 30, 100, 247, 60
1, 2, 101, 200, 247, 80
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

# --- Load nutrition mapping from GitHub ---
st.header('2) Nutrition mapping (Excel from GitHub)')
mapping_url = "https://github.com/wasimsamikhan/streamlit_food_nutrition_app/raw/main/Food%20and%20Nutrition.xlsx"

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
st.header('3) Convert to long format')
if df_wide is not None:
    columns = df_wide.columns.tolist()
    household_col = 'household_id'
    person_col = 'person_id'
    food_cols = [col for col in columns if 'food_code' in col.lower()]

    long_data = []
    for _, row in df_wide.iterrows():
        household = row[household_col]
        person = row[person_col]
        for food_col in food_cols:
            num = ''.join(filter(str.isdigit, food_col))
            grams_col = f'grams{num}'
            if grams_col in columns and pd.notna(row[food_col]) and pd.notna(row[grams_col]):
                long_data.append({
                    'household_id': household,
                    'person_id': person,
                    'food_code': row[food_col],
                    'grams': row[grams_col]
                })

    df_long = pd.DataFrame(long_data)
    st.success(f'Converted to long format with {len(df_long)} rows')
    st.dataframe(df_long.head(20))
else:
    df_long = None

# --- Process and compute ---
st.header('4) Compute household & person-wise nutrition totals')
if st.button('Compute results'):
    if df_long is None:
        st.error('Please upload your wide-format CSV first.')
    elif mapping_df is None:
        st.error('Nutrition mapping file not loaded.')
    else:
        # Identify columns in mapping file
        map_code_col = mapping_df.columns[0]
        food_name_en_col = mapping_df.columns[1]
        food_name_bn_col = mapping_df.columns[2]  # Translation column
        nutrient_cols = mapping_df.columns[3:]

        # Merge
        df_long['food_code'] = df_long['food_code'].astype(str).str.strip()
        mapping_df[map_code_col] = mapping_df[map_code_col].astype(str).str.strip()

        merged = pd.merge(df_long,
                          mapping_df[[map_code_col, food_name_en_col, food_name_bn_col] + list(nutrient_cols)],
                          left_on='food_code', right_on=map_code_col, how='left')

        # Calculate nutrient intake per row
        for col in nutrient_cols:
            merged[col] = (merged['grams'].astype(float) / 100.0) * merged[col].astype(float)

        # --- 1) Household-level totals (no person ID) ---
        household_totals = merged.groupby(['household_id', food_name_bn_col, food_name_en_col])[[*nutrient_cols]].sum().reset_index()

        # --- 2) Person-level totals (no household ID) ---
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

st.caption('This app converts wide-format food data to long format, maps it to nutrition data, and outputs two CSVs: household-level totals (with Bengali & English names) and person-level totals.')
