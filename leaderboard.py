import streamlit as st
import pandas as pd
import requests
import json  # Import the json module
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, time, timedelta
import pytz
import base64

# Loading Data


# time to live - you can change this as it is required to be refereshed
@st.cache_data(ttl=5)
def load_data(sheet_url):
    try:
        data = pd.read_csv(sheet_url)
        return data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Function to calculate the total 'Applied' related to each entity
def calculate_total_applied(df, data_mode):
    entity_applied_total = {}
    for index, row in df.iterrows():
        entity = row['Entity']
        applied = row[f'{data_mode} Applied']
        if entity not in entity_applied_total:
            entity_applied_total[entity] = applied
        else:
            entity_applied_total[entity] += applied
    return entity_applied_total

# Function to calculate the total 'Approved' related to each entity
def calculate_total_approved(df, data_mode):
    entity_approved_total = {}
    for index, row in df.iterrows():
        entity = row['Entity']
        approved = row[f'{data_mode} Approved']
        if entity not in entity_approved_total:
            entity_approved_total[entity] = approved
        else:
            entity_approved_total[entity] += approved
    return entity_approved_total

# Function to calculate the total SUs related to each entity
def calculate_total_mou(df, data_mode):
    entity_sus_total = {}
    for index, row in df.iterrows():
        entity = row['Entity']
        sus = row[f'{data_mode} MoUs']
        if entity not in entity_sus_total:
            entity_sus_total[entity] = sus
        else:
            entity_sus_total[entity] += sus
    return entity_sus_total

# Function to calculate the total points of each entity
def calulate_total_points(df, data_mode):
    entity_sum = {}
    for index, row in df.iterrows():
        entity = row['Entity']
        total = row[f'{data_mode} Total']
        if entity not in entity_sum:
            entity_sum[entity] = total
        else:
            entity_sum[entity] += total
    return entity_sum

def count_SUs_by_entity(df, selected_function, data_mode):
    filtered_df = df[df['Function'] == selected_function]
    su_counts = filtered_df.groupby('Entity')[f'{data_mode} SUs'].sum().reset_index()
    su_counts.rename(columns={f'{data_mode} SUs': 'Count_SUs'}, inplace=True)
    return su_counts

# Function to calculate the count of 'Applied' related to each entity based on the selected function
def count_applied_by_entity(df, selected_function, data_mode):
    filtered_df = df[df['Function'] == selected_function]
    applied_counts = filtered_df.groupby(
        'Entity')[f'{data_mode} Applied'].sum().reset_index()
    applied_counts.rename(columns={f'{data_mode} Applied': 'Count_Applied'}, inplace=True)
    return applied_counts

# Function to calculate the count of 'Approved' related to each entity based on the selected function
def count_approved_by_entity(df, selected_function, data_mode):
    filtered_df = df[df['Function'] == selected_function]
    approved_counts = filtered_df.groupby(
        'Entity')[f'{data_mode} Approved'].sum().reset_index()
    approved_counts.rename(
        columns={f'{data_mode} Approved': 'Count_Approved'}, inplace=True)
    return approved_counts

# Function to calculate the %applied to approved ratio for each entity on the selected function
def count_applied_to_approved_ratio(df, selected_function, data_mode):
    filtered_df = df[df['Function'] == selected_function]
    applied_to_approved_ratio = filtered_df.groupby(
        'Entity')[f'{data_mode} %APL-APD'].sum().reset_index()
    applied_to_approved_ratio.rename(
        columns={f'{data_mode} %APL-APD': 'Applied_to_Approved_Ratio'}, inplace=True)
    return applied_to_approved_ratio

# Function to caulculate ranks and display medals for top 3 ranks
def display_score_ranks(df):
    # Calculate ranks based on scores
    df_with_ranks = df.sort_values(by=f'Total', ascending=False)
    df_with_ranks['Rank'] = range(1, len(df_with_ranks) + 1)

    # Replace rank number with - if the total is 0
    df_with_ranks['Rank'] = df_with_ranks.apply(lambda row:
                                                '-' if row['Total'] == 0 else row['Rank'], axis=1)

    # Apply gold, silver, and bronze medals to the 'Entity' column
    df_with_ranks['Entity'] = df_with_ranks.apply(lambda row:
                                                  f"🥇 {row['Entity']}" if (row['Rank'] == 1 and row['Total'] != 0) else
                                                  f"🥈 {row['Entity']}" if (row['Rank'] == 2 and row['Total'] != 0) else
                                                  f"🥉 {row['Entity']}" if (row['Rank'] == 3 and row['Total'] != 0) else
                                                  row['Entity'], axis=1)

    # display the leaderboard section
    return df_with_ranks

