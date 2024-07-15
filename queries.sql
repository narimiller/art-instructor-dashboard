-- START_QUERY: csize_over_time
WITH expanded AS
    (
    SELECT *
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    ORDER by cohort_id, module, assignment_full, username, datetime
    ),

posts AS 
    (
    SELECT cohort_id, module, assignment_full, username, datetime, 
        launch_start, term_start, term_end, COUNT(*) AS images_in_post
    FROM expanded
    GROUP BY cohort_id, module, assignment_full, username, datetime
    ),

first_seen AS
    (
    SELECT cohort_id, launch_start, term_start, term_end, username, assignment_full AS first_assignment, MIN(datetime) AS first_time
    FROM posts
    GROUP by cohort_id, username
    ORDER by cohort_id, first_assignment, username, datetime
    ),

final AS
    (
    SELECT DISTINCT cohort_id, username, launch_start, term_start, term_end, first_time AS datetime, 
        COUNT(username) OVER (PARTITION BY cohort_id ORDER BY first_time) AS cohort_size
    FROM first_seen
    ORDER BY cohort_id, first_time
    )

SELECT * FROM final;
-- END_QUERY: csize_over_time



-- START_QUERY: student_posts
 WITH posts AS 
    (
    SELECT cohort_id, c.name AS term_name, module, assignment_full, username, datetime
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    GROUP BY cohort_id, module, assignment_full, username, datetime
    ),

final AS
    (
    SELECT cohort_id, term_name, module, assignment_full AS assignment, username, COUNT(*) AS num_posts 
    FROM posts
    GROUP BY cohort_id, module, assignment, username
    ORDER BY cohort_id DESC
    )

SELECT * FROM final;
-- END_QUERY: student_posts



-- START_QUERY: term_completion
 WITH posted_modules AS 
    (
    SELECT cohort_id, c.name AS term_name, username, COUNT(DISTINCT module) AS num_modules
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    GROUP BY cohort_id, term_name, username
    ),

module_counts AS
    (
    SELECT cohort_id, COUNT(DISTINCT module) AS total_modules
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    GROUP BY cohort_id
    ),

final AS
    (
    SELECT p.cohort_id, p.username, p.num_modules, m.total_modules,
        100 * CAST(p.num_modules AS REAL)/m.total_modules AS percent_completion
    FROM posted_modules p
    INNER JOIN module_counts m
    ON p.cohort_id = m.cohort_id
    )

SELECT *,
    AVG(percent_completion) OVER (PARTITION BY cohort_id) AS avg_completion 
FROM final;
-- END_QUERY: term_completion



-- START_QUERY: posts_images
WITH final AS 
    (
    SELECT c.cohort_id, c.name AS term_name, u.module, 
        assignment_full AS assignment,
        u.username, u.datetime, COUNT(*) AS num_images
    FROM uploads u
    LEFT JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE u.assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    GROUP BY c.cohort_id, u.module, assignment, u.username, u.datetime
    )

SELECT * FROM final;
-- END_QUERY: posts_images



-- START_QUERY: alltime_totals
 WITH posts AS 
    (
    SELECT c.cohort_id, c.name AS term_name, u.module, assignment_full,
        u.username, u.datetime, COUNT(*) AS num_images
    FROM uploads u
    LEFT JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE u.assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    GROUP BY c.cohort_id, u.module, assignment_full, u.username, u.datetime
    ),
        
totals AS
    (
    SELECT COUNT(*) AS total_posts,
    COUNT(DISTINCT username) AS total_students,
    SUM(num_images) AS total_images
    FROM posts
    )

    SELECT * FROM totals;
-- END_QUERY: alltime_totals



-- START_QUERY: rates_by_grouping
WITH expanded AS
    (
    SELECT *
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    ORDER by cohort_id, module, assignment_full, username, datetime
    ),

posts AS 
    (
    SELECT cohort_id, module, assignment_full, username, datetime, COUNT(*) AS images_in_post
    FROM expanded
    GROUP BY cohort_id, module, assignment_full, username, datetime
    ),

posts_by_assignment AS
    (
    SELECT cohort_id, module, assignment_full, COUNT(DISTINCT username) AS posters_assn, COUNT(*) AS post_count_assn
    FROM posts
    GROUP BY cohort_id, module, assignment_full
    ),

posts_by_module AS
    (
    SELECT cohort_id, module, COUNT(DISTINCT username) AS posters_module, COUNT(*) AS post_count_module
    FROM posts
    GROUP BY cohort_id, module
    ),

cohort_sizes AS
    (
    SELECT cohort_id, COUNT(DISTINCT username) AS max_cohort_size
    FROM expanded
    GROUP BY cohort_id
    ),

final AS
    (
    SELECT p1.cohort_id, p1.module, p1.assignment_full AS assignment, 
        p1.post_count_assn, p1.posters_assn, p2.posters_module, c.max_cohort_size
    FROM posts_by_assignment p1
    INNER JOIN posts_by_module p2
        ON p1.cohort_id = p2.cohort_id AND p1.module = p2.module
    INNER JOIN cohort_sizes c
        ON p1.cohort_id = c.cohort_id
    )

SELECT *, 
    100 * CAST(posters_assn AS REAL)/max_cohort_size AS participation_rate_assn,
    100 * CAST(posters_module AS REAL)/max_cohort_size AS participation_rate_module
    FROM final;
-- END_QUERY: rates_by_grouping



