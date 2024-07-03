# Art Instructor Dashboard
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://art-instructor-dashboard.streamlit.app/)

## Overview
This repository contains a demo version of an Instructor Dashboard, which is designed to provide insights and analytics for online art courses. The dashboard tracks metrics such as student participation, module completion rates, and overall engagement. The demo data is generated to simulate real usage and does not reflect actual student information. There are also no images to display in this demo.

The real dashboard is being used by the instructor-stakeholder to enhance the learning experience and improve course outcomes. Currently the dashboard uses data for a single course, but support will be added for additional courses in the future.

## Credit
This project is being developed in collaboration with [@dorian-iten](https://github.com/dorian-iten). His insights and feedback have been crucial in shaping the functionality of this dashboard.

## Pages
#### Students
Metrics and plots for individual students.<br>
Filters: All assignments, regardless of when they were posted.
#### Cohorts
Metrics and plots for specific cohorts/terms.<br>
Filters: All assignments posted during a term (timestamp is between `launch_start` and 14 days after `term_end`).
#### Courses
All-time metrics and plots for The Shading Course.<br>
Filters: All assignments for metric cards. All assignments posted during a term for the rest of the page.

## Definitions
- **Post**: Image records from uploads.csv with the same cohort_id, module, assignment, username, datetime.
- **Active Participants**: Students who have made at least one post within the term.
- **Committed Participants**: Students who have posted in 30% or more available modules during the term.
- **Cohort Size:** Total number of active participants for a term.

## Statistics

| Name          | Definition                                         | Formula                                                                | Significance                                          |
|----------------------|----------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| **Participation Rate**      | The percentage of students who post at least once in a module or assignment.           | ```100 * COUNT(students_who_posted) / cohort_size```                               | Indicates how much of the student body is participating in different areas of the course. Breadth of engagement.          |
| **Avg Participation Rate**      | Same as above, averaged across all cohorts.           | ```AVG(100 * COUNT(students_who_posted) / cohort_size)```                               | |
| **Weighted Avg Posts/Cohort**     | Average number of posts per cohort, weighted by cohort size.      | ```SUM(num_posts * cohort_size) / SUM(cohort_size)```               | Shows what modules and assignments generate more activity from participating students. Depth of engagement.               |
| **Completion Rate**   | The percentage of modules in which a student has posted at least once, out of the total number of modules available to them at the time they participated.         | ```100 * COUNT(modules_posted) / total_modules``` | Understand individual student behavior.       |
| **Avg Completion Rate** | Same as above, averaged across all students.        | ```AVG(100 * COUNT(modules_posted) / total_modules)``` | Understand the behavior of the average student.     |
| **Avg Completion Rate (cohorts page)** | The percentage of modules a student has completed within the selected term, averaged across all active participants.        | ```AVG(100 * COUNT(modules_posted_during_term) / total_modules_during_term)``` | Understand completion  within a single term.     |
<br>

## Future Work
- Refactor code to accommodate additional courses.
- Consider using an additional table (terms + all assignments for those terms) in order to provide every possible cohort-assignment combination. Currently, the code relies on there being at least one post in a cohort-assignment pair for it to be displayed in heatmaps and used in calculations.