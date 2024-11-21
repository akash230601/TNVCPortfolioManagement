import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Set the directory containing your data files
DATA_DIR = 'data/'

# Load available datasets
@st.cache_data
def get_datasets():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') or f.endswith('.xlsx')]
    return files

@st.cache_data
def load_data(filename, rows, columns):
    file_path = os.path.join(DATA_DIR, filename)
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    
    # Filter by columns and rows if specified
    if columns:
        df = df[columns]
    if rows:
        df = df.iloc[rows]
    return df

# Save updated dataset
def save_data(filename, df):
    file_path = os.path.join(DATA_DIR, filename)
    if filename.endswith('.csv'):
        df.to_csv(file_path, index=False)
    elif filename.endswith('.xlsx'):
        df.to_excel(file_path, index=False)

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Data Interaction", "Visualizations"])

if page == "Data Interaction":
    st.title("Data Interaction - Add/Update Records")
    datasets = get_datasets()
    selected_file = st.selectbox("Select a dataset:", datasets)

    if selected_file:
        # Load dataset
        full_df = load_data(selected_file, None, None)
        st.write(f"Preview of `{selected_file}` dataset:")
        st.dataframe(full_df)

        # Step 3: Select specific columns and rows
        columns = list(full_df.columns)
        st.write("Available Columns:", columns)
        selected_columns = st.multiselect("Select columns to display:", columns)
        row_range = st.slider("Select rows to display (start to end):", 
                            min_value=0, max_value=len(full_df)-1, value=(0, 10))
        selected_rows = list(range(row_range[0], row_range[1] + 1))
        # Step 3.5: Load and display the data
        data = load_data(selected_file, selected_rows, selected_columns)
        st.write("Filtered Data:")
        st.dataframe(data)


        # Step 4
        st.write("### Filter Data by Column Values")
        columns = list(full_df.columns)
        selected_column = st.selectbox("Select a column to filter by:", columns)

        if selected_column:
            unique_values = full_df[selected_column].dropna().unique()
            selected_value = st.selectbox(f"Select a value for '{selected_column}':", unique_values)

            if selected_value:
                filtered_df = full_df[full_df[selected_column] == selected_value]
                st.write(f"Filtered Data (where `{selected_column}` is `{selected_value}`):")
                st.dataframe(filtered_df)


        # Dynamic form for Add/Update
        st.write("### Manage Records")
        action = st.radio("Choose action:", ["Add a Record", "Update a Record"])

        new_record = {}
        with st.form("manage_record_form"):
            for col in full_df.columns:
                new_record[col] = st.text_input(f"Enter value for {col}", key=f"{col}_{action}")
            
            submit_button = st.form_submit_button(label=action)
        
        if submit_button:
            if action == "Add a Record":
                new_df = pd.DataFrame([new_record])
                full_df = pd.concat([full_df, new_df], ignore_index=True)
                save_data(selected_file, full_df)
                st.success("Record added successfully!")
            elif action == "Update a Record":
                primary_key_col = st.selectbox("Select the primary key column for update:", full_df.columns)
                primary_key_value = st.text_input(f"Enter value for `{primary_key_col}` to update:", key="update_key")
                if primary_key_value:
                    index = full_df[full_df[primary_key_col] == primary_key_value].index
                    if not index.empty:
                        for col, value in new_record.items():
                            if value:
                                full_df.at[index[0], col] = value
                        save_data(selected_file, full_df)
                        st.success("Record updated successfully!")
                    else:
                        st.error("Record not found for the given primary key!")
            st.dataframe(full_df)

elif page == "Visualizations":
    st.title("Data Visualizations")
    # User selects dataset
    datasets = ["Companies", "Prizes", "Funds", "Employees"]
    selected_dataset = st.selectbox("Select a dataset for analysis:", datasets)

    if selected_dataset:
        # Load dataset based on user choice
        file_name_map = {
            "Companies": "companies.csv",
            "Prizes": "prizes.csv",
            "Funds": "funds.csv",
            "Employees": "employees.csv"
        }
        selected_file = file_name_map[selected_dataset]
        df = load_data(selected_file, None, None)
        st.write(f"Preview of `{selected_dataset}` dataset:")
        st.dataframe(df)

        # Visualization 1: Example Histogram (e.g., Most prizes won by companies in an industry)
        if selected_dataset == "Prizes":
            st.write("### Visualization 1: Most Prizes Won by Companies in an Industry")

            # Load both the Companies and Prizes datasets
            companies_df = load_data("companies.csv", None, None)
            prizes_df = load_data("prizes.csv", None, None)

            # Perform the join to add the Industry column to the Prizes dataset
            merged_df = prizes_df.merge(companies_df, left_on="company", right_on="company", how="inner")

            # Allow user to select an industry
            industry = st.selectbox("Select an industry:", merged_df["industry"].unique())

            # Filter by the selected industry
            filtered_df = merged_df[merged_df["industry"] == industry]

            # Group by company and count the number of prizes
            histogram_data = filtered_df.groupby("company").size()

            # Display the histogram
            st.bar_chart(histogram_data)


        # Visualization 2: Scatter Plot (e.g., Initial Funds vs Employees)
        if selected_dataset == "Companies":
            st.write("### Visualization 2: Initial Funds vs Employees")
            x_col = st.selectbox("Select column for x-axis:", ["initial_funds", "initial_employees"])
            y_col = st.selectbox("Select column for y-axis:", ["initial_employees", "initial_funds"])
            df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

            # Drop rows with NaN values in the selected columns
            df_filtered = df.dropna(subset=[x_col, y_col])

            if df_filtered.empty:
                st.error("The selected columns do not have valid numeric data to plot.")
            else:
                plt.figure(figsize=(8, 6))
                plt.scatter(df_filtered[x_col], df_filtered[y_col], alpha=0.7)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.title(f"{x_col} vs {y_col}")
                st.pyplot(plt)

        # Visualization 3: Time-based line plot
        if selected_dataset == "Funds":
            st.write("### Visualization 3: Funding Over Time")
            company = st.selectbox("Select a company:", df["company"].unique())
            filtered_df = df[df["company"] == company].sort_values("date_added")
            plt.figure(figsize=(8, 6))
            plt.plot(filtered_df["date_added"], filtered_df["value"], marker='o')
            plt.xlabel("Date Added")
            plt.ylabel("Value")
            plt.title(f"Funding Over Time for {company}")
            st.pyplot(plt)
