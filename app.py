
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏡",
    layout="wide"
)

# ---------------- CUSTOM DESIGN ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101827, #17243b);
    color: white;
}
[data-testid="stSidebar"] {
    background-color: #111827;
}
h1, h2, h3 {
    color: #ffffff !important;
}
div[data-testid="stMetric"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 18px;
    border-radius: 15px;
}
div[data-testid="stMetricLabel"] {
    color: #a5b4fc;
}
div[data-testid="stMetricValue"] {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🏡 Airbnb Analytics Dashboard")
st.markdown("### Explore Airbnb listings, prices, availability, hosts & reviews")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "📂 Upload your Airbnb CSV dataset",
    type=["csv"]
)

if uploaded_file is None:
    st.info("👆 Upload your Airbnb dataset to start exploring.")
    st.stop()

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, low_memory=False)

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Rename columns
    df = df.rename(columns={
        'host id': 'host_id',
        'host name': 'host_name',
        'neighbourhood group': 'neighbourhood_group',
        'room type': 'room_type',
        'Construction year': 'Construction_year',
        'service fee': 'service_fee',
        'minimum nights': 'minimum_nights',
        'number of reviews': 'number_of_reviews',
        'last review': 'last_review',
        'reviews per month': 'reviews_per_month',
        'review rate number': 'review_rate_number',
        'calculated host listings count': 'calculated_host_listings_count',
        'availability 365': 'availability_365'
    })

    # Remove unnecessary columns
    drop_cols = ['id', 'lat', 'long', 'country code', 'house_rules']
    df = df.drop(columns=drop_cols, errors='ignore')

    # Fill categorical missing values
    cat_cols = [
        'NAME', 'host_name', 'host_identity_verified',
        'neighbourhood_group', 'neighbourhood', 'country',
        'instant_bookable', 'cancellation_policy', 'license',
        'room_type'
    ]

    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown').astype(str)

    # Convert numeric columns
    numeric_cols = [
        'price', 'service_fee', 'minimum_nights',
        'number_of_reviews', 'reviews_per_month',
        'review_rate_number', 'calculated_host_listings_count',
        'availability_365', 'Construction_year'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r'[$,]', '', regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Correct neighbourhood spelling
    if 'neighbourhood_group' in df.columns:
        df['neighbourhood_group'] = df['neighbourhood_group'].replace({
            'brookln': 'Brooklyn',
            'manhatan': 'Manhattan'
        })

    # Convert last_review
    if 'last_review' in df.columns:
        df['last_review'] = pd.to_datetime(
            df['last_review'], errors='coerce'
        )

    return df

df = load_data(uploaded_file)

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.title("🎛️ Dashboard Filters")

filtered_df = df.copy()

# Neighbourhood filter
if 'neighbourhood_group' in df.columns:
    neighbourhood_options = sorted(df['neighbourhood_group'].dropna().unique())
    selected_neighbourhood = st.sidebar.multiselect(
        "Neighbourhood Group",
        neighbourhood_options,
        default=neighbourhood_options
    )
    filtered_df = filtered_df[
        filtered_df['neighbourhood_group'].isin(selected_neighbourhood)
    ]

# Room type filter
if 'room_type' in df.columns:
    room_options = sorted(df['room_type'].dropna().unique())
    selected_room = st.sidebar.multiselect(
        "Room Type",
        room_options,
        default=room_options
    )
    filtered_df = filtered_df[
        filtered_df['room_type'].isin(selected_room)
    ]

# Host verification filter
if 'host_identity_verified' in df.columns:
    verification_options = sorted(
        df['host_identity_verified'].dropna().unique()
    )
    selected_verification = st.sidebar.multiselect(
        "Host Identity Verified",
        verification_options,
        default=verification_options
    )
    filtered_df = filtered_df[
        filtered_df['host_identity_verified'].isin(selected_verification)
    ]

# Cancellation policy filter
if 'cancellation_policy' in df.columns:
    policy_options = sorted(df['cancellation_policy'].dropna().unique())
    selected_policy = st.sidebar.multiselect(
        "Cancellation Policy",
        policy_options,
        default=policy_options
    )
    filtered_df = filtered_df[
        filtered_df['cancellation_policy'].isin(selected_policy)
    ]

# Instant booking filter
if 'instant_bookable' in df.columns:
    booking_options = sorted(df['instant_bookable'].dropna().unique())
    selected_booking = st.sidebar.multiselect(
        "Instant Bookable",
        booking_options,
        default=booking_options
    )
    filtered_df = filtered_df[
        filtered_df['instant_bookable'].isin(selected_booking)
    ]

# Price slider
if 'price' in df.columns and df['price'].notna().any():
    min_price = int(max(0, df['price'].min()))
    max_price = int(df['price'].max())

    if min_price < max_price:
        price_range = st.sidebar.slider(
            "Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )
        filtered_df = filtered_df[
            filtered_df['price'].between(price_range[0], price_range[1])
        ]

# Availability slider
if 'availability_365' in df.columns and df['availability_365'].notna().any():
    avail_range = st.sidebar.slider(
        "Availability (Days)",
        min_value=0,
        max_value=365,
        value=(0, 365)
    )
    filtered_df = filtered_df[
        filtered_df['availability_365'].between(
            avail_range[0], avail_range[1]
        )
    ]

# Reset reminder
st.sidebar.caption("Change filters to explore different listing groups.")

# ---------------- KPI CALCULATIONS ----------------
total_listings = len(filtered_df)

avg_price = (
    filtered_df['price'].mean()
    if 'price' in filtered_df.columns else 0
)

avg_availability = (
    filtered_df['availability_365'].mean()
    if 'availability_365' in filtered_df.columns else 0
)

total_hosts = (
    filtered_df['host_id'].nunique()
    if 'host_id' in filtered_df.columns else 0
)

total_reviews = (
    filtered_df['number_of_reviews'].sum()
    if 'number_of_reviews' in filtered_df.columns else 0
)

# ---------------- KPI CARDS ----------------
st.markdown("## 📊 Key Performance Indicators")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("🏠 Total Listings", f"{total_listings:,}")
k2.metric("💰 Average Price", f"${avg_price:,.0f}")
k3.metric("📅 Avg Availability", f"{avg_availability:.1f} days")
k4.metric("👤 Total Hosts", f"{total_hosts:,}")
k5.metric("⭐ Total Reviews", f"{total_reviews:,.0f}")

st.divider()

# ---------------- CHART THEME ----------------
chart_template = "plotly_dark"

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Overview",
    "📍 Location",
    "💰 Pricing",
    "📅 Availability",
    "👤 Hosts",
    "⭐ Reviews",
    "🔍 Outliers"
])

