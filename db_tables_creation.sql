-- Users table
CREATE TABLE dm_user_tbl (
	user_id SERIAL PRIMARY KEY,  
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL,
	gender VARCHAR(10) CHECK (gender IN ('Male', 'Female')) NOT NULL, 
	user_category VARCHAR(20) CHECK (user_category IN ('employee', 'applicant', 'client', 'other')) NOT NULL  
);



-- cash outflow table
CREATE TABLE fact_cashoutflow_tbl (
	transaction_id SERIAL PRIMARY KEY, 
	sender_id INT NOT NULL,            
	receiver_id INT NOT NULL,           
	transaction_date DATE NOT NULL, 
	qty INT NOT NULL,                
	amount DECIMAL(15, 2) NOT NULL,    
	transaction_cost DECIMAL(15, 2) NOT NULL, 
	department_id INT NOT NULL,         
	location_id INT NOT NULL,           
	FOREIGN KEY (sender_id) REFERENCES dm_user_tbl (user_id),  
	FOREIGN KEY (receiver_id) REFERENCES dm_user_tbl (user_id),  
	FOREIGN KEY (department_id) REFERENCES dm_department_tbl (department_id), 
	FOREIGN KEY (location_id) REFERENCES dm_location_tbl (location_id) 



-- Departments table
CREATE TABLE dm_department_tbl(
	department_id SERIAL PRIMARY KEY,
	department_name VARCHAR (200)
);



-- Location table
CREATE TABLE dm_location_tbl (
	location_id SERIAL PRIMARY KEY,  
	location_name VARCHAR(100) NOT NULL
);



-- Cash inflow table
CREATE TABLE fact_cashinflow_tbl (
	payment_id SERIAL PRIMARY KEY,  
	payment_fees DECIMAL(15, 2) NOT NULL,
	down_payment DECIMAL(15, 2) NOT NULL,
	fee_balance DECIMAL(15, 2) NOT NULL,
	user_id INT NOT NULL,
	rep_date DATE NOT NULL,
	contract_date DATE NOT NULL,
	FOREIGN KEY (user_id) REFERENCES dm_user_tbl (user_id)
);


-- Category table
CREATE TABLE dim_category_tbl (
	category_id SERIAL PRIMARY KEY,  
	category_name VARCHAR(100) NOT NULL, 
	department_id INT NOT NULL,  
	FOREIGN KEY (department_id) REFERENCES dm_department_tbl (department_id)
);


-- Subcategory table
CREATE TABLE dm_sub_category_tbl (
	sub_category_id SERIAL PRIMARY KEY,
	sub_category_name VARCHAR(100) NOT NULL,
	category_id INT NOT NULL,
	FOREIGN KEY (category_id) REFERENCES dm_category_tbl (category_id)
);



