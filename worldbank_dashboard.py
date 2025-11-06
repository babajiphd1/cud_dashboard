import streamlit as st
import pandas_datareader.wb as wb
import pandas as pd
import time


# -------------------------------
# App Title
# -------------------------------
st.set_page_config(page_title="World Bank Macro Dashboard", layout="wide")
st.title("🌍 ECGC - Country Review Dashboard")
st.write("Select a country - Key economic indicators (2000–2023).")

# -------------------------------
# Indicators List
# -------------------------------
indicators = {
    'NY.GDP.MKTP.CD': 'GDP (current US$)',
    'NY.GDP.PCAP.CD': 'GDP per capita (current US$)',
    'SP.URB.TOTL.IN.ZS': 'Urban population (% of total population)',
    'NE.TRD.GNFS.ZS': 'Merchandise trade (% of GDP)',
    'EG.IMP.CONS.ZS': 'Energy imports, net (% of energy use)',
    'SL.UEM.TOTL.ZS': 'Unemployment, total (% of labor force)',
    'SP.DYN.LE00.IN': 'Life expectancy at birth (years)',
    'MS.MIL.XPND.GD.ZS': 'Military expenditure (% of GDP)',
    'GC.TAX.TOTL.GD.ZS': 'Tax revenue (% of GDP)',
    'FS.AST.PRVT.GD.ZS': 'Domestic credit to private sector (% of GDP)',
    'SI.POV.GINI': 'Gini index',
    'FB.AST.NPER.ZS': 'Bank non-performing loans to total gross loans (%)',
    'CM.MKT.TRAD.GD.ZS': 'Stocks traded, total value (% of GDP)',
    'BX.TRF.PWKR.DT.GD.ZS': 'Personal remittances received (% of GDP)',
    'FR.INR.LNDP': 'Interest rate spread (lending rate minus deposit rate, %)',
    'BN.CAB.XOKA.GD.ZS': 'Current account balance (% of GDP)',
    #'EG.ELC.ACCS.ZS': 'Access to electricity (% of population)',
    'EG.USE.ELEC.KH.PC': 'Electric power consumption (kWh per capita)',
   # 'NY.GNS.ICTR.ZS': 'Gross savings (% of GDP)',
    #'AG.LND.AGRI.ZS': 'Agricultural land (% of land area)'
}

start_year = 2010
end_year = 2023

# -------------------------------
# Load available countries
# -------------------------------
@st.cache_data
def get_country_list():
    df = wb.get_countries()
    df = df[df['region'] != 'Aggregates']
    df = df.sort_values(by='name')
    return df

countries_df = get_country_list()

# -------------------------------
# Country Selection
# -------------------------------
country_name = st.selectbox(
    "🌐 Select Country",
    countries_df['name'].tolist(),
    index=countries_df['name'].tolist().index("India") if "India" in countries_df['name'].tolist() else 0
)

country_code = countries_df.loc[countries_df['name'] == country_name, 'iso2c'].values[0]

# -------------------------------
# Fetch World Bank Data
# -------------------------------
@st.cache_data


def fetch_data(country_code, max_retries=3, delay=5):
    frames = []
    progress = st.progress(0)
    steps = len(indicators) // 5 + 1
    for idx, i in enumerate(range(0, len(indicators), 5)):
        progress.progress((idx + 1) / steps)
        sub_indicators = list(indicators.keys())[i:i+5]
        attempt = 0
        success = False
        while attempt < max_retries and not success:
            try:
                df_chunk = wb.download(
                    indicator=sub_indicators,
                    country=country_code,
                    start=start_year,
                    end=end_year
                )
                frames.append(df_chunk)
                success = True
            except Exception as e:
                attempt += 1
                if attempt < max_retries:
                    st.warning(f"⚠️ Error fetching indicators {sub_indicators}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    st.error(f"❌ Failed to fetch {sub_indicators} after {max_retries} attempts. Error: {e}")

    if not frames:
        st.error("No data could be fetched from World Bank API.")
        return pd.DataFrame()

    df = pd.concat(frames, axis=1)
    df.rename(columns=indicators, inplace=True)
    df.reset_index(inplace=True)
    macro_df = df.pivot_table(index='year', values=list(indicators.values()))
    macro_df.sort_index(inplace=True)
    return macro_df

if st.button("📥 Fetch Data"):
    with st.spinner(f"Fetching World Bank data for {country_name}..."):
        macro_df = fetch_data(country_code)
        st.success(f"Data successfully fetched for {country_name}!")
        st.write("### 📊 Macro Indicators (2000–2023)")
        st.dataframe(macro_df.style.format("{:.2f}"))

        # -------------------------------
        # Charts
        # -------------------------------
        st.write("### 📈 Key Trends")

        selected_indicators = st.multiselect(
            "Select indicators to visualize:",
            list(indicators.values()),
            default=[
                'GDP (current US$)',
                'GDP per capita (current US$)',
                'Unemployment, total (% of labor force)'
            ]
        )

        if selected_indicators:
            st.line_chart(macro_df[selected_indicators])

        # -------------------------------
        # Download Option
        # -------------------------------
        excel_filename = f"WorldBank_MacroData_{country_name.replace(' ', '_')}.xlsx"
        macro_df.to_excel(excel_filename)

        with open(excel_filename, "rb") as f:
            st.download_button(
                label="⬇️ Download Data as Excel",
                data=f,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
