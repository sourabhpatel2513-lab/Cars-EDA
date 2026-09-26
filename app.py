
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Cars EDA Dashboard",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Used Cars Analysis Dashboard")
st.markdown(
    "Interactive dashboard for analyzing used cars, "
    "prices, fuel types, and car features."
)

# ==========================================
# 2. LOAD DATA
# ==========================================

@st.cache_data
def load_data(file):
    if file is not None:
        df = pd.read_csv(file)
    else:
        df = pd.read_csv("Cars.csv")

    df.columns = df.columns.str.strip()
    return df


st.sidebar.header("📂 Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload Cars CSV",
    type=["csv"]
)

try:
    df = load_data(uploaded_file)
except FileNotFoundError:
    st.error("Please upload Cars.csv or place it beside app.py.")
    st.stop()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# ==========================================
# 3. DATA CLEANING
# ==========================================

numeric_columns = [
    "Price",
    "Year",
    "Kilometers_Driven",
    "Mileage",
    "Engine",
    "Power",
    "Seats"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str)
                   .str.replace(",", "", regex=False)
                   .str.replace(r"[^\d.\-]", "", regex=True),
            errors="coerce"
        )

# Identify car name column
name_col = next(
    (c for c in ["Name", "Car_Name", "Model"] if c in df.columns),
    None
)

# Create brand column
if name_col:
    df["Brand"] = (
        df[name_col]
        .fillna("")
        .astype(str)
        .str.split()
        .str[0]
    )

# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================

st.sidebar.header("🔎 Advanced Filters")

filtered = df.copy()


# Categorical filter function
def categorical_filter(data, column, label):

    if column not in data.columns:
        return data

    options = sorted(
        data[column].dropna().astype(str).unique().tolist()
    )

    selected = st.sidebar.multiselect(
        label,
        options,
        default=options
    )

    if len(selected) == 0:
        return data.iloc[0:0]

    return data[
        data[column].astype(str).isin(selected)
    ]


# Brand filter
if "Brand" in filtered.columns:

    brands = sorted(
        filtered["Brand"].replace("", pd.NA)
        .dropna().unique().tolist()
    )

    selected_brands = st.sidebar.multiselect(
        "Select Brand",
        brands,
        default=brands
    )

    filtered = filtered[
        filtered["Brand"].isin(selected_brands)
    ]


# Other categorical filters
filters = [
    ("Location", "Select Location"),
    ("Fuel_Type", "Select Fuel Type"),
    ("Transmission", "Select Transmission"),
    ("Owner_Type", "Select Owner Type"),
    ("Seller_Type", "Select Seller Type"),
    ("Seats", "Select Seats")
]

for column, label in filters:

    filtered = categorical_filter(
        filtered,
        column,
        label
    )


# Numeric range filter
def range_filter(data, column, label, step=None):

    if column not in data.columns:
        return data

    values = data[column].dropna()

    if values.empty:
        return data

    minimum = float(values.min())
    maximum = float(values.max())

    if minimum == maximum:
        return data

    if step is None:
        step = max((maximum - minimum) / 100, 1)

    selected_range = st.sidebar.slider(
        label,
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        step=float(step)
    )

    return data[
        data[column].between(
            selected_range[0],
            selected_range[1]
        )
    ]


# Price filter
filtered = range_filter(
    filtered,
    "Price",
    "Price Range",
    0.5
)

# Manufacturing year filter
filtered = range_filter(
    filtered,
    "Year",
    "Manufacturing Year",
    1
)

# Kilometers filter
filtered = range_filter(
    filtered,
    "Kilometers_Driven",
    "Kilometers Driven",
    1000
)

# Mileage filter
filtered = range_filter(
    filtered,
    "Mileage",
    "Mileage Range",
    0.5
)

# Engine filter
filtered = range_filter(
    filtered,
    "Engine",
    "Engine Capacity",
    50
)

