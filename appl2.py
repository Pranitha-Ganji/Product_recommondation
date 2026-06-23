import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

st.set_page_config(page_title="Advanced Recommendation Engine", layout="wide")
st.title("🎯 Next-Gen Product Recommendation Dashboard")

# 1. Database Connection
def load_db_data():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="dbms26", database="sales_db"
    )
    items_df = pd.read_sql("SELECT * FROM items;", conn)
    orders_df = pd.read_sql("SELECT * FROM order_history;", conn)
    conn.close()
    return items_df, orders_df

try:
    items_df, orders_df = load_db_data()

    # 2. Advanced Interactive Selection Widget
    st.subheader("🛒 Selection Control")
    # Using a selectbox ensures Streamlit registers changes instantly and cleanly
    selected_product = st.selectbox(
        "Choose a target product to calculate recommended pairings:", 
        options=items_df["product_name"].unique()
    )
    
    # Get the category of the selected item
    selected_category = items_df[items_df['product_name'] == selected_product]['category'].values[0]

    st.markdown("---")

    # 3. Recommendation Algorithm Function (Frequently Bought Together)
    def get_recommendations(target_product, items_df, orders_df):
        # Find orders that contain the targeted product
        matching_orders = orders_df[orders_df['product_name'] == target_product]['order_id'].unique()
        
        if len(matching_orders) == 0:
            return pd.DataFrame()
        
        # Get all other products inside those exact orders
        co_occurring_items = orders_df[
            orders_df['order_id'].isin(matching_orders) & (orders_df['product_name'] != target_product)
        ]
        
        # Calculate frequency of occurrence
        rec_counts = co_occurring_items['product_name'].value_counts().reset_index()
        rec_counts.columns = ['product_name', 'co_occurrences']
        
        # Merge back with item details to get price and category
        final_recs = pd.merge(rec_counts, items_df, on='product_name')
        return final_recs.sort_values(by='co_occurrences', ascending=False)

    # 4. Display Layout split dynamically
    left_col, right_col = st.columns([1.1, 0.9])

    with left_col:
        st.subheader("📦 Product Catalog Spotlight")
        # Highlight the currently viewed item dynamically in your main database view
        def highlight_selected(row):
            return ['background-color: #e6f2ff' if row['product_name'] == selected_product else '' for _ in row]
            
        st.dataframe(
            items_df.style.apply(highlight_selected, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={"price": st.column_config.NumberColumn("Price ($)", format="$%.2f")}
        )

    with right_col:
        st.subheader(f"🔮 Dynamic Up-Sells for: **{selected_product}**")
        
        # Generate new data on every dropdown change
        recommendations = get_recommendations(selected_product, items_df, orders_df)
        
        if not recommendations.empty:
            st.dataframe(
                recommendations[['product_name', 'category', 'price', 'co_occurrences']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "co_occurrences": st.column_config.ProgressColumn(
                        "Recommendation Strength",
                        min_value=0,
                        max_value=int(recommendations['co_occurrences'].max() + 1),
                        format="%d bundle orders"
                    ),
                    "price": st.column_config.NumberColumn("Price ($)", format="$%.2f")
                }
            )
            
            # Interactive visualization updates immediately
            fig = px.bar(
                recommendations, x="product_name", y="co_occurrences",
                labels={"product_name": "Recommended Product", "co_occurrences": "Co-occurrence matches"},
                color_discrete_sequence=["#2b5c8f"]
            )
            fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("ℹ️ No bundle purchase patterns discovered yet. Recommending target fallback category items.")
            backup_recs = items_df[
                (items_df['category'] == selected_category) & (items_df['product_name'] != selected_product)
            ]
            st.dataframe(backup_recs, use_container_width=True, hide_index=True)

    # 5. Admin tools hidden cleanly
    st.markdown("---")
    with st.popover("⚙️ View Transaction Clusters (Full Graph)"):
        fig_scatter = px.scatter(
            orders_df, x="order_id", y="product_name", 
            color="product_name", title="Transactional Co-occurrences in Database"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

except Exception as e:
    st.error(f"🚨 Application Error: {e}")