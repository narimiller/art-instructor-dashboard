import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
from utils import load_card_css, create_metric_card, read_query_from_file, TERM_END_BUFFER

def app():
    #######################
    # Queries
    conn = sqlite3.connect('data.db')
    query_file_path = 'queries.sql'
    
    # All-time totals
    q = read_query_from_file(query_file_path, 'alltime_totals')
    alltime_totals = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # rates by grouping, including null modules & assignments
    q = read_query_from_file(query_file_path, 'rates_with_nulls')
    rates_by_grouping = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # all assignment posts, including "between terms" category
    q = read_query_from_file(query_file_path, 'posts_all')
    posts = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER, TERM_END_BUFFER))

    # Cohort sizes over time
    q_all = """
    SELECT c.cohort_id, c.name as term_name, COUNT(DISTINCT u.username) as total_students
    FROM cohorts c
    LEFT JOIN uploads u
    ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, '{TERM_END_BUFFER}')
    WHERE u.username IS NOT NULL
    GROUP BY c.cohort_id, c.name
    ORDER BY c.cohort_id
    """
    q_all = q_all.format(TERM_END_BUFFER=TERM_END_BUFFER)
    cohort_sizes_all = pd.read_sql_query(q_all, conn)

    q_3_modules = """
    SELECT cohort_id, term_name, COUNT(username) AS total_students
    FROM (
        SELECT c.cohort_id, c.name AS term_name, u.username, COUNT(DISTINCT u.module) AS modules_count
        FROM uploads u
        INNER JOIN cohorts c ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, '{TERM_END_BUFFER}')
        GROUP BY c.cohort_id, c.name, u.username
        HAVING modules_count >= 3
    )
    GROUP BY cohort_id, term_name
    ORDER BY cohort_id
    """
    q_3_modules = q_3_modules.format(TERM_END_BUFFER=TERM_END_BUFFER)
    cohort_sizes_3_modules = pd.read_sql_query(q_3_modules, conn)

    conn.close()

    #######################
    # Theme

    primaryColor = st.get_option('theme.primaryColor')
    backgroundColor = st.get_option('theme.backgroundColor')
    secondaryBackgroundColor = st.get_option('theme.secondaryBackgroundColor')
    textColor = st.get_option('theme.textColor')

    #######################
    # Plotting functions
    
    def make_participation_barplot(df, x_name, y_name):
        grouped_df = df[[x_name, y_name]].groupby([x_name]).mean().reset_index()
        sorted_df = grouped_df.sort_values(by=x_name, ascending=True)
        
        fig = px.bar(sorted_df, x=x_name, y=y_name,
                     custom_data=[sorted_df[x_name], sorted_df[y_name]])
        
        y_name_custom = "Participation Rate"
        hover_template = f"{x_name.capitalize()}: %{{customdata[0]}}<br>{y_name_custom}: %{{customdata[1]:.1f}}%<extra></extra>"
        fig.update_traces(hovertemplate=hover_template)       
        
        tickangle = 90 if x_name == 'assignment' else 0
        
        fig.update_layout(
            xaxis_title=x_name.capitalize(),
            yaxis_title="Avg Participation Rate per Cohort (%)",
            xaxis=dict(tickangle=tickangle, tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(range=[0,100]),
            height=500,
            margin=dict(t=10)
        )
        
        return fig
    
    def make_totals_barplot(df, x_name, weighted_posts):
        denominator = df['sum_cohort_sizes'][0]
        if x_name == 'module':
            df = df.drop_duplicates(subset=['cohort_id', 'module', 'weighted_posts_module'])

        grouped_df = df[[x_name, weighted_posts]].groupby([x_name]).sum().reset_index()
        grouped_df['weighted_avg'] = grouped_df[weighted_posts]/denominator
        sorted_df = grouped_df.sort_values(by=x_name, ascending=True)
        
        fig = px.bar(sorted_df, x=x_name, y='weighted_avg',
                     custom_data=[sorted_df[x_name], sorted_df['weighted_avg']])
        
        y_name_custom = "Avg Posts"
        hover_template = f"{x_name.capitalize()}: %{{customdata[0]}}<br>{y_name_custom}: %{{customdata[1]:.1f}}<extra></extra>"
        fig.update_traces(hovertemplate=hover_template)
        
        tickangle = 90 if x_name == 'assignment' else 0
        
        fig.update_layout(
            xaxis_title=x_name.capitalize(),
            yaxis_title="Avg Total Posts per Cohort",
            xaxis=dict(tickangle=tickangle, tickmode='linear', tick0=1, dtick=1),
            height=500,
            margin=dict(t=10)
        )
        
        return fig

    def make_cohort_lineplot(df, x_name, y_name): 
        df = df[['cohort_id', x_name, y_name]]
        df_new = df.drop_duplicates() if x_name =='module' else df
        df_sorted = df_new.sort_values(by=['cohort_id', x_name], ascending=True)
        
        unique_cohort_ids = df_sorted['cohort_id'].unique()

        # Display most recent 15 cohorts on legend, select most recent 3
        recent_cohort_ids_legend = unique_cohort_ids[-15:] if len(unique_cohort_ids) >= 15 else unique_cohort_ids
        recent_cohort_ids_selected = unique_cohort_ids[-3:]
        
        fig = px.line(df_sorted, x=x_name, y=y_name, color='cohort_id',
                      custom_data=[df_sorted[x_name], df_sorted[y_name], df_sorted['cohort_id']])

        y_name_custom = "Participation Rate"
        hover_template = f"Cohort ID: %{{customdata[2]}}<br>{x_name.capitalize()}: %{{customdata[0]}}<br>{y_name_custom}: %{{customdata[1]:.1f}}%<extra></extra>"
        fig.update_traces(hovertemplate=hover_template)

        # legend visibility
        for trace in fig.data:
            trace.visible = True if trace.name in recent_cohort_ids_legend else 'legendonly' # type: ignore
    
        # trace selection
        for trace in fig.data:
            trace.visible = True if trace.name in recent_cohort_ids_selected else 'legendonly' # type: ignore

        tickangle = 90 if x_name == 'assignment' else 0
        fig.update_traces(connectgaps=True)
        fig.update_layout(
                xaxis_title=x_name.capitalize(),
                yaxis_title='Participation Rate (%)',
                xaxis=dict(tickangle=tickangle, tickmode='linear', tick0=1, dtick=1),
                yaxis=dict(range=[0,100]),
                height=500,
                margin=dict(t=10)
            )
        
        return fig

    def make_participation_trend_chart(df, title):
        df = df[df['total_students'] > 0]  # Exclude cohorts with 0 uploads/participation
        fig = px.line(df, x='term_name', y='total_students',
                      markers=True, line_shape='linear', title=title)
        
        # Add annotations to each data point
        fig.add_trace(go.Scatter(
            x=df['term_name'],
            y=df['total_students'],
            mode='markers+text',
            text=df['total_students'],
            textposition='top center',
            textfont=dict(size=16),  # Double the font size
            showlegend=False
        ))

        fig.update_layout(
            xaxis_title='',
            yaxis_title='Total Active Students',
            margin=dict(t=20)
        )
        return fig

    def make_combined_participation_trend_chart(df1, df2):
        df1 = df1[df1['total_students'] > 0]  # Exclude cohorts with 0 uploads/participation
        df2 = df2[df2['total_students'] > 0]  # Exclude cohorts with 0 uploads/participation
        df1['type'] = 'All'
        df2['type'] = '3+ Modules'
        combined_df = pd.concat([df1, df2])
        
        fig = px.line(combined_df, x='term_name', y='total_students', color='type',
                      markers=True, line_shape='linear', title='Participation Trends')

        # Add annotations to each data point
        fig.add_trace(go.Scatter(
            x=combined_df['term_name'],
            y=combined_df['total_students'],
            mode='markers+text',
            text=combined_df['total_students'],
            textposition='top center',
            textfont=dict(size=16),  # Double the font size
            showlegend=False
        ))

        fig.update_layout(
            xaxis_title='',
            yaxis_title='Total Active Students',
            margin=dict(t=20)
        )
        return fig

    #######################
    # Main panel
  
    st.title("The Super Awesome Drawing Course")
    
    # Calculate avg completion
    student_modules = posts.groupby('username')['module'].nunique().reset_index()
    posted_modules = posts[posts['num_posts'] > 0].groupby('username')['module'].nunique().reset_index()
    completion_df = student_modules.merge(posted_modules, on='username', how='left', suffixes=('_total', '_posted'))
    completion_df['percent_completion'] = (completion_df['module_posted']/completion_df['module_total']) * 100
    
    row1 = st.columns(3)
    load_card_css(secondaryBackgroundColor)
    with row1[0]:
        create_metric_card(
            title='Active Participants',
            value=alltime_totals['total_students'][0]
        )
    with row1[1]:
        create_metric_card(
            title='Total Images',
            value=alltime_totals['total_images'][0]
        )    
    with row1[2]:
        create_metric_card(
            title='Average Completion',
            value=f"{int(round(completion_df['percent_completion'].mean(), 0))}%"

        )    

    st.markdown('#### Participation per Cohort')
    
    toggle = ui.tabs(
        options=["All", "3+ Modules", "Both"],
        default_value="All",
        key="participation_toggle"
    )

    if toggle == "All":
        selected_df = cohort_sizes_all
        st.plotly_chart(make_participation_trend_chart(selected_df, 'Participation Trends (All)'), use_container_width=True, theme='streamlit')
    elif toggle == "3+ Modules":
        selected_df = cohort_sizes_3_modules
        st.plotly_chart(make_participation_trend_chart(selected_df, 'Participation Trends (3+ Modules)'), use_container_width=True, theme='streamlit')
    elif toggle == "Both":
        st.plotly_chart(make_combined_participation_trend_chart(cohort_sizes_all, cohort_sizes_3_modules), use_container_width=True, theme='streamlit')

    row2 = st.columns(3, gap='medium')
    with row2[1]:
        st.markdown('#### Avg Participation Rate')
        avg_rate_tabs = ui.tabs(
            options=['Modules', 'Assignments'],
            default_value='Modules',
            key="avg_rate_tabs",
            )
        if avg_rate_tabs == 'Modules':
            st.plotly_chart(make_participation_barplot(rates_by_grouping, 'module', 'participation_rate_module'), use_container_width=True, theme='streamlit')
        else:
            st.plotly_chart(make_participation_barplot(rates_by_grouping, 'assignment', 'participation_rate_assn'), use_container_width=True, theme='streamlit')

    with row2[2]:
        st.markdown('#### Cohort Participation Rates')
        cohort_rate_tabs = ui.tabs(
            options=['Modules', 'Assignments'],
            default_value='Modules',
            key="cohort_rate_tabs",
            )
        if cohort_rate_tabs == 'Modules':
            st.plotly_chart(make_cohort_lineplot(rates_by_grouping, 'module', 'participation_rate_module'), use_container_width=True, theme='streamlit')
        else:
            st.plotly_chart(make_cohort_lineplot(rates_by_grouping, 'assignment', 'participation_rate_assn'), use_container_width=True, theme='streamlit')
     
    with row2[0]:
        st.markdown('#### Avg Total Posts (weighted)')
        weighted_avg_tabs = ui.tabs(
            options=['Modules', 'Assignments'],
            default_value='Modules',
            key="weighted_avg_tabs",
            )
        if weighted_avg_tabs == 'Modules':
            st.plotly_chart(make_totals_barplot(rates_by_grouping, 'module', 'weighted_posts_module'), use_container_width=True, theme='streamlit')
        else:
            st.plotly_chart(make_totals_barplot(rates_by_grouping, 'assignment', 'weighted_posts_assn'), use_container_width=True, theme='streamlit')
    
# Run the app
if __name__ == '__main__':
    app()