# Power filter
filtered = range_filter(
    filtered,
    "Power",
    "Power Range",
    5
)

# ==========================================
# 5. KEY PERFORMANCE INDICATORS
# ==========================================

st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)


def get_mean(column):

    if column in filtered.columns:
        return filtered[column].mean()

    return None


def format_metric(value):

    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}"


col1.metric(
    "Total Cars",
    f"{len(filtered):,}"
)

col2.metric(
    "Average Price",
    format_metric(get_mean("Price"))
)

col3.metric(
    "Median Price",
    format_metric(
        filtered["Price"].median()
        if "Price" in filtered.columns
        else float("nan")
    )
)

col4.metric(
    "Average Kilometers",
    f"{get_mean('Kilometers_Driven'):,.0f}"
    if pd.notna(get_mean("Kilometers_Driven"))
    else "N/A"
)

if "Fuel_Type" in filtered.columns and not filtered["Fuel_Type"].dropna().empty:
    most_common_fuel = filtered["Fuel_Type"].mode().iloc[0]
else:
    most_common_fuel = "N/A"

col5.metric(
    "Most Common Fuel",
    most_common_fuel
)

st.divider()

if filtered.empty:
    st.warning("No cars match the selected filters.")
    st.stop()

# ==========================================
# 6. TABS
# ==========================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Visual Analysis",
    "🚘 Car Comparison",
    "🧹 Data Quality",
    "📋 Explore Dataset"
])

# ==========================================
# TAB 1: VISUAL ANALYSIS
# ==========================================

with tab1:

    st.subheader("Cars Data Visualization")

    col1, col2 = st.columns(2)

    # Fuel type chart
    with col1:

        if "Fuel_Type" in filtered.columns:

            st.write("### Cars by Fuel Type")

            fuel_count = filtered["Fuel_Type"].value_counts()

            fig, ax = plt.subplots()

            fuel_count.plot(
                kind="bar",
                ax=ax
            )

            ax.set_xlabel("Fuel Type")
            ax.set_ylabel("Number of Cars")
            ax.tick_params(
                axis="x",
                rotation=30
            )

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # Transmission chart
    with col2:

        if "Transmission" in filtered.columns:

            st.write("### Transmission Distribution")

            trans_count = filtered["Transmission"].value_counts()

            fig, ax = plt.subplots()

            trans_count.plot(
                kind="pie",
                autopct="%1.1f%%",
                ax=ax
            )

            ax.set_ylabel("")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    col3, col4 = st.columns(2)

    # Price distribution
    with col3:

        if "Price" in filtered.columns:

            st.write("### Price Distribution")

            fig, ax = plt.subplots()

            filtered["Price"].dropna().plot(
                kind="hist",
                bins=30,
                ax=ax,
                edgecolor="black"
            )

            ax.set_xlabel("Price")
            ax.set_ylabel("Number of Cars")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # Year trend
    with col4:

        if "Year" in filtered.columns and "Price" in filtered.columns:

            st.write("### Average Price by Year")

            yearly_price = (
                filtered.groupby("Year")["Price"]
                .mean()
                .sort_index()
            )

            st.line_chart(yearly_price)

    # Location analysis
    if "Location" in filtered.columns:

        st.write("### Cars by Location")

        location_count = (
            filtered["Location"]
            .value_counts()
            .head(15)
        )

        st.bar_chart(location_count)

    # Fuel-wise average price
    if "Fuel_Type" in filtered.columns and "Price" in filtered.columns:

        st.write("### Average Price by Fuel Type")

        fuel_price = (
            filtered.groupby("Fuel_Type")["Price"]
            .mean()
        )

        st.bar_chart(fuel_price)

# ==========================================
# TAB 2: CAR COMPARISON
# ==========================================