# =========================================================
# TAB 1: OVERVIEW
# =========================================================
with tab1:
    st.subheader("Airbnb Overview")

    c1, c2 = st.columns(2)

    with c1:
        if 'room_type' in filtered_df.columns:
            room_count = filtered_df['room_type'].value_counts().reset_index()
            room_count.columns = ['Room Type', 'Listings']

            fig = px.pie(
                room_count,
                names='Room Type',
                values='Listings',
                hole=0.55,
                title="Room Type Distribution"
            )
            fig.update_traces(textinfo='label+percent')
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'neighbourhood_group' in filtered_df.columns:
            ng = filtered_df['neighbourhood_group'].value_counts().reset_index()
            ng.columns = ['Neighbourhood Group', 'Listings']

            fig = px.bar(
                ng,
                x='Neighbourhood Group',
                y='Listings',
                color='Listings',
                title="Listings by Neighbourhood Group",
                color_continuous_scale='Viridis',
                text='Listings'
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

    if 'price' in filtered_df.columns:
        fig = px.histogram(
            filtered_df,
            x='price',
            nbins=40,
            title="Price Distribution",
            color_discrete_sequence=['#00CC96']
        )
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2: LOCATION
# =========================================================
with tab2:
    st.subheader("📍 Location & Listing Analysis")

    c1, c2 = st.columns(2)

    with c1:
        if 'neighbourhood_group' in filtered_df.columns:
            loc_count = filtered_df['neighbourhood_group'].value_counts().reset_index()
            loc_count.columns = ['Neighbourhood Group', 'Listings']

            fig = px.bar(
                loc_count,
                x='Neighbourhood Group',
                y='Listings',
                color='Listings',
                title="Listings Across Neighbourhood Groups",
                color_continuous_scale='Blues',
                text='Listings'
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'neighbourhood' in filtered_df.columns:
            top_neighbourhoods = (
                filtered_df['neighbourhood']
                .value_counts()
                .head(10)
                .reset_index()
            )
            top_neighbourhoods.columns = ['Neighbourhood', 'Listings']

            fig = px.bar(
                top_neighbourhoods,
                x='Listings',
                y='Neighbourhood',
                orientation='h',
                color='Listings',
                title="Top 10 Neighbourhoods",
                color_continuous_scale='Turbo',
                text='Listings'
            )
            fig.update_layout(
                template=chart_template,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

    if all(c in filtered_df.columns for c in ['neighbourhood_group', 'room_type']):
        room_loc = filtered_df.groupby(
            ['neighbourhood_group', 'room_type']
        ).size().reset_index(name='Listings')

        fig = px.bar(
            room_loc,
            x='neighbourhood_group',
            y='Listings',
            color='room_type',
            barmode='group',
            title="Room Types Across Neighbourhood Groups"
        )
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 3: PRICING
# =========================================================
with tab3:
    st.subheader("💰 Pricing Analysis")

    if 'price' in filtered_df.columns:
        c1, c2 = st.columns(2)

        with c1:
            if 'neighbourhood_group' in filtered_df.columns:
                avg_price_group = (
                    filtered_df.groupby('neighbourhood_group')['price']
                    .mean()
                    .sort_values(ascending=False)
                    .reset_index()
                )

                fig = px.bar(
                    avg_price_group,
                    x='neighbourhood_group',
                    y='price',
                    color='price',
                    title="Average Price by Neighbourhood",
                    color_continuous_scale='Plasma',
                    text_auto='.0f'
                )
                fig.update_layout(template=chart_template)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if 'room_type' in filtered_df.columns:
                room_price = (
                    filtered_df.groupby('room_type')['price']
                    .mean()
                    .sort_values(ascending=False)
                    .reset_index()
                )

                fig = px.bar(
                    room_price,
                    x='room_type',
                    y='price',
                    color='room_type',
                    title="Average Price by Room Type",
                    text_auto='.0f'
                )
                fig.update_layout(template=chart_template)
                st.plotly_chart(fig, use_container_width=True)

        if 'neighbourhood_group' in filtered_df.columns:
            st.markdown("### Highest & Lowest Average Prices")

            price_groups = (
                filtered_df.groupby('neighbourhood_group')['price']
                .mean()
                .dropna()
                .sort_values()
                .reset_index()
            )

            if not price_groups.empty:
                low_group = price_groups.iloc[0]
                high_group = price_groups.iloc[-1]

                c1, c2 = st.columns(2)
                c1.metric("Lowest Average Price", f"${low_group['price']:,.0f}",
                          low_group['neighbourhood_group'])
                c2.metric("Highest Average Price", f"${high_group['price']:,.0f}",
                          high_group['neighbourhood_group'])

        # Price vs other numerical variables
        num_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()

        if len(num_cols) > 1:
            selected_y = st.selectbox(
                "Compare Price With:",
                [c for c in num_cols if c != 'price'],
                key='price_compare'
            )

            fig = px.scatter(
                filtered_df,
                x='price',
                y=selected_y,
                color='room_type' if 'room_type' in filtered_df.columns else None,
                title=f"Price vs {selected_y}",
                opacity=0.5
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 4: AVAILABILITY
# =========================================================
with tab4:
    st.subheader("📅 Availability Analysis")

    if 'availability_365' in filtered_df.columns:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.histogram(
                filtered_df,
                x='availability_365',
                nbins=30,
                title="Availability Distribution (Days)",
                color_discrete_sequence=['#AB63FA']
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if 'room_type' in filtered_df.columns:
                room_avail = (
                    filtered_df.groupby('room_type')['availability_365']
                    .mean()
                    .reset_index()
                )

                fig = px.bar(
                    room_avail,
                    x='room_type',
                    y='availability_365',
                    color='room_type',
                    title="Average Availability by Room Type",
                    text_auto='.1f'
                )
                fig.update_layout(template=chart_template)
                st.plotly_chart(fig, use_container_width=True)

        if 'last_review' in filtered_df.columns:
            review_date_df = filtered_df.dropna(subset=['last_review']).copy()
            review_date_df['Year'] = review_date_df['last_review'].dt.year

            year_avail = (
                review_date_df.groupby('Year')['availability_365']
                .mean()
                .reset_index()
            )

            if not year_avail.empty:
                fig = px.line(
                    year_avail,
                    x='Year',
                    y='availability_365',
                    markers=True,
                    title="Average Availability by Last Review Year"
                )
                fig.update_layout(template=chart_template)
                st.plotly_chart(fig, use_container_width=True)

            review_date_df['Month'] = review_date_df['last_review'].dt.month
            month_avail = (
                review_date_df.groupby('Month')['availability_365']
                .mean()
                .reset_index()
            )

            if not month_avail.empty:
                fig = px.line(
                    month_avail,
                    x='Month',
                    y='availability_365',
                    markers=True,
                    title="Monthly Availability Trends"
                )
                fig.update_layout(
                    template=chart_template,
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(1, 13)),
                        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 5: HOST ANALYSIS
# =========================================================
with tab5:
    st.subheader("👤 Host Analysis")

    c1, c2 = st.columns(2)

    with c1:
        if 'host_name' in filtered_df.columns:
            top_hosts = filtered_df['host_name'].value_counts().head(10).reset_index()
            top_hosts.columns = ['Host', 'Listings']

            fig = px.bar(
                top_hosts,
                x='Listings',
                y='Host',
                orientation='h',
                color='Listings',
                title="Top 10 Hosts by Listings",
                color_continuous_scale='Sunset'
            )
            fig.update_layout(
                template=chart_template,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'host_identity_verified' in filtered_df.columns:
            verification = filtered_df.groupby(
                'host_identity_verified'
            ).agg(
                Average_Rating=('review_rate_number', 'mean')
                if 'review_rate_number' in filtered_df.columns
                else ('price', 'mean'),
                Average_Price=('price', 'mean')
            ).reset_index()

            fig = px.bar(
                verification,
                x='host_identity_verified',
                y='Average_Price',
                color='host_identity_verified',
                title="Average Price by Host Verification"
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

    if 'host_name' in filtered_df.columns and 'number_of_reviews' in filtered_df.columns:
        host_reviews = (
            filtered_df.groupby('host_name')['number_of_reviews']
            .mean()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            host_reviews,
            x='host_name',
            y='number_of_reviews',
            color='number_of_reviews',
            title="Top Hosts by Average Reviews",
            text_auto='.1f'
        )
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 6: REVIEWS
# =========================================================
with tab6:
    st.subheader("⭐ Review & Rating Analysis")

    c1, c2 = st.columns(2)

    with c1:
        if 'neighbourhood' in filtered_df.columns and 'number_of_reviews' in filtered_df.columns:
            avg_reviews = (
                filtered_df.groupby('neighbourhood')['number_of_reviews']
                .mean()
                .nlargest(10)
                .reset_index()
            )

            fig = px.bar(
                avg_reviews,
                x='number_of_reviews',
                y='neighbourhood',
                orientation='h',
                color='number_of_reviews',
                title="Top Neighbourhoods by Average Reviews"
            )
            fig.update_layout(
                template=chart_template,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'neighbourhood' in filtered_df.columns and 'review_rate_number' in filtered_df.columns:
            avg_rating = (
                filtered_df.groupby('neighbourhood')['review_rate_number']
                .mean()
                .nlargest(10)
                .reset_index()
            )

            fig = px.bar(
                avg_rating,
                x='review_rate_number',
                y='neighbourhood',
                orientation='h',
                color='review_rate_number',
                title="Top Neighbourhoods by Average Rating"
            )
            fig.update_layout(
                template=chart_template,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

    if 'number_of_reviews' in filtered_df.columns and 'price' in filtered_df.columns:
        fig = px.scatter(
            filtered_df,
            x='price',
            y='number_of_reviews',
            color='room_type' if 'room_type' in filtered_df.columns else None,
            title="Price vs Number of Reviews",
            opacity=0.5
        )
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

    # Reviews by room type
    if 'room_type' in filtered_df.columns and 'number_of_reviews' in filtered_df.columns:
        reviews_room = (
            filtered_df.groupby('room_type')['number_of_reviews']
            .mean()
            .reset_index()
        )

        fig = px.bar(
            reviews_room,
            x='room_type',
            y='number_of_reviews',
            color='room_type',
            title="Average Reviews by Room Type",
            text_auto='.1f'
        )
        fig.update_layout(template=chart_template)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 7: OUTLIERS
# =========================================================
with tab7:
    st.subheader("🔍 Outlier & Anomaly Analysis")

    if 'price' in filtered_df.columns:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.box(
                filtered_df,
                y='price',
                title="Price Outlier Detection",
                points='outliers'
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            price_sorted = filtered_df.sort_values(
                'price', ascending=False
            ).head(10)

            fig = px.bar(
                price_sorted,
                x='price',
                y='NAME' if 'NAME' in filtered_df.columns else None,
                orientation='h',
                color='price',
                title="10 Highest Priced Listings"
            )
            fig.update_layout(template=chart_template)
            st.plotly_chart(fig, use_container_width=True)

        # Neighbourhood comparison
        if 'neighbourhood' in filtered_df.columns:
            c1, c2 = st.columns(2)

            with c1:
                neighbourhood_price = (
                    filtered_df.groupby('neighbourhood')['price']
                    .mean()
                    .nlargest(10)
                    .reset_index()
                )

                fig = px.bar(
                    neighbourhood_price,
                    x='price',
                    y='neighbourhood',
                    orientation='h',
                    color='price',
                    title="10 Most Expensive Neighbourhoods"
                )
                fig.update_layout(
                    template=chart_template,
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                neighbourhood_availability = (
                    filtered_df.groupby('neighbourhood')['availability_365']
                    .mean()
                    .nlargest(10)
                    .reset_index()
                )

                fig = px.bar(
                    neighbourhood_availability,
                    x='availability_365',
                    y='neighbourhood',
                    orientation='h',
                    color='availability_365',
                    title="10 Neighbourhoods with Highest Availability"
                )
                fig.update_layout(
                    template=chart_template,
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------- DATA PREVIEW ----------------
st.divider()
with st.expander("📋 View Filtered Dataset"):
    st.dataframe(filtered_df, use_container_width=True, height=400)

    st.download_button(
        "⬇️ Download Filtered Data",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name="airbnb_filtered_data.csv",
        mime="text/csv"
    )

st.caption("Airbnb Analytics Dashboard | Built with Streamlit & Plotly")
