import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import io

@st.cache_data
# Load and cache all GADM Excel files at once
def load_all_data():
    """Load all GADM36 and GADM41, levels 0–5 into a dict and cache."""
    data = {}
    for version in ["36", "41"]:
        for level in range(6):
            filepath = f"gad{version}_level{level}.csv"
            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                # If a file is missing or corrupt, store empty DataFrame
                st.error(f"Loading failed: {filepath}\n{e}")
                df = pd.DataFrame()
            data[(version, level)] = df
    return data


def find_matches(query, df, level, version, threshold, gid0_filter=None):
    """
    Search for query in df; optionally filter by GID_0.
    """
    name_col = f"NAME_{level}"
    gid_col = f"GID_{level}"
    matches = []
    if name_col in df.columns and gid_col in df.columns:
        for _, row in df.iterrows():
            # Apply GID_0 filter if provided
            if gid0_filter:
                if 'GID_0' not in row or str(row['GID_0']) != gid0_filter:
                    continue
            db_name = str(row[name_col])
            score = fuzz.token_set_ratio(query, db_name)
            if score >= threshold:
                matches.append({
                    "query": query,
                    "version": version,
                    "level": level,
                    "GID_0": row.get('GID_0', ''),
                    "GID": row[gid_col],
                    "matched_name": db_name,
                    "score": score
                })
    return matches


def main():
    st.title("GADM City Name Matcher")
    st.markdown(
        "Match city names with GADM codes using fuzzy matching. "
        "Input city names in the format: `City Name|GID_0` (optional)."
    )
    threshold = st.sidebar.slider("Matching threshold", 0, 100, 80)

    raw_input = st.text_area(
        "City Name List",
        height=200,
        placeholder="Example：\nNew York City|USA\nNew York\nCiudad de México|MEX"
    )

    if st.button("开始匹配"):
        if not raw_input.strip():
            st.warning("Please enter at least one city name.")
            return

        # Parse entries: name and optional GID_0
        entries = []
        for line in raw_input.splitlines():
            if not line.strip():
                continue
            if '|' in line:
                name, gid0 = [part.strip() for part in line.split('|', 1)]
            else:
                name, gid0 = line.strip(), None
            entries.append({'query': name, 'gid0': gid0})

        # Load all data once
        data_dict = load_all_data()
        results = []
        for (ver, lvl), df in data_dict.items():
            for entry in entries:
                matches = find_matches(
                    entry['query'], df, lvl, ver, threshold, entry['gid0']
                )
                results.extend(matches)

        if results:
            df_res = pd.DataFrame(results)
            df_res.sort_values(["query", "score"], ascending=[True, False], inplace=True)
            st.dataframe(df_res)

            # Export to Excel
            output = io.BytesIO()
            df_res.to_excel(
                output,
                index=False,
                engine="openpyxl"
            )
            st.download_button(
                "Download result as Excel",
                data=output.getvalue(),
                file_name="matches.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info(
                "No matches found. "
                "Try adjusting the threshold or check your input format."
            )


if __name__ == "__main__":
    main()
