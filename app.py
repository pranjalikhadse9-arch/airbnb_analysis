import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏡",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #171d29;
}
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1c2636, #25344b);
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #34445c;
}
h1, h2, h3 {
    color: #f8fafc !important;
}
</style>
""", unsafe_allow_html=True)

CHART_THEME = "plotly_dark"

# =========================================================
# TITLE
# =========================================================
st.title("🏡 Airbnb Analytics Dashboard")
st.markdown("Explore Airbnb listings with interactive filters and dropdowns.")

# =========================================================
# UPLOAD DATASET
# =========================================================
uploaded_file = st.file_uploader(
    "Upload your Airbnb CSV dataset",
    type=["csv"],
    help="Upload your Airbnb dataset directly. You don't need to put the CSV on GitHub."
)

if uploaded_file is None:
    st.info("Please upload your Airbnb CSV file to begin.")
    st.stop()

# =========================================================
# LOAD & CLEAN DATA
# =========================================================
@st.cache_data(show_spinner="Loading and cleaning Airbnb data...")
def load_data(file_bytes):

    df = pd.read_csv(file_bytes, low_memory=False)

    # Standardize column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Handle alternative column names
    rename_columns = {
        "neighbourhood_group": "neighbourhood_group",
        "neighborhood_group": "neighbourhood_group",
        "room_type": "room_type",
        "host_id": "host_id",
        "host_name": "host_name",
        "availability_365": "availability_365",
        "number_of_reviews": "number_of_reviews",
        "reviews_per_month": "reviews_per_month",
        "review_rate_number": "review_rate_number",
        "minimum_nights": "minimum_nights",
        "calculated_host_listings_count": "calculated_host_listings_count",
        "construction_year": "construction_year"
    }

    df = df.rename(columns=rename_columns)

    # Remove unnecessary columns if present
    drop_cols = [
        "id", "lat", "long", "country_code",
        "country_code", "house_rules"
    ]
    df = df.drop(columns=drop_cols, errors="ignore")

    # Convert price columns
    numeric_columns = [
        "price", "service_fee", "minimum_nights",
        "number_of_reviews", "reviews_per_month",
        "review_rate_number", "calculated_host_listings_count",
        "availability_365", "construction_year",
        "host_id"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert date column
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(
            df["last_review"], errors="coerce"
        )

    # Clean text columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    # Correct common spelling issues
    if "neighbourhood_group" in df.columns:
        df["neighbourhood_group"] = df["neighbourhood_group"].replace({
            "brookln": "Brooklyn",
            "manhatan": "Manhattan"
        })

    return df


df = load_data(uploaded_file.getvalue())

# =========================================================
# IDENTIFY COLUMNS
# =========================================================
numeric_columns = df.select_dtypes(include=np.number).columns.tolist()

categorical_columns = df.select_dtypes(
    include=["object", "category"]
).columns.tolist()

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.title("🎛️ Dashboard Filters")

filtered_df = df.copy()

# Neighbourhood filter
if "neighbourhood_group" in df.columns:

    neighbourhood_options = sorted(
        df["neighbourhood_group"].dropna().unique().tolist()
    )

    selected_neighbourhood = st.sidebar.multiselect(
        "Neighbourhood Group",
        neighbourhood_options,
        default=neighbourhood_options
    )

    filtered_df = filtered_df[
        filtered_df["neighbourhood_group"].isin(selected_neighbourhood)
    ]

# Room type filter
if "room_type" in df.columns:

    room_options = sorted(df["room_type"].dropna().unique().tolist())

    selected_room = st.sidebar.multiselect(
        "Room Type",
        room_options,
        default=room_options
    )

    filtered_df = filtered_df[
        filtered_df["room_type"].isin(selected_room)
    ]

# Verification filter
if "host_identity_verified" in df.columns:

    verify_options = sorted(
        df["host_identity_verified"].dropna().unique().tolist()
    )

    selected_verify = st.sidebar.multiselect(
        "Host Verification",
        verify_options,
        default=verify_options
    )

    filtered_df = filtered_df[
        filtered_df["host_identity_verified"].isin(selected_verify)
    ]

# Cancellation policy
if "cancellation_policy" in df.columns:

    policy_options = sorted(
        df["cancellation_policy"].dropna().unique().tolist()
    )

    selected_policy = st.sidebar.multiselect(
        "Cancellation Policy",
        policy_options,
        default=policy_options
    )

    filtered_df = filtered_df[
        filtered_df["cancellation_policy"].isin(selected_policy)
    ]

# Price filter
if "price" in df.columns and df["price"].notna().any():

    min_price = max(0, int(df["price"].min()))
    max_price = int(df["price"].max())

    if min_price < max_price:

        price_range = st.sidebar.slider(
            "Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )

        filtered_df = filtered_df[
            filtered_df["price"].between(
                price_range[0], price_range[1]
            )
        ]

# Availability filter
if "availability_365" in df.columns and df["availability_365"].notna().any():

    avail_range = st.sidebar.slider(
        "Availability Days",
        min_value=0,
        max_value=365,
        value=(0, 365)
    )

    filtered_df = filtered_df[
        filtered_df["availability_365"].between(
            avail_range[0], avail_range[1]
        )
    ]

# =========================================================
# KPI CARDS
# =========================================================
st.markdown("## 📊 Key Metrics")

total_listings = len(filtered_df)

avg_price = (
    filtered_df["price"].mean()
    if "price" in filtered_df.columns else 0
)

avg_availability = (
    filtered_df["availability_365"].mean()
    if "availability_365" in filtered_df.columns else 0
)

total_hosts = (
    filtered_df["host_id"].nunique()
    if "host_id" in filtered_df.columns else 0
)

total_reviews = (
    filtered_df["number_of_reviews"].sum()
    if "number_of_reviews" in filtered_df.columns else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("🏠 Listings", f"{total_listings:,}")
k2.metric("💰 Average Price", f"${avg_price:,.0f}")
k3.metric("📅 Avg Availability", f"{avg_availability:.1f}")
k4.metric("👤 Hosts", f"{total_hosts:,}")
k5.metric("⭐ Reviews", f"{total_reviews:,.0f}")

st.divider()

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Overview",
    "📍 Location",
    "💰 Pricing",
    "📅 Availability",
    "👤 Hosts",
    "⭐ Reviews",
    "📊 Custom Analysis"
])

# =========================================================
# TAB 1 - OVERVIEW
# =========================================================
with tab1:

    st.subheader("Overview")

    col1, col2 = st.columns(2)

    # Room type distribution
    with col1:

        if "room_type" in filtered_df.columns:

            room_counts = filtered_df["room_type"].value_counts().reset_index()
            room_counts.columns = ["Room Type", "Listings"]

            fig = px.pie(
                room_counts,
                names="Room Type",
                values="Listings",
                hole=0.5,
                title="Room Type Distribution"
            )

            fig.update_layout(template=CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)

    # Listings by neighbourhood group
    with col2:

        if "neighbourhood_group" in filtered_df.columns:

            loc_counts = filtered_df["neighbourhood_group"].value_counts().reset_index()
            loc_counts.columns = ["Neighbourhood", "Listings"]

            fig = px.bar(
                loc_counts,
                x="Neighbourhood",
                y="Listings",
                color="Listings",
                title="Listings by Neighbourhood",
                text="Listings",
                color_continuous_scale="Viridis"
            )

            fig.update_layout(template=CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)

    # Price histogram
    if "price" in filtered_df.columns:

        fig = px.histogram(
            filtered_df,
            x="price",
            nbins=40,
            title="Price Distribution",
            color_discrete_sequence=["#00CC96"]
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2 - LOCATION ANALYSIS WITH DROPDOWNS
# =========================================================
with tab2:

    st.subheader("📍 Location Analysis")

    location_options = [
        col for col in categorical_columns
        if col in filtered_df.columns
    ]

    if location_options:

        selected_location = st.selectbox(
            "Select Location Parameter",
            location_options,
            index=location_options.index("neighbourhood")
            if "neighbourhood" in location_options else 0
        )

        top_n = st.selectbox(
            "Select Number of Locations",
            [5, 10, 15, 20, 30],
            index=1
        )

        location_counts = (
            filtered_df[selected_location]
            .value_counts()
            .head(top_n)
            .reset_index()
        )

        location_counts.columns = ["Location", "Listings"]

        fig = px.bar(
            location_counts,
            x="Listings",
            y="Location",
            orientation="h",
            color="Listings",
            text="Listings",
            title=f"Top {top_n} {selected_location}",
            color_continuous_scale="Viridis"
        )

        fig.update_layout(
            template=CHART_THEME,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)

    # Room type by selected neighbourhood
    if all(c in filtered_df.columns for c in [
        "neighbourhood_group", "room_type"
    ]):

        fig = px.bar(
            filtered_df,
            x="neighbourhood_group",
            color="room_type",
            title="Room Types Across Neighbourhood Groups",
            barmode="group"
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 3 - PRICE ANALYSIS WITH DROPDOWNS
# =========================================================
with tab3:

    st.subheader("💰 Pricing Analysis")

    if "price" in numeric_columns:

        price_group_options = [
            col for col in categorical_columns
            if col in filtered_df.columns
        ]

        if price_group_options:

            selected_price_group = st.selectbox(
                "Select Parameter to Compare Average Price",
                price_group_options,
                key="price_group"
            )

            selected_aggregation = st.selectbox(
                "Select Price Calculation",
                ["Average", "Median", "Minimum", "Maximum"],
                key="price_aggregation"
            )

            top_n_price = st.selectbox(
                "Select Top Locations / Categories",
                [5, 10, 15, 20],
                key="price_top_n"
            )

            if selected_aggregation == "Average":
                price_data = filtered_df.groupby(selected_price_group)["price"].mean()

            elif selected_aggregation == "Median":
                price_data = filtered_df.groupby(selected_price_group)["price"].median()

            elif selected_aggregation == "Minimum":
                price_data = filtered_df.groupby(selected_price_group)["price"].min()

            else:
                price_data = filtered_df.groupby(selected_price_group)["price"].max()

            price_data = (
                price_data.dropna()
                .sort_values(ascending=False)
                .head(top_n_price)
                .reset_index()
            )

            price_data.columns = ["Category", "Price"]

            fig = px.bar(
                price_data,
                x="Price",
                y="Category",
                orientation="h",
                color="Price",
                text_auto=".0f",
                title=f"{selected_aggregation} Price by {selected_price_group}",
                color_continuous_scale="Plasma"
            )

            fig.update_layout(
                template=CHART_THEME,
                yaxis={"categoryorder": "total ascending"}
            )

            st.plotly_chart(fig, use_container_width=True)

        # Price distribution
        fig = px.histogram(
            filtered_df,
            x="price",
            nbins=40,
            title="Price Distribution",
            color_discrete_sequence=["#FFA15A"]
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

        # Price box plot
        if "room_type" in filtered_df.columns:

            fig = px.box(
                filtered_df,
                x="room_type",
                y="price",
                color="room_type",
                title="Price Range by Room Type"
            )

            fig.update_layout(template=CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 4 - AVAILABILITY WITH DROPDOWNS
# =========================================================
with tab4:

    st.subheader("📅 Availability Analysis")

    availability_col = "availability_365"

    if availability_col in numeric_columns:

        avail_group_options = [
            col for col in categorical_columns
            if col in filtered_df.columns
        ]

        if avail_group_options:

            selected_avail_group = st.selectbox(
                "Select Parameter for Availability",
                avail_group_options,
                key="availability_group"
            )

            avail_metric = filtered_df.groupby(
                selected_avail_group
            )[availability_col].mean().sort_values(
                ascending=False
            ).head(10).reset_index()

            avail_metric.columns = ["Category", "Average Availability"]

            fig = px.bar(
                avail_metric,
                x="Average Availability",
                y="Category",
                orientation="h",
                color="Average Availability",
                text_auto=".1f",
                title=f"Average Availability by {selected_avail_group}"
            )

            fig.update_layout(
                template=CHART_THEME,
                yaxis={"categoryorder": "total ascending"}
            )

            st.plotly_chart(fig, use_container_width=True)

        # Availability distribution
        fig = px.histogram(
            filtered_df,
            x=availability_col,
            nbins=30,
            title="Availability Distribution"
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

        # Availability by room type
        if "room_type" in filtered_df.columns:

            room_availability = (
                filtered_df.groupby("room_type")[availability_col]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                room_availability,
                x="room_type",
                y=availability_col,
                color="room_type",
                title="Average Availability by Room Type",
                text_auto=".1f"
            )

            fig.update_layout(template=CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 5 - HOST ANALYSIS WITH DROPDOWNS
# =========================================================
with tab5:

    st.subheader("👤 Host Analysis")

    if "host_name" in filtered_df.columns:

        top_host_count = st.selectbox(
            "Select Top Hosts",
            [5, 10, 15, 20],
            key="host_top_n"
        )

        top_hosts = (
            filtered_df["host_name"]
            .value_counts()
            .head(top_host_count)
            .reset_index()
        )

        top_hosts.columns = ["Host", "Listings"]

        fig = px.bar(
            top_hosts,
            x="Listings",
            y="Host",
            orientation="h",
            color="Listings",
            title=f"Top {top_host_count} Hosts by Listings"
        )

        fig.update_layout(
            template=CHART_THEME,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)

    # Host verification dropdown analysis
    if "host_identity_verified" in filtered_df.columns:

        verify_metric = st.selectbox(
            "Select Metric for Host Verification",
            [col for col in numeric_columns if col in filtered_df.columns],
            key="host_verify_metric"
        )

        verification_data = (
            filtered_df.groupby("host_identity_verified")[verify_metric]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            verification_data,
            x="host_identity_verified",
            y=verify_metric,
            color="host_identity_verified",
            title=f"{verify_metric} by Host Verification Status"
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 6 - REVIEW ANALYSIS WITH DROPDOWNS
# =========================================================
with tab6:

    st.subheader("⭐ Reviews & Ratings Analysis")

    review_columns = [
        col for col in numeric_columns
        if col in [
            "number_of_reviews",
            "reviews_per_month",
            "review_rate_number"
        ]
    ]

    if review_columns and categorical_columns:

        selected_review_metric = st.selectbox(
            "Select Review Parameter",
            review_columns,
            key="review_metric"
        )

        selected_review_group = st.selectbox(
            "Group Reviews By",
            categorical_columns,
            key="review_group"
        )

        review_top_n = st.selectbox(
            "Select Top Categories",
            [5, 10, 15, 20],
            key="review_top_n"
        )

        review_data = (
            filtered_df.groupby(selected_review_group)[selected_review_metric]
            .mean()
            .sort_values(ascending=False)
            .head(review_top_n)
            .reset_index()
        )

        review_data.columns = ["Category", "Average"]

        fig = px.bar(
            review_data,
            x="Average",
            y="Category",
            orientation="h",
            color="Average",
            text_auto=".2f",
            title=f"{selected_review_metric} by {selected_review_group"
        )

        fig.update_layout(
            template=CHART_THEME,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)

    # Price vs reviews
    if all(col in filtered_df.columns for col in [
        "price", "number_of_reviews"
    ]):

        scatter_df = filtered_df.dropna(
            subset=["price", "number_of_reviews"]
        )

        # Limit points for faster rendering
        if len(scatter_df) > 5000:
            scatter_df = scatter_df.sample(5000, random_state=42)

        fig = px.scatter(
            scatter_df,
            x="price",
            y="number_of_reviews",
            color="room_type" if "room_type" in filtered_df.columns else None,
            title="Price vs Number of Reviews",
            opacity=0.6
        )

        fig.update_layout(template=CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 7 - CUSTOM PARAMETER ANALYSIS
# =========================================================
with tab7:

    st.subheader("📊 Custom Analysis")
    st.write("Choose your own parameters to create an interactive chart.")

    available_columns = filtered_df.columns.tolist()

    col1, col2, col3 = st.columns(3)

    with col1:
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Bar", "Line", "Scatter", "Histogram", "Box", "Pie"]
        )

    with col2:
        x_parameter = st.selectbox(
            "Select X-axis Parameter",
            available_columns,
            index=available_columns.index("price")
            if "price" in available_columns else 0
        )

    with col3:
        y_parameter = st.selectbox(
            "Select Y-axis Parameter",
            available_columns,
            index=available_columns.index("number_of_reviews")
            if "number_of_reviews" in available_columns else 0
    )

    color_options = ["None"] + available_columns

    color_parameter = st.selectbox(
        "Select Color Parameter",
        color_options
    )

    selected_color = None if color_parameter == "None" else color_parameter

    # Select Top N
    top_n_custom = st.selectbox(
        "Show Top Categories",
        [5, 10, 15, 20, 30, 50],
        index=1,
        key="custom_top_n"
    )

    chart_df = filtered_df.copy()

    # Sample large datasets for charts
    if len(chart_df) > 10000 and chart_type in ["Scatter", "Box"]:
        chart_df = chart_df.sample(10000, random_state=42)

    # Create chart
    try:

        if chart_type == "Bar":

            chart_df = chart_df.groupby(x_parameter)[y_parameter].mean().reset_index()
            chart_df = chart_df.sort_values(
                y_parameter, ascending=False
            ).head(top_n_custom)

            fig = px.bar(
                chart_df,
                x=x_parameter,
                y=y_parameter,
                color=selected_color,
                title=f"{y_parameter} by {x_parameter}"
            )

        elif chart_type == "Line":

            chart_df = chart_df.groupby(x_parameter)[y_parameter].mean().reset_index()
            chart_df = chart_df.sort_values(x_parameter)

            fig = px.line(
                chart_df,
                x=x_parameter,
                y=y_parameter,
                markers=True,
                color=selected_color,
                title=f"{y_parameter} Trend by {x_parameter}"
            )

        elif chart_type == "Scatter":

            fig = px.scatter(
                chart_df,
                x=x_parameter,
                y=y_parameter,
                color=selected_color,
                title=f"{x_parameter} vs {y_parameter}",
                opacity=0.6
            )

        elif chart_type == "Histogram":

            fig = px.histogram(
                chart_df,
                x=x_parameter,
                color=selected_color,
                title=f"Distribution of {x_parameter}",
                nbins=40
            )

        elif chart_type == "Box":

            fig = px.box(
                chart_df,
                x=x_parameter,
                y=y_parameter,
                color=selected_color,
                title=f"{y_parameter} by {x_parameter}"
            )

        elif chart_type == "Pie":

            pie_df = chart_df.groupby(x_parameter)[y_parameter].mean().reset_index()
            pie_df = pie_df.nlargest(top_n_custom, y_parameter)

            fig = px.pie(
                pie_df,
                names=x_parameter,
                values=y_parameter,
                title=f"{y_parameter} by {x_parameter}",
                hole=0.4
            )

        fig.update_layout(
            template=CHART_THEME,
            height=550
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning("Please select suitable parameters for this chart.")
        st.caption(str(e))

# =========================================================
# DATA PREVIEW & DOWNLOAD
# =========================================================
st.divider()

with st.expander("📋 View Filtered Dataset"):

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )

    st.download_button(
        "⬇️ Download Filtered Dataset",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="airbnb_filtered_data.csv",
        mime="text/csv"
    )

st.caption("Airbnb Dashboard | Streamlit + Plotly")    
