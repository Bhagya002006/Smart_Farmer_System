# Smart Farmer System

## About the Project

Smart Farmer System is a web-based application developed to help manage farming activities and connect farmers with consumers. It provides features for managing farmer details, land information, crops, orders, sales, and soil testing records.

## Technologies Used

- **Python** – Backend programming
- **Flask** – Web application framework
- **MySQL** – Database management
- **HTML** – Frontend structure
- **CSS** – Frontend styling

## Features

- **Farmer Management:** Register and manage farmer details.
- **Land Management:** Store farmer land information.
- **Crop Management:** Add and manage crop details, prices, quantities, and seasons.
- **Consumer Management:** Register and manage consumer details.
- **Farmer and Crop Listing:** View available crops and farmer information.
- **Order Management:** Place and manage crop orders.
- **Order Tracking:** View order information and status.
- **Price Comparison:** Compare prices of available crops.
- **Sales Management:** Record sales information.
- **Sales Analytics:** View sales summaries and crop-wise sales information.
- **Soil Testing Records:** Store and view soil pH test records.
- **Farmer Reviews:** Submit and view reviews for farmers.
- **Dashboards:** Separate dashboards for farmers and consumers.

## Project Structure

```text
smart_farming_system/
│
├── .vscode/
├── models/
├── static/
│   ├── dashboard.css
│   └── style.css
│
├── templates/
│   ├── consumer.html
│   ├── consumer_dashboard.html
│   ├── crop.html
│   ├── farmer.html
│   ├── farmer_reviews.html
│   ├── farmers_crops.html
│   ├── farmers_dashboard.html
│   ├── index.html
│   ├── land.html
│   ├── order_tracking.html
│   ├── orders.html
│   ├── price_comparison.html
│   ├── reviews.html
│   ├── sales.html
│   ├── sales_analytics.html
│   ├── soil_test.html
│   └── view.html
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Execution

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Smart-Farmer-System.git
```

### 2. Open the Project Folder

```bash
cd Smart-Farmer-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure MySQL

Make sure MySQL Server is running and the required database is configured.

Database name used in the project:

```text
smart_farmer_system
```

Configure the database connection settings in `app.py` for your local environment.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## Project Purpose

The purpose of this project is to provide a simple platform for managing farming-related information, handling crop orders, maintaining sales records, and connecting farmers with consumers.

## Author

**Bhagyashree Jamadar**
