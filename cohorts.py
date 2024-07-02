import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit_shadcn_ui as ui
from streamlit_extras.add_vertical_space import add_vertical_space
from utils import load_card_css, create_metric_card, read_query_from_file, TERM_END_BUFFER

def app():

    #######################
    # Queries
    
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
   
    query_file_path = 'queries.sql'
    
    # Cohort size over time
    q = read_query_from_file(query_file_path, 'csize_over_time')
    csize_over_time = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))
    
    # Student posts
    q = read_query_from_file(query_file_path, 'student_posts')
    student_posts = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # posts, rates by module, assignment
    q = read_query_from_file(query_file_path, 'rates_by_grouping')
    rates_by_grouping = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # committed participants (posted in 30% or more of modules in selected cohort)
    q = read_query_from_file(query_file_path, 'committed_participants')
    committed_participants = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # avg term completion
    q = read_query_from_file(query_file_path, 'term_completion')
    term_completion = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER, TERM_END_BUFFER))
    
    # completion_report
    query_file_path2 = 'reports.sql'
    q = read_query_from_file(query_file_path2, 'completion_report')
    completion_report = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER, TERM_END_BUFFER))
    
    conn.close()
    
    #######################
    # Theme

    primaryColor = st.get_option('theme.primaryColor')
    backgroundColor = st.get_option('theme.backgroundColor')
    secondaryBackgroundColor = st.get_option('theme.secondaryBackgroundColor')
    textColor = st.get_option('theme.textColor')
    
    #######################
    # Plots
    
    def calculate_percent_change(df, cohort_id, subject):
        cohort_options = sorted(df['cohort_id'].unique(), reverse=False) 
        idx = cohort_options.index(cohort_id)      
        selected_cohort_df = df[df['cohort_id'] == cohort_id]
        previous_cohort_df = df[df['cohort_id'] == cohort_options[idx-1]]
        current_size = selected_cohort_df[subject].max()
        previous_size = previous_cohort_df[subject].max()
        percent_change = (current_size - previous_size) / previous_size * 100

        return round(percent_change, 1)
    
    def calculate_percentage_point_change(df, cohort_id, subject):
        cohort_options = sorted(df['cohort_id'].unique(), reverse=False) 
        idx = cohort_options.index(cohort_id)      
        selected_cohort_df = df[df['cohort_id'] == cohort_id]
        previous_cohort_df = df[df['cohort_id'] == cohort_options[idx-1]]
        current = selected_cohort_df[subject].iloc[0]
        previous = previous_cohort_df[subject].iloc[0]
        percentage_point_change = current - previous

        return round(percentage_point_change, 1)
    
    def make_heatmap(df, cohort_id, x_name):
        # Filter based on cohort_id
        filtered_df = df[df['cohort_id'] == cohort_id]
        if x_name == 'module':
            filtered_df = filtered_df.groupby(['username', 'module']). sum().reset_index()
        
        custom_colorscale = [
                [0.0, backgroundColor],
                [0.4, '#1499FF'],
                [1.0, '#B8E0FF']
        ]
        
        # Reshape df for heatmap
        heatmap_data = filtered_df.pivot_table(index='username', columns=x_name, values='num_posts')
        heatmap_data.fillna(0, inplace=True)

        # Calculate total posts per user and sort
        heatmap_data['total_posts'] = heatmap_data.sum(axis=1)
        heatmap_data = heatmap_data.sort_values(by='total_posts', ascending=False)
        heatmap_data = heatmap_data.drop(columns=['total_posts'])

        fig = px.imshow(heatmap_data, aspect='auto', color_continuous_scale=custom_colorscale, zmin=0)
        
        fig.update_traces(
            hovertemplate=f'{x_name.capitalize()}: %{{x}}<br>Username: %{{y}}<br>Posts: %{{z}}<extra></extra>',
            xgap=2,
            ygap=2
        )

        tickangle = 45 if x_name == 'assignment' else 0     
        # add 15px for each student beyond 50 students
        num_usernames = heatmap_data.index.nunique()
        height = 750 + (num_usernames - 50)*15 if num_usernames > 50 else 750
        
        fig.update_layout(
            xaxis_title=x_name.capitalize(),
            yaxis_title="Username",
            yaxis_nticks=len(filtered_df),
            xaxis_nticks=len(filtered_df[x_name].unique()),
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                tickangle=tickangle
            ),
            height=height,
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            margin=dict(t=10)
        )

        return fig
    
    def csize_lineplot(df, cohort_id):
        filtered_df = df[df['cohort_id']==cohort_id]
        fig = px.line(filtered_df, x="datetime", y="cohort_size", 
                      custom_data=[filtered_df["datetime"], filtered_df["cohort_size"]])

        y_name_custom = "Active Participants"
        hover_template = f"Datetime: %{{customdata[0]}}<br>{y_name_custom}: %{{customdata[1]}}<extra></extra>"
        fig.update_traces(hovertemplate=hover_template)
        
        fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Active Participants",
                margin=dict(t=10)
            )
        fig.update_xaxes(range=[filtered_df['term_start'], filtered_df['term_end']])

        return fig
    
    def make_barplot(df, cohort_id, x_name, y_name):
        if x_name == 'module':
            df = df[['cohort_id', 'module', 'participation_rate_module']].drop_duplicates()
        filtered_df = df[df['cohort_id'] == cohort_id]
        fig = px.bar(filtered_df, x=x_name, y=y_name,
                            custom_data = [filtered_df[x_name], filtered_df[y_name]]
                            )
        y_name_custom = 'Participation Rate'
        hover_template = f"{x_name.capitalize()}: %{{customdata[0]}}<br>{y_name_custom}: %{{customdata[1]:.1f}}%<extra></extra>"

        fig.update_traces(hovertemplate=hover_template)
        
        tickangle = 45 if x_name == 'assignment' else 0 
        
        fig.update_layout(
            xaxis_title=x_name.capitalize(),
            yaxis_title="Participation Rate (%)",
            xaxis=dict(tickangle=tickangle, tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(range=[0,100]),
            margin=dict(t=10)
            )
        
        return fig

    #######################
    # Main panel

    # Dropdown menu for selecting cohort
    cohort_options = sorted(student_posts['cohort_id'].unique(), reverse=True)
    selected_cohort = st.selectbox('Select cohort', cohort_options)
    term = student_posts[student_posts['cohort_id'] == selected_cohort]['term_name'].unique()[0]

    st.title(f"{selected_cohort}: {term}") 

    # Top row with info cards
    top_row = st.columns(3)
    load_card_css(secondaryBackgroundColor)
    with top_row[0]:
        # number of active students
        filtered_csize = csize_over_time[csize_over_time['cohort_id'] == selected_cohort]
        size_diff_csize = calculate_percent_change(csize_over_time, selected_cohort, 'cohort_size')
        delta_str_csize = f"{size_diff_csize:+.1f} % from previous term"  # The + sign ensures positive numbers have a + prefix
        create_metric_card(title='Active Participants', 
                           value=filtered_csize['cohort_size'].max(),
                           subtext=delta_str_csize)
    
    with top_row[1]:
        # sum of participants with posts in 30%+ of available modules in chosen cohort
        size_diff_cp = calculate_percent_change(committed_participants, selected_cohort, 'num_students_30_plus')
        delta_str_cp = f"{size_diff_cp:+.1f} % from previous term"
        filtered_cp = committed_participants[committed_participants['cohort_id'] == selected_cohort]
        create_metric_card(title="Committed Participants", 
                           value=filtered_cp['num_students_30_plus'].iloc[0],
                           subtext=delta_str_cp)

    with top_row[2]:
        # avg completion rate of chosen cohort
        size_diff_tc = calculate_percentage_point_change(term_completion, selected_cohort, 'avg_completion')
        delta_str_tc = f"{size_diff_tc:+} from previous term"
        filtered_tc = term_completion[term_completion['cohort_id'] == selected_cohort]
        create_metric_card(title="Average Completion", 
                           value=f"{round(filtered_tc['percent_completion'].mean(), 1)}%", 
                           subtext=delta_str_tc)
    
    st.markdown('#### Post Activity')
    heatmap_tabs = ui.tabs(
        options=['Modules', 'Assignments'],
        default_value='Modules',
        key="heatmap_tabs",
    )
    if heatmap_tabs == 'Modules':
        x_label = 'module'
    else:
        x_label = 'assignment'
    st.plotly_chart(make_heatmap(student_posts, selected_cohort, x_label), 
                    use_container_width=True, theme="streamlit")
    
    add_vertical_space(1)

    row2 = st.columns(2, gap='medium')

    with row2[0]:
        
        st.markdown('#### Participation Rate')
        participation_tabs = ui.tabs(
            options=['Modules', 'Assignments'],
            default_value='Modules',
            key="participation_tabs",
            )
        if participation_tabs == 'Modules':
            st.plotly_chart(make_barplot(rates_by_grouping, selected_cohort, 'module', 'participation_rate_module'), use_container_width=True, theme='streamlit')
        else:
            st.plotly_chart(make_barplot(rates_by_grouping, selected_cohort, 'assignment', 'participation_rate_assn'), use_container_width=True, theme='streamlit')
    
    with row2[1]:   
        st.markdown('#### Cohort Size Over Time')
        add_vertical_space(5)  # Align charts

        st.plotly_chart(csize_lineplot(csize_over_time, selected_cohort), use_container_width=True, theme="streamlit")


    #######################
    # Generate completion report

    def export_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    def display_report(df):

        csv = export_csv(df)

        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='report.csv',
            mime='text/csv',
        )
    
    if st.button("Create Term Report"):
        st.write(f"#### Completion Report: {selected_cohort}")
        filtered_df = student_posts[student_posts['cohort_id'] == selected_cohort]
        cohort_usernames = filtered_df['username'].unique()    
        term_report = completion_report[completion_report['username'].isin(cohort_usernames)].reset_index(drop=True)
        st.dataframe(term_report, use_container_width=True)    
        display_report(term_report)
    
    if st.button("Create All-time Report"):
        st.write(f"#### Completion Report: All-time")
        alltime_report = completion_report
        st.dataframe(alltime_report, use_container_width=True) 
        display_report(alltime_report)        


if __name__ == "__main__":
    app()