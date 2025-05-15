import streamlit as st
import pandas as pd
import re

# Cache CSV loading for performance
def load_csv(version_tag: str, level: int) -> pd.DataFrame:
    """
    Load the CSV file for a given GADM version and level.
    version_tag: '36' for GADM 3.6, '41' for GADM 4.1
    level: integer level (0-5)
    """
    filename = f"gad{version_tag}_level{level}.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"CSV file not found: {filename}")
        return pd.DataFrame()
    return df

@st.cache_data
def get_df(version_tag: str, level: int) -> pd.DataFrame:
    return load_csv(version_tag, level)

def parse_codes(text: str) -> list[str]:
    """
    Split user input into individual GID codes (comma/whitespace separated).
    """
    items = re.split(r"[\s,;]+", text.strip())
    return [code for code in items if code]

def main():
    st.title("GADM Code Query Tool")

    # Sidebar for version selection
    version = st.sidebar.selectbox("Select GADM Version:", ["3.6", "4.1"])
    version_map = {"3.6": "36", "4.1": "41"}
    version_tag = version_map[version]

    # Input area for multiple GID codes
    input_text = st.text_area(
        "Enter one or more GID codes (e.g. VNM.54.2_1), separated by commas, spaces, or new lines:",
        height=150
    )

    if input_text:
        codes = parse_codes(input_text)
        results = []
        not_found = []

        for code in codes:
            level = code.count('.')  # number of periods determines level
            df = get_df(version_tag, level)
            if df.empty:
                not_found.append((code, f"No data for level {level}"))
                continue

            gid_col = f"GID_{level}"
            if gid_col not in df.columns:
                st.error(f"Column {gid_col} not in CSV for level {level}.")
                continue

            match = df[df[gid_col] == code]
            if not match.empty:
                results.append(match)
            else:
                not_found.append((code, "No matching record"))

        if results:
            result_df = pd.concat(results, ignore_index=True)
            st.subheader("Query Results")
            st.dataframe(result_df)

            # Download button
            csv_bytes = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv_bytes,
                file_name="gadm_query_results.csv",
                mime="text/csv"
            )

        if not_found:
            st.subheader("Not Found / Errors")
            for code, msg in not_found:
                st.warning(f"{code}: {msg}")
    else:
        st.info("Please enter at least one GID code to begin.")

if __name__ == "__main__":
    main()
