

CREATE OR REPLACE PROCEDURE public.finance_outflow_sp(
	)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
    -- Core joins of all necessary tables
    WITH joined_data AS (
        SELECT 
            txn.transaction_date,
            txn.qty AS quantity,
            txn."type",
            txn.amount AS transaction_amount,
            txn.transaction_cost,
            (txn.amount + txn.transaction_cost) AS total_cost,
            txn.payment_method,
            txn.description AS transaction_description,
            dept."name" AS department_name,
            cat.category_name,
            subcat.sub_category_name,
            loc.location_name
        FROM account_transactions_tbl txn
        LEFT JOIN account_department_tbl dept 
            ON txn.department_id = dept.department_id
        LEFT JOIN account_category_tbl cat 
            ON txn.category_id = cat.category_id
        LEFT JOIN account_subcategory_tbl subcat 
            ON txn.subcategory_id = subcat.sub_category_id
        LEFT JOIN accounts_location_tbl loc 
            ON txn.location_id = loc.location_id
    ),
    aggregated AS (
        SELECT 
            jd.*,
            SUM(jd.total_cost) OVER (PARTITION BY jd.department_name) AS cost_per_department_total,
            SUM(jd.total_cost) OVER (PARTITION BY jd.location_name)   AS cost_per_location_total,
            SUM(jd.total_cost) OVER (PARTITION BY jd.category_name)   AS cost_per_category_total,
            SUM(jd.total_cost) OVER (PARTITION BY jd.sub_category_name) AS cost_per_subcategory_total
        FROM joined_data jd
    )
    -- Final result set returned by the procedure
    SELECT * FROM aggregated;
END;
$BODY$;
ALTER PROCEDURE public.finance_outflow_sp()
    OWNER TO uf4o5nponalopo;