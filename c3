
WITH children AS (
    SELECT
        c.parent_code AS parent_code,
        json_agg(
            json_build_object(
                'code', c.code,
                'title', c.title,
                'description', c.description,
                'questions_by_age_group', COALESCE(
                    (
                        SELECT json_agg(
                            json_build_object(
                                'age_group', v.age_group,
                                'questions', COALESCE(
                                    (
                                        SELECT json_agg(
                                            json_build_object(
                                                'code', q.unique_code,
                                                'text', q.question,
                                                'question_by_category', (
                                                    SELECT json_agg(
                                                        json_build_object(
                                                            'category',
                                                            cq.category,
                                                            'answers', COALESCE(
                                                                (
                                                                    SELECT json_agg(
                                                                        json_build_object(
                                                                            'code', a.unique_code,
                                                                            'text', a.answer
                                                                        )
                                                                        ORDER BY a.unique_code
                                                                    )
                                                                    FROM answer a
                                                                    JOIN question_answer_view v2
                                                                      ON a.unique_code = v2.answer_code
                                                                    JOIN category_question_view cqv2
                                                                      ON cqv2.question_code = v2.question_code
                                                                      AND cqv2.age_group = v2.age_group
                                                                    WHERE v2.question_code = q.unique_code
                                                                      AND v2.age_group = v.age_group
                                                                      AND cqv2.category_question_code = ANY (
                                                                          CASE cq.code
                                                                              WHEN 'C3' THEN ARRAY['C1','C2']
                                                                              WHEN 'C6' THEN ARRAY['C4','C5']
                                                                              WHEN 'C9' THEN ARRAY['C7','C8']
                                                                              -- add more combined categories here
                                                                              ELSE ARRAY[cq.code]
                                                                          END
                                                                      )
                                                                ),
                                                                '[]'::json
                                                            )
                                                        )
                                                        ORDER BY cq.category
                                                    )
                                                    FROM (
                                                        SELECT DISTINCT cqv.category_question_code, cqv.question_code
                                                        FROM category_question_view cqv
                                                        WHERE cqv.question_code = q.unique_code
                                                    ) cqv_dist
                                                    JOIN category_question cq
                                                      ON cqv_dist.category_question_code = cq.code
                                                )
                                            )
                                            ORDER BY q.unique_code
                                        )
                                        FROM question q
                                        WHERE q.parent_code = CASE 
                                                                  WHEN v.age_group = 'under_8_year_old' THEN c.code
                                                                  WHEN v.age_group = 'over_8_year_old' THEN REPLACE(c.code, '_', '.')
                                                              END
                                    ),
                                    '[]'::json
                                )
                            )
                            ORDER BY 
                                CASE 
                                    WHEN v.age_group = 'under_8_year_old' THEN 1
                                    WHEN v.age_group = 'over_8_year_old' THEN 2
                                    ELSE 3
                                END
                        )
                        FROM (
                            SELECT DISTINCT age_group
                            FROM question_answer_view
                        ) v
                    ),
                    '[]'::json
                )
            )
            ORDER BY c.code
        ) AS subtypes
    FROM disability_type c
    WHERE c.parent_code IS NOT NULL
    GROUP BY c.parent_code
)
SELECT
    dt.code AS disability_code,
    dt.title,
    dt.description,
    COALESCE(ch.subtypes, '[]'::json) AS subtypes
FROM disability_type dt
LEFT JOIN children ch
    ON ch.parent_code = dt.code
WHERE dt.parent_code IS NULL
ORDER BY CAST(SUBSTRING(dt.code FROM '[0-9]+') AS INT);
