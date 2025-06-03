CREATE VIEW finance_outflow AS

	WITH join_tables AS (
		SELECT
			*,
			txn.description AS description_txn
		FROM account_cleaned_transactions_table AS txn
		-- Horizontally combine Departments table
		LEFT JOIN account_cleaned_department_table AS department 
		ON txn.department_id = department.department_id
		-- Horizontally combine Category table
		LEFT JOIN account_cleaned_category_table AS category
		ON txn.category_id = category.category_id
		-- Horizontally combine Sub-category table
		LEFT JOIN account_cleaned_subcategory_table AS subcategory
		ON category.category_id = subcategory.sub_category_id
		-- Horizontally combine Locations table
		LEFT JOIN accounts_cleaned_location AS loc
		ON txn.location_id = loc.location_id
	),
	important_columns AS (
		SELECT
			transaction_date,
			amount as transaction_amount,
			transaction_cost,
			amount + transaction_cost AS all_cost,
			"type",
			qty as quantity,
			payment_method,
			description_txn,
			sender_id,
			"name" AS department_name,
			category_name,
			sub_category_name,
			location_name
		FROM join_tables
	)
	SELECT
		*,
		-- Total cost per department
		SUM(all_cost) OVER(PARTITION BY department_name) cost_per_department_total,
	    -- Total cost per office location
		SUM(all_cost) OVER(PARTITION BY location_name) cost_per_locatn_total,
		-- Total cost per category
		SUM(all_cost) OVER(PARTITION BY category_name) category_cost_total,
		-- Total cost per sub_category
		SUM(all_cost) OVER(PARTITION BY sub_category_name) sub_category_cost_total
	FROM important_columns
