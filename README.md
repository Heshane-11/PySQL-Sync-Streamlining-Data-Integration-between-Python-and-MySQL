# 🛒 Retailytics

**Retailytics** is a data analytics project that integrates **Python with MySQL** to analyze retail sales, customer behavior, and transaction patterns. It provides insightful SQL queries to extract meaningful data for business decision-making.

## ✨ Features

- 🏙️ **Customer Location Analysis**: Identifies unique cities where customers are located.
- 🛍️ **Order Statistics**: Counts the number of orders placed within a specific timeframe.
- 📊 **Category-wise Sales Analysis**: Computes total sales for each product category.
- 💳 **Payment Insights**: Calculates the percentage of orders paid in installments.
- 🔍 **Data Extraction using SQL Queries**: Efficient data retrieval from MySQL.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/retailytics.git
   cd retailytics
   ```

2. Install dependencies:
   ```bash
   pip install mysql-connector-python pandas
   ```

3. Set up the MySQL database:
   - Import the provided SQL schema.
   - Update database credentials in `config.py`.

## 🚀 Usage

1. **Open Jupyter Notebook:**
   ```bash
   jupyter notebook
   ```
2. **Run the Notebook:**
   - Open `python-mysql.ipynb`
   - Execute cells to run queries

## 📂 Project Structure

```
/retailytics
│── 📜 python-mysql.ipynb    # Jupyter notebook with queries and outputs
│── 💾 database.py           # MySQL integration
│── 📃 requirements.txt      # Dependencies
│── 📌 config.py             # Database credentials
```

## 🛠️ Technologies Used

- 🐍 **Python**
- 🗄️ **MySQL**
- 📊 **pandas**
- 🔍 **SQL Queries**
- 📓 **Jupyter Notebook**

## 📊 Project Outputs

The outputs of the project, including query results and analysis, are displayed within the **python-mysql.ipynb** file.

## 🤝 Contribution

Feel free to contribute by submitting pull requests or reporting issues.

---