# Function to create total applications bar chart and data
def applied_bar_chart_and_data(data, data_mode):
    # Calculate total 'Applied' related to each entity
    entity_applied_total = calculate_total_applied(data, data_mode)

    # Convert dictionary to DataFrame
    df_entity_applied_total = pd.DataFrame.from_dict(
        entity_applied_total, orient='index', columns=['Total_Applied'])
    df_entity_applied_total.reset_index(inplace=True)
    df_entity_applied_total.rename(columns={'index': 'Entity'}, inplace=True)

    # Create a colored bar chart using Plotly Express
    fig_applied = px.bar(df_entity_applied_total, x='Entity', y='Total_Applied', title=f'🌍 {data_mode} Applications by Entity', labels={
                         'Entity': 'Entity', 'Total_Applied': 'Applications'}, color='Entity')

    # Hide the legend
    functional_bar_charts_formatting(fig_applied)

    return fig_applied, df_entity_applied_total

# Function to create total approvals bar chart and data
def approved_bar_chart_and_data(data, data_mode):
    # Calculate total 'Approved' related to each entity
    entity_approved_total = calculate_total_approved(data, data_mode)

    # Convert dictionary to DataFrame
    df_entity_approved_total = pd.DataFrame.from_dict(
        entity_approved_total, orient='index', columns=['Total_Approved'])
    df_entity_approved_total.reset_index(inplace=True)
    df_entity_approved_total.rename(columns={'index': 'Entity'}, inplace=True)
    # Create a colored bar chart using Plotly Express
    fig_approved = px.bar(df_entity_approved_total, x='Entity', y='Total_Approved', title=f'✅ {data_mode} Approvals by Entity', labels={
                          'Entity': 'Entity', 'Total_Approved': 'Approvals'}, color='Entity')
    # Hide the legend
    functional_bar_charts_formatting(fig_approved)

    return fig_approved, df_entity_approved_total

# Function to create applied to approved ratio bar chart and data
def applied_to_approved_ratio_bar_chart_and_data(df_entity_apd_total, df_entity_apl_total, data_mode):
    # calculate the ratio of applied to approved (APD/APL)
    # divide the pd.dataframe of total approved by total applied

    apl_to_apd = pd.DataFrame({
        # use entity column as the index
        'Entity': df_entity_apd_total['Entity'],
        'APL_to_APD': round(df_entity_apd_total['Total_Approved']*100 / df_entity_apl_total['Total_Applied'], 2)
    })

    # Replace any inf or NaN values with 0, in case of division by zero
    apl_to_apd['APL_to_APD'] = apl_to_apd['APL_to_APD'].replace(
        [float('inf'), float('nan')], 0)

    fig_apl_to_apd = px.bar(apl_to_apd, x='Entity', y='APL_to_APD', title=f'📊 {data_mode} Applied to Approved Ratio by Entity', labels={
                            'Entity': 'Entity', 'APL_to_APD': '%Applied to Approved'}, color='Entity')

    functional_bar_charts_formatting(fig_apl_to_apd)

    return fig_apl_to_apd, apl_to_apd

# Function to create total SUs bar chart and data
def mou_bar_chart_and_data(data, data_mode):
    entity_sus_total = calculate_total_mou(data, data_mode)

    df_entity_sus_total = pd.DataFrame.from_dict(
        entity_sus_total, orient='index', columns=['Total_MoUs'])
    df_entity_sus_total.reset_index(inplace=True)
    df_entity_sus_total.rename(columns={'index': 'Entity'}, inplace=True)

    fig_sus = px.bar(df_entity_sus_total, x='Entity', y='Total_MoUs', 
                     title=f'📩 {data_mode} SUs by Entity', 
                     labels={'Entity': 'Entity', 'Total_MoUs': 'Total MoUs'}, 
                     color='Entity')

    functional_bar_charts_formatting(fig_sus)

    return fig_sus, df_entity_sus_total