-- START_QUERY: rates_with_nulls
WITH expanded AS
(
    SELECT *
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE u.assignment IN
        (SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*')
    ORDER BY c.cohort_id, u.module, assignment_full, u.username, u.datetime
),

posts AS 
(
    SELECT cohort_id, module, assignment_full, username, datetime, COUNT(*) AS images_in_post
    FROM expanded
    GROUP BY cohort_id, module, assignment_full, username, datetime
),

posts_by_assignment AS
(
    SELECT cohort_id, module, assignment_full, COUNT(DISTINCT username) AS posters_assn, COUNT(*) AS post_count_assn
    FROM posts
    GROUP BY cohort_id, module, assignment_full
),

posts_by_module AS
(
    SELECT cohort_id, module, COUNT(DISTINCT username) AS posters_module, COUNT(*) AS post_count_module
    FROM posts
    GROUP BY cohort_id, module
),

cohort_sizes_ AS
(
    SELECT cohort_id, COUNT(DISTINCT username) AS max_cohort_size
    FROM expanded
    GROUP BY cohort_id
),

cohort_sizes AS
(
    SELECT *, SUM(max_cohort_size) OVER () AS sum_cohort_sizes
    FROM cohort_sizes_
),

unique_cohorts AS
(
    SELECT DISTINCT cohort_id FROM expanded
),

unique_assignments AS
(
    SELECT DISTINCT assignment_full FROM expanded
),

cohort_assignment_combinations AS
(
    SELECT uc.cohort_id, ua.assignment_full
    FROM unique_cohorts uc
    CROSS JOIN unique_assignments ua
),

final AS
(
    SELECT cac.cohort_id, p1.module, cac.assignment_full AS assignment, 
        p1.post_count_assn, p1.posters_assn, p2.posters_module, c.max_cohort_size,
        p1.post_count_assn*c.max_cohort_size AS weighted_posts_assn,
        p2.post_count_module*c.max_cohort_size AS weighted_posts_module,
        c.sum_cohort_sizes
    FROM cohort_assignment_combinations cac
    LEFT JOIN posts_by_assignment p1
        ON cac.cohort_id = p1.cohort_id AND cac.assignment_full = p1.assignment_full
    LEFT JOIN posts_by_module p2
        ON cac.cohort_id = p2.cohort_id AND p1.module = p2.module
    LEFT JOIN cohort_sizes c
        ON cac.cohort_id = c.cohort_id
)

SELECT *,
    100 * CAST(posters_assn AS REAL) / max_cohort_size AS participation_rate_assn,
    100 * CAST(posters_module AS REAL) / max_cohort_size AS participation_rate_module
FROM final
ORDER BY cohort_id, module, assignment;
-- END_QUERY: rates_with_nulls



-- START_QUERY: posts_all
WITH posts AS 
    (
    SELECT cohort_id, c.name AS term_name, module, assignment_full, username, datetime
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
    SELECT DISTINCT username, recent_cohort_id, term_name,
    CASE WHEN cohort_id IS NULL THEN "between terms" ELSE cohort_id END AS cohort_id
    FROM recent_term
    ORDER BY username
    ),

user_assignments AS
    (
    SELECT uc.username, uc.recent_cohort_id, 
        uc.cohort_id, uc.term_name, 
        ca.module, ca.assignment_full AS assignment
    FROM user_cohorts uc
    INNER JOIN cohort_assignments ca
        ON uc.recent_cohort_id = ca.cohort_id
    ),

post_count AS
    (
    SELECT
        CASE WHEN cohort_id IS NULL THEN 'between terms' ELSE cohort_id END AS cohort_id,
        recent_cohort_id, module, assignment_full AS assignment, username, COUNT(datetime) AS num_posts
    FROM recent_term
    GROUP BY cohort_id, recent_cohort_id, module, assignment, username
    ),

final AS
    (
    SELECT ua.cohort_id, ua.term_name,
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
    )

SELECT * FROM final;
-- END_QUERY: posts_all



-- START_QUERY: committed_participants
WITH posts AS 
(
    SELECT cohort_id, module, assignment, username, datetime
    FROM uploads u
    INNER JOIN cohorts c
        ON u.datetime BETWEEN c.launch_start AND DATE(c.term_end, ?)
    WHERE assignment IN (
        SELECT DISTINCT assignment
        FROM uploads 
        WHERE assignment GLOB 'A[0-9]*'
    )
    GROUP BY cohort_id, module, assignment, username, datetime
),

cohort_modules AS 
(
    SELECT cohort_id, COUNT(DISTINCT module) AS total_modules
    FROM posts
    GROUP BY cohort_id
),

user_modules AS 
(
    SELECT cohort_id, username, COUNT(DISTINCT module) AS modules_submitted
    FROM posts
    GROUP BY cohort_id, username
),

students_30_plus AS 
(
    SELECT u.cohort_id, u.username, u.modules_submitted, c.total_modules,
        CASE WHEN u.modules_submitted * 1.0 / c.total_modules >= 0.3 THEN 1 ELSE 0 END AS _30_plus
    FROM user_modules u
    INNER JOIN cohort_modules c
    ON u.cohort_id = c.cohort_id
)

SELECT 
    cohort_id,
    COUNT(DISTINCT username) AS total_students,
    SUM(_30_plus) AS num_students_30_plus,
    ROUND((SUM(_30_plus) * 1.0 / COUNT(DISTINCT username)) * 100, 2) AS percentage_30_plus
FROM students_30_plus 
GROUP BY cohort_id
-- END_QUERY: committed_participants