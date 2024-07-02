-- START_QUERY: completion_report
WITH posts AS 
    (
    SELECT cohort_id, c.name AS term_name, module, 
        assignment_full, username, datetime
    FROM uploads u
    LEFT JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment GLOB 'A[0-9]*'
    GROUP BY cohort_id, module, assignment_full, username, datetime
    ),

recent_term AS 
    (
    SELECT p.*, 
        COALESCE(p.cohort_id, 
            (SELECT c.cohort_id
             FROM cohorts c
             WHERE p.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
             ORDER BY c.term_end DESC
             LIMIT 1),
            (SELECT c.cohort_id
             FROM cohorts c
             WHERE p.datetime >= c.launch_start
             ORDER BY c.term_end DESC
             LIMIT 1)
        ) AS recent_cohort_id
    FROM posts p
    ),

cohort_assignments AS 
    (
    SELECT DISTINCT cohort_id, module, assignment_full
    FROM posts
    WHERE cohort_id IS NOT NULL
    ),

user_cohorts AS
    (
    SELECT DISTINCT username, recent_cohort_id, 
    CASE WHEN cohort_id IS NULL THEN "between terms" ELSE cohort_id END AS cohort_id
    FROM recent_term
    ORDER BY username
    ),

user_assignments AS
    (
    SELECT uc.username, uc.recent_cohort_id, 
        uc.cohort_id, 
        ca.module, ca.assignment_full AS assignment
    FROM user_cohorts uc
    INNER JOIN cohort_assignments ca
        ON uc.recent_cohort_id = ca.cohort_id
    ),

post_count AS
    (
    SELECT
        CASE WHEN cohort_id IS NULL THEN "between terms" ELSE cohort_id END AS cohort_id,
        recent_cohort_id, module, assignment_full AS assignment, username, COUNT(datetime) AS num_posts
    FROM recent_term
    GROUP BY cohort_id, recent_cohort_id, module, assignment, username
    ),

posts_all AS
    (
    SELECT ua.cohort_id, 
        ua.recent_cohort_id, ua.module, ua.assignment, ua.username, 
        COALESCE(p.num_posts, 0) AS num_posts
    FROM user_assignments ua
    LEFT JOIN post_count p
        ON ua.recent_cohort_id = p.recent_cohort_id
        AND ua.cohort_id = p.cohort_id 
        AND ua.module = p.module 
        AND ua.assignment = p.assignment 
        AND ua.username = p.username
    WHERE ua.username IN (SELECT DISTINCT username FROM posts)
    ORDER BY ua.cohort_id, ua.username, ua.module, ua.assignment
    ),

summed_posts AS
    (
    SELECT username, module, SUM(num_posts) AS sum_posts,
        CASE WHEN SUM(num_posts) = 0 THEN 1 ELSE 0 END AS missing
    FROM posts_all
    GROUP BY username, module
    ORDER BY username
    ),

counts AS
    (
    SELECT 
        username,
        COUNT(module) AS modules_available,
        SUM(CASE WHEN sum_posts > 0 THEN 1 ELSE 0 END) AS modules_posted
    FROM summed_posts
    GROUP BY username
    ),

missing AS
    (
    SELECT username,
    GROUP_CONCAT(module) AS missing_modules
    FROM summed_posts
    WHERE missing = 1
    GROUP BY username
    ),

final AS
    (
    SELECT c.username, c.modules_posted, c.modules_available, 
    ROUND(100*CAST(c.modules_posted AS REAL)/c.modules_available, 1) AS percent_completion,
    m.missing_modules
    FROM counts c
    LEFT JOIN missing m
    ON c.username = m.username
    ORDER BY percent_completion DESC, c.username ASC
    )

SELECT * FROM final;
-- END_QUERY: completion_report