# Function to get total points of each entity
def total_points(data, data_mode):
    entity_points_total = calulate_total_points(data, data_mode)
    df_entity_points_total = pd.DataFrame.from_dict(
        entity_points_total, orient='index', columns=['Total'])
    df_entity_points_total.reset_index(inplace=True)
    df_entity_points_total.rename(columns={'index': 'Entity'}, inplace=True)

    # return df_ranks
    return df_entity_points_total

# display summary details (on the top of the page)
def display_summary_numbers(total_mou, total_approved, total_applied, data_mode):
    # Calculate the conversion rate, with a check for division by zero
            conversion_rate = round(total_approved / total_applied, 2) if total_applied != 0 else 0

            # Define a layout with two columns
            col2, col3, col4 = st.columns([1, 1, 1])

            # with col1:
            #     st.markdown(
            #         "<div style='text-align: center;'>"
            #         f"<h3>📩 {data_mode} Sign Ups</h3>"
            #         f"<p style='font-size: 32px;'>{total_SUs}</p>"
            #         "</div>",
            #         unsafe_allow_html=True,
            #     )

            # Display the total applications in the first column
            with col2:
                st.markdown(
                    "<div style='text-align: center;'>"
                    f"<h3>🌍 {data_mode} Applications</h3>"
                    f"<p style='font-size: 32px;'>{total_applied}</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

            # Display the total approvals in the second column
            with col3:
                st.markdown(
                    "<div style='text-align: center;'>"
                    f"<h3>✅ {data_mode} Approvals</h3>"
                    f"<p style='font-size: 32px;'>{total_approved}</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

            # Display the conversion rate in the third column
            with col4:
                st.markdown(
                    "<div style='text-align: center;'>"
                    f"<h3>📊 {data_mode} MoUs</h3>"
                    f"<p style='font-size: 32px;'>{total_mou} </p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

# Function to display the leaderboard table
def display_leaderboard_table(df, data_mode):
    # Apply custom CSS for styling
    st.markdown(
        """
    <style>
    th, td {
        font-size: 20px !important;
        padding: 10px; /* Add padding for better spacing */
        text-align: center; /* Center-align text */
        font-weight: 900;
    }
    table {
        width: 100%; /* Full width */
        border-collapse: collapse; /* Collapse borders */
    }
    th {
        background-color: #FCFCFC; /* Light gray background for headers */
        border: 5px solid #ddd; /* Add borders to header */
    }
    td {
        border: 1px solid #ddd; /* Add borders to cells */
    }
    thead th {
        background-color: green !important; /* Set the first row's background color to green */
        color: white !important; /* Optional: Set text color to white for contrast */
    }

    /* Add media queries for responsiveness */
    @media screen and (max-width: 768px) {
        th, td {
            font-size: 16px !important; /* Reduce font size for small screens */
            padding: 8px; /* Adjust padding for small screens */
        }
    }

    @media screen and (max-width: 480px) {
        th, td {
            font-size: 11px !important; /* Further reduce font size for very small screens */
            padding: 6px; /* Further adjust padding */
        }
    }
</style>

    """, unsafe_allow_html=True)

    # Calculate ranks based on scores
    df_with_ranks = display_score_ranks(df)

    # Rename the columns for better readability
    df_with_ranks.rename(columns={
        'Total': f'{data_mode} OPS Score',
        'Total_Approved': f'{data_mode} Approvals',
        'Total_Applied': f'{data_mode} Applications',
        'Total_MoUs': f'{data_mode} MoUs',
        # 'APL_to_APD': f'{data_mode} Applied to Approved Ratio %'
    }, inplace=True)

    # Ensure the Rank column is included and set as the index
    df_with_ranks['Rank'] = range(1, len(df_with_ranks) + 1)

    # Specify the order of columns explicitly
    # Make sure that the columns listed here match your DataFrame
    columns_order = ['Rank', 'Entity', f'{data_mode} OPS Score',
                     f'{data_mode} Applications', f'{data_mode} Approvals', f'{data_mode} MoUs']

    # Check if all specified columns exist in the DataFrame
    for col in columns_order:
        if col not in df_with_ranks.columns:
            st.error(f"Column '{col}' not found in DataFrame.")
            return  # Stop execution if a column is missing

    # Reorder DataFrame to include the Rank column first
    df_with_ranks = df_with_ranks[columns_order]

    # Convert DataFrame to HTML, including the rank column as a standard column
    html_table = df_with_ranks.to_html(
        classes='dataframe', index=False, escape=False)

    # Display the HTML table
    st.markdown(html_table, unsafe_allow_html=True)

def functional_image_rendering(function):
    if (function == "oGV" or function == "iGV"):
        # Render GV image
        st.image(gv_image_path)
    elif (function == "oGTa" or function == "iGTa"):
        # Render GTa image
        st.image(gta_image_path)
    elif (function == "oGTe" or function == "iGTe"):
        # Render GTe image
        st.image(gte_image_path)

def functional_bar_charts_formatting(chart):
    chart.update_layout(
        title_font=dict(size=20, color="#31333F"),  # Title font size
        # X-axis title font size
        xaxis_title_font=dict(size=16, color="#31333F"),
        # Y-axis title font size
        yaxis_title_font=dict(size=16, color="#31333F"),
        # X-axis tick font size
        xaxis_tickfont=dict(size=14, color="#31333F"),
        # Y-axis tick font size
        yaxis_tickfont=dict(size=14, color="#31333F"),
        showlegend=False)

def radio_button():

    # Set the time zone to GMT+5:30 (Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')

    # Get the current time in GMT+5:30
    now = datetime.now(tz)
     
    # Define 8:00 PM time object
    eight_pm = time(20, 0, 0)  # 20:00 hours
 
     # Check if current time is before or after 8:00 PM
    if now.time() < eight_pm:
        # Before 8 PM: Show data from yesterday 8 PM to current time
        start_time = (now - timedelta(days=1)).strftime("%d-%m-%Y")
    else:
        # After 8 PM: Show data from today 8 PM to current time
        start_time = now.strftime("%d-%m-%Y")
 
    end_time = now.strftime("%d-%m-%Y")
    
    # data_type = st.radio(
    #     "",
    #     ["Total Numbers", "Daily Numbers"],
    #     captions=[
    #         # f'Showing Total Data From 11-03-2025 to {today_gmt_530}',
    #         f'Showing Total Data From 27-04-2025 to Current Time',
    #         f'Showing Data Between {start_time} : 8.00 PM -- {end_time} : Current Time'
    #     ],
    #     horizontal=True,
    #     label_visibility="collapsed"
    # )

    # if data_type == "Total Numbers":
    data_mode = "Total"
    # elif data_type == "Daily Numbers":
    #     data_mode = "Daily"

    return data_mode

# Functional Image Rendaring
# Replace with your image URL_image_path

icon_path = 'https://lh3.googleusercontent.com/d/19KFA_FrnUb8UVj06EyfhFXdeDa6vVVui'
# mascot_image = 'https://lh3.googleusercontent.com/d/1undYpxuWYWLP3A0uH1XvUJRCnNIkXpod' #iseeek
# mascot_image = 'https://lh3.googleusercontent.com/d/1eR-_6JAUvUNXFVnlOLoamWGOpSRUnJHu' #natcon
mascot_image = 'https://lh3.googleusercontent.com/d/1OasiX9Kt2T5YswXojmmro6ytw6hUZEEI' #ex marathon
favicon_path = 'https://lh3.googleusercontent.com/d/1Fide8c8sEd6-SLiA_bS3lVr93OOCw9Mw'
gta_image_path = "https://lh3.googleusercontent.com/d/1KP_HuRqFjffWIEZsOHqrGh4l7r0YApTv"
gte_image_path = 'https://lh3.googleusercontent.com/d/1pO8mI2dVEqNBHWXhz_hNP7gllVDkQfND'
gv_image_path = "https://lh3.googleusercontent.com/d/1P_mg-0qWhpPp2bs9_XlgDru_YA3bjvSi"

# title_image_path = "https://lh3.googleusercontent.com/d/1UVGBInlNXFd6Q6m5tLeRJfh21OMkjhi2"
#title_image_path = "https://lh3.googleusercontent.com/d/1nPlofkBrZWqdMomRwRm3gOzVp3hDQ1GF"
# title_image_path = "https://lh3.googleusercontent.com/d/1OQPCc3V6LrIgMpX9F3r9ip11WWAQhAUg" #natcon
title_image_path = "https://lh3.googleusercontent.com/d/1s4U1LoOU9PTckAb1r3iWIENlv2ZYGUcN" #nlds

nsbm_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1Z9mSOFgTgZ9OnsQQDbnh0GbtRfywRM4z"
kandy_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1lRYiydzs42ipNW6tDKWgPmxMRpOKid0o"
ccxcn_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1TVuDfJlySCJsGcb7UtRXTp_Ii8rFNHFp"
cs_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1RxqLwfUbvPiUfOfkpff7TdMbBQ8MhQc6"
usj_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1efMdMhXxUwAt90acpuA7-Hp0nnTYzkVr"
sliit_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1p5n-MQy9BpT90lLk_CvyOC-nOi_dD_7S"
nibm_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1IEYPQrNErhu2wiQlmYlj35Hc3rpIHRht"
ruhuna_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1_SU1BEdpLROzWU3e5vll5xcx2S9L9x8V"
rajarata_entity_workspace_goodluck_banner = "https://lh3.googleusercontent.com/d/1MXd-6WiUbDgyoiy9UQGg5Or_mk7OrDnb"

# Main Streamlit app
def main():
        
    st.set_page_config(
        layout="wide",
        page_title="NLDS2025 Hackathon",
        page_icon=mascot_image,
    )
    
    # col100, col101, col102 = st.columns([1, 18, 1])
    # with col101:
    st.image(title_image_path,use_column_width=True)

    st.markdown(
        "<hr style='border: 1px solid #000; width: 100%;'>",
        unsafe_allow_html=True
    )
    
    # col151 = st.columns(1)
    # with col151:
    #st.image(rajarata_entity_workspace_goodluck_banner, use_column_width=True)

    # st.markdown("<div style='text-align: left;'>"
    #             f"<h4>Select the type of data you want to view</h4>"
    #             "</div>",
    #             unsafe_allow_html=True,)
    data_mode = radio_button()
    # Set interval to 5 minutes
    st_autorefresh(interval=1 * 60 * 1000, key="data_refresh")
    # URL to your Google Sheets data
    # Datasource url / Google Sheets CSV
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSid0QnQOYSzZBEtZHwGhzkgdFF7pcxHxs8evjsqZ9H4vspzUlAg8JcuRNNj56XZZtnIxwlasRxjYhg/pub?gid=2141420671&single=true&output=csv"

    # Load data using the cached function
    data = load_data(sheet_url)

    if data is not None:
        # Check if the 'Entity' column exists in the DataFrame
        if 'Entity' in data.columns:  

            # calculation of leaderboard items
            fig_applied, df_entity_applied_total = applied_bar_chart_and_data(data, data_mode)
            fig_approved, df_entity_approved_total = approved_bar_chart_and_data(data, data_mode)
            fig_sus, df_entity_mou_total = mou_bar_chart_and_data(data, data_mode)
            fig_apltoapd, df_entity_apltoapd_total = applied_to_approved_ratio_bar_chart_and_data(df_entity_approved_total, df_entity_applied_total, data_mode)
            df_ranks = total_points(data, data_mode)

        # Merge all datasets
            df_combined = df_entity_applied_total.merge(
                df_entity_approved_total, on='Entity').merge(
                    df_entity_mou_total, on='Entity').merge(
                        df_entity_apltoapd_total, on='Entity').merge(df_ranks, on='Entity')

            # Calculate total values
            total_approved = df_entity_approved_total['Total_Approved'].sum()
            total_applied = df_entity_applied_total['Total_Applied'].sum()
            total_mou = df_entity_mou_total['Total_MoUs'].sum()

            # Display the summary numbers (total applications, total approvals, and conversion rate)
            display_summary_numbers(total_mou, total_approved, total_applied, data_mode)
     
            st.divider()

            st.subheader(f'🔥{data_mode} Leaderboard')

            # Display the leaderboard table
            display_leaderboard_table(df_combined, data_mode)

            # st.divider()

            # col204, col205 = st.columns([1, 1])

            # # applied bar chart
            # # with col204:
            # #     st.plotly_chart(fig_sus, use_container_width=True)

            # # approved bar chart
            # with col205:
            #     st.plotly_chart(fig_applied, use_container_width=True)

            # col206, col207 = st.columns([1, 1])

            # # applied to approved ratio bar chart
            # with col206:
            #     st.plotly_chart(fig_approved, use_container_width=True)

            # with col207:
            #     st.plotly_chart(fig_apltoapd, use_container_width=True)

            # ###############################################################################

            # st.divider()

            # col11, col12 = st.columns([9, 2])

            # with col11:

            #     st.subheader('Functional Analysis')
            #     # Create a select box to choose the 'Function'
            #     selected_function = st.selectbox(
            #         'Select Function', data['Function'].unique())

            # with col12:
            #     functional_image_rendering(selected_function)
            
            # SU_counts = count_SUs_by_entity(data, selected_function, data_mode)
            # fig_0 = px.bar(SU_counts, x='Entity', y='Count_SUs',
            #                title=f'📩 {data_mode} Sign Ups by Entity for {selected_function} Function',
            #                labels={'Entity': 'Entity', 'Count_SUs': 'Sign Ups'}, color='Entity')
            
            # functional_bar_charts_formatting(fig_0)

            # # Get the count of 'Applied' related to each entity based on the selected function
            # applied_counts = count_applied_by_entity(data, selected_function, data_mode)

            # # Create a bar chart using Plotly Express
            # fig_1 = px.bar(applied_counts, x='Entity', y='Count_Applied', 
            #                title=f'🌍 {data_mode} Applications by Entity for {selected_function} Function', 
            #                labels={'Entity': 'Entity', 'Count_Applied': 'Applications'}, color='Entity')
            
            # functional_bar_charts_formatting(fig_1)

            # # Get the count of 'Approved' related to each entity based on the selected function
            # approved_counts = count_approved_by_entity(data, selected_function, data_mode)

            # # Create a bar chart using Plotly Express
            # fig_2 = px.bar(approved_counts, x='Entity', y='Count_Approved', 
            #                title=f'✅ {data_mode} Approvals by Entity for {selected_function} Function',
            #                labels={'Entity': 'Entity', 'Count_Approved': 'Approvals'}, color='Entity')
            
            # functional_bar_charts_formatting(fig_2)

            # applied_to_approved_percent = count_applied_to_approved_ratio(
            #     data, selected_function, data_mode)

            # # Create a bar chart using Plotly Express
            # fig_3 = px.bar(applied_to_approved_percent, x='Entity', y='Applied_to_Approved_Ratio', 
            #                title=f'📊 {data_mode} Applied to Approved Ratio by Entity for {selected_function} Function',
            #                labels={'Entity': 'Entity', 'Applied_to_Approved_Ratio': 'Applied to Approved Ratio'}, color='Entity')

            # functional_bar_charts_formatting(fig_3)
        
            # ###############################################################################
            # if selected_function == "oGV" or selected_function == "oGTa" or selected_function == "oGTe":
            #     # st.write("<br><br>", unsafe_allow_html=True)
            #     col301, col302 = st.columns(2)

            #     with col301:
            #         st.plotly_chart(fig_0, use_container_width=True)

            #     with col302:
            #         st.plotly_chart(fig_1, use_container_width=True)

            #     col311, col312 = st.columns(2)

            #     with col311:
            #         st.plotly_chart(fig_2, use_container_width=True)

            #     with col312:
            #         st.plotly_chart(fig_3, use_container_width=True)
            
            # else:
            #     col5, col6 = st.columns(2)

            #     with col5:
            #         st.plotly_chart(fig_1, use_container_width=True)

            #     with col6:
            #         st.plotly_chart(fig_2, use_container_width=True)

            #     col13, col14, col15 = st.columns([1, 2, 1])

            #     with col14:
            #         st.plotly_chart(fig_3, use_container_width=True)

            # st.write("<br>", unsafe_allow_html=True)
            st.divider()

            # st.write("<br><br>", unsafe_allow_html=True)
            st.write("<p style='text-align: center;'>Made with ❤️ by &lt;/Dev.Team&gt; of <strong>AIESEC in Sri Lanka</strong></p>", unsafe_allow_html=True)
        else:
            st.error("The 'Entity' column does not exist in the loaded data.")
    else:
        st.error("Failed to load data.")


if __name__ == "__main__":
    main()














