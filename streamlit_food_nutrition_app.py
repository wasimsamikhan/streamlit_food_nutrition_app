# Streamlit app: Match person-food CSV to nutrition mapping and compute totals per person
# Save this file as streamlit_food_nutrition_app.py and run with:
# pip install streamlit pandas openpyxl
# streamlit run streamlit_food_nutrition_app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title='Food → Nutrition Mapper', layout='wide')
st.title('Food code → Nutrition mapper')

st.markdown(
    """Upload a CSV with 3 columns: **ID**, **Food code**, **Grams eaten**.\
    The app will automatically use the nutrition mapping Excel file stored in the GitHub repo (per 100 g values)
    to compute nutrition per person."""
)

# --- Upload CSV of consumption ---
st.header('1) Upload consumption CSV (your data)')
cons_file = st.file_uploader('Upload CSV with columns: ID, food_code, grams (first three columns used by default)', type=['csv'], key='cons')

example_btn = st.button('Show example CSV')
if example_btn:
    example_df = pd.DataFrame({
        'person_id': [1,1,2,3],
        'food_code': [101,102,101,103],
        'grams': [150, 80, 200, 50]
    })
    st.dataframe(example_df)

cons_df = None
if cons_file is not None:
    try:
        cons_df = pd.read_csv(cons_file)
    except Exception:
        cons_file.seek(0)
        cons_df = pd.read_csv(cons_file, encoding='latin1')
    st.success('Consumption file loaded')
    st.write('Preview (first 10 rows):')
    st.dataframe(cons_df.head(10))

# --- Load the nutrition mapping Excel from GitHub ---
st.header('2) Nutrition mapping (loaded automatically from GitHub)')

mapping_url = "https://github.com/wasimsamikhan/streamlit_food_nutrition_app/raw/main/Food%20and%20Nutrition.xlsx"
mapping_df = None
try:
    mapping_df = pd.read_excel(mapping_url, header=0)
    # Drop empty columns (like the 3rd one in your file)
    mapping_df = mapping_df.dropna(axis=1, how='all')
    # Ensure numeric conversion for nutrient columns
    for col in mapping_df.columns[3:]:
        mapping_df[col] = pd.to_numeric(mapping_df[col], errors='coerce').fillna(0)
    st.success('Nutrition mapping loaded successfully (values per 100 g)')
    st.write('Preview of nutrition mapping (first 10 rows):')
    st.dataframe(mapping_df.head(10))
except Exception as e:
    st.error('Failed to read the nutrition mapping Excel from GitHub: ' + str(e))

# --- Column mapping for consumption and mapping files ---
st.header('3) Map columns (auto-detected; you can override)')
if cons_df is not None:
    id_col = st.selectbox('Person ID column (consumption file)', options=list(cons_df.columns), index=0)
    code_col = st.selectbox('Food code column (consumption file)', options=list(cons_df.columns), index=1)
    grams_col = st.selectbox('Grams column (consumption file)', options=list(cons_df.columns), index=2)
else:
    id_col = code_col = grams_col = None

if mapping_df is not None:
    # First column is food code, second column is food name, third is empty
    map_code_col = mapping_df.columns[0]
    food_name_col = mapping_df.columns[1]
    # All remaining columns after the first three are nutrition columns
    chosen_nutrition_cols = list(mapping_df.columns[3:])
    st.write('Detected nutrition columns (per 100 g):', chosen_nutrition_cols)
else:
    map_code_col = None
    chosen_nutrition_cols = []

# --- Run mapping and calculation ---
st.header('4) Compute per-person nutrition totals')
if st.button('Compute results'):
    if cons_df is None:
        st.error('Please upload the consumption CSV first.')
    elif mapping_df is None:
        st.error('Could not load the nutrition mapping Excel from GitHub.')
    elif not chosen_nutrition_cols:
        st.error('No nutrition columns detected in mapping file.')
    else:
        cons = cons_df.copy()
        cons[grams_col] = pd.to_numeric(cons[grams_col].astype(str).str.replace(',',''), errors='coerce')
        missing_grams = cons[cons[grams_col].isna()]
        if len(missing_grams) > 0:
            st.warning(f'{len(missing_grams)} rows have non-numeric grams and will be treated as 0.')
            cons[grams_col] = cons[grams_col].fillna(0)

        map_df = mapping_df.copy()
        cons[code_col] = cons[code_col].astype(str).str.strip()
        map_df[map_code_col] = map_df[map_code_col].astype(str).str.strip()

        merged = pd.merge(cons, map_df[[map_code_col] + chosen_nutrition_cols], left_on=code_col, right_on=map_code_col, how='left')

        n_missing = merged[chosen_nutrition_cols].isna().all(axis=1).sum()
        if n_missing > 0:
            st.warning(f'{n_missing} consumption rows could not be matched to any food code in the mapping file. They will have NaNs for nutrition values.')

        for col in chosen_nutrition_cols:
            merged[col + '_for_grams'] = (merged[grams_col].astype(float) / 100.0) * merged[col].astype(float)

        agg_cols = [c + '_for_grams' for c in chosen_nutrition_cols]
        result = merged.groupby(id_col)[agg_cols].sum().reset_index()
        rename_map = {c + '_for_grams': c for c in chosen_nutrition_cols}
        result = result.rename(columns=rename_map)

        st.subheader('Per-person aggregated nutrition (computed from per-100 g values)')
        st.dataframe(result.head(200))

        unmatched = merged[merged[chosen_nutrition_cols].isna().all(axis=1)][[code_col]].drop_duplicates()
        if len(unmatched) > 0:
            st.warning('The following food codes from your consumption file had no match in the mapping file:')
            st.dataframe(unmatched)

        csv_bytes = result.to_csv(index=False).encode('utf-8')
        st.download_button('Download per-person nutrition CSV', data=csv_bytes, file_name='per_person_nutrition.csv', mime='text/csv')

        if st.checkbox('Show merged consumption -> mapping details (first 500 rows)'):
            st.dataframe(merged.head(500))

st.markdown('---')
st.caption('This app expects you to upload (1) a consumption CSV. The nutrition Excel file is loaded automatically from GitHub (per 100 g values). Excel format: col1=food code, col2=food name, col3 empty, col4+ = numeric nutrients per 100g.')