with tab2:

    st.subheader("Compare Car Features")

    # Top expensive cars
    if name_col and "Price" in filtered.columns:

        st.write("### Top 10 Most Expensive Cars")

        top_cars = filtered.nlargest(
            10,
            "Price"
        )

        columns_to_show = [
            col for col in [
                name_col,
                "Year",
                "Price",
                "Fuel_Type",
                "Transmission",
                "Kilometers_Driven"
            ]
            if col in top_cars.columns
        ]

        st.dataframe(
            top_cars[columns_to_show],
            use_container_width=True,
            hide_index=True
        )

    # Brand analysis
    if "Brand" in filtered.columns and "Price" in filtered.columns:

        st.write("### Average Price by Brand")

        brand_price = (
            filtered.groupby("Brand")["Price"]
            .mean()
            .sort_values(ascending=False)
            .head(20)
        )

        st.bar_chart(brand_price)

    # Price vs kilometers
    if "Price" in filtered.columns and "Kilometers_Driven" in filtered.columns:

        st.write("### Price vs Kilometers Driven")

        plot_data = filtered.dropna(
            subset=["Price", "Kilometers_Driven"]
        )

        fig, ax = plt.subplots()

        ax.scatter(
            plot_data["Kilometers_Driven"],
            plot_data["Price"],
            alpha=0.5
        )

        ax.set_xlabel("Kilometers Driven")
        ax.set_ylabel("Price")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Fuel summary
    if "Fuel_Type" in filtered.columns and "Price" in filtered.columns:

        st.write("### Price Statistics by Fuel Type")

        summary = (
            filtered.groupby("Fuel_Type")["Price"]
            .agg([
                "count",
                "mean",
                "median",
                "min",
                "max"
            ])
            .round(2)
        )

        st.dataframe(
            summary,
            use_container_width=True
        )

# ==========================================
# TAB 3: DATA QUALITY
# ==========================================

with tab3:

    st.subheader("Data Quality Report")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Rows",
        f"{len(filtered):,}"
    )

    c2.metric(
        "Columns",
        f"{filtered.shape[1]:,}"
    )

    c3.metric(
        "Duplicate Rows",
        f"{filtered.duplicated().sum():,}"
    )

    # Missing values
    st.write("### Missing Values")

    missing = (
        filtered.isnull()
        .sum()
        .sort_values(ascending=False)
    )

    missing = missing[missing > 0]

    if not missing.empty:

        missing_df = pd.DataFrame({
            "Missing Values": missing,
            "Missing Percentage": (
                missing / len(filtered) * 100
            ).round(2)
        })

        st.dataframe(
            missing_df,
            use_container_width=True
        )

        st.bar_chart(
            missing_df["Missing Values"]
        )

    else:

        st.success("No missing values found in this selection.")

    # Descriptive statistics
    st.write("### Descriptive Statistics")

    st.dataframe(
        filtered.describe(include="all").transpose(),
        use_container_width=True
    )

# ==========================================
# TAB 4: EXPLORE DATASET
# ==========================================

with tab4:

    st.subheader("Search and Explore Cars")

    search = st.text_input(
        "Search car details",
        placeholder="Enter brand, model, fuel type, location..."
    )

    display_df = filtered.copy()

    if search.strip():

        text_columns = (
            display_df
            .select_dtypes(include=["object", "string"])
            .columns
        )

        if len(text_columns) > 0:

            mask = (
                display_df[text_columns]
                .astype(str)
                .apply(
                    lambda col: col.str.contains(
                        search,
                        case=False,
                        na=False
                    )
                )
                .any(axis=1)
            )

            display_df = display_df[mask]

    st.write(
        f"Showing {len(display_df):,} cars"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Download filtered dataset
    csv = (
        display_df
        .drop(columns=["Brand"], errors="ignore")
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download Filtered Dataset",
        data=csv,
        file_name="filtered_cars.csv",
        mime="text/csv"
    )

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Cars EDA Dashboard | Built using Streamlit, "
    "Pandas, and Matplotlib. Price and other values "
    "are displayed in the original dataset units."
)