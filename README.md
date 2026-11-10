# Tourism-and-travel-management-system
This project optimizes tour and travel management by providing actionable insights for admins, planners, and customers. Using structured data and analytics, the system tracks schedules, customer interactions, and booking patterns. It identifies popularity trends to enable data-driven decisions and deliver seamless travel experiences. 
# ✈️ Tour & Travel Management System

An enterprise-grade, interactive CLI travel suite engineered with Python, Object-Oriented Architecture, Custom Data Structures, Pandas DataFrames, and Matplotlib Visual Analytics.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Pandas-Data%20Engine-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/Matplotlib-Data%20Viz-11557c?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Architecture-OOP%20%2B%20DSA-ff69b4?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Release-v1.0.0--stable-brightgreen?style=for-the-badge" />
</p>

---

## 📌 Project Introduction

The **Tour & Travel Management System (TTMS)** is a high-performance terminal application designed to streamline travel agency operations. By integrating relational CSV datasets with clean object-oriented software patterns and custom stack data structures, TTMS provides agency staff with real-time tour booking, customer profile tracking, and automated analytical reporting without full web-stack overhead.

> [!NOTE]
> Designed for lightweight execution, TTMS runs efficiently in local command lines or cloud notebook environments like Google Colab.

---

## 🎯 Project Goal

- **Automate Core Workflows:** Modernize tour schedule creation, price updating, and customer record management.
- **Fail-Safe CLI Navigation:** Eliminate runtime crashes from bad user inputs using custom flow-control exception handling.
- **Visual Analytics Engine:** Enable data-driven business decisions by automatically plotting popularity trends and budget distribution curves.
- **Maintainable Architecture:** Modularize code using OOP inheritance and dynamic controller routing maps for frictionless future expansion.

---

## 📊 Data Collection

The core system reads and persists real-time transactional records across four relational CSV files:

| File Name | Primary Key | Description & Core Attributes |
| :--- | :---: | :--- |
| `TOUR.csv` | `Tour_ID` | Master catalog storing tour names, destinations, price segments, and dates. |
| `CUSTOMERS.csv` | `Customer_ID` | Customer database tracking profiles, phone records, address, and email details. |
| `BOOKING.csv` | `Booking_ID` | Mapping table storing active customer reservations linked to tour packages. |
| `GUIDE.csv` | `Guide_ID` | Staff assignment logs detailing active tour guides and operational scheduling. |

---

## 🧠 Methodology

TTMS utilizes a modular tier architecture balancing robust Object-Oriented principles with custom Data Structures & Algorithms (DSA):

```text
Tour Travel Management System
 ┣ 📂 Data Layer
 ┃ ┗ DatabaseManager (Pandas Read/Write Engine & ID Generator)
 ┣ 📂 DSA Navigation Stack
 ┃ ┗ SessionHistory (LIFO Stack tracking menu state frames)
 ┣ 📂 Control Tier
 ┃ ┣ PromptValidator (Input verification & NavigationBackException trigger)
 ┃ ┣ MenuController (Base Class with dynamic dispatch mapping)
 ┃ ┣ TourOperations (Concrete Controller for tours & Matplotlib analytics)
 ┃ ┗ CustomerOperations (Concrete Controller for profiles & booking histograms)
 ┗ 📂 Runtime
   ┗ AppEngine (Central runtime dispatcher)
> [!IMPORTANT]
> Typing `back` at any prompt safely triggers the custom `NavigationBackException`, unwinding the LIFO session stack without corrupting data or throwing tracebacks.

---

## 💻 System Requirements

### Hardware & Environment
- **OS:** Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+)
- **RAM:** 2 GB Minimum (4 GB Recommended)
- **Disk Space:** 50 MB Free Space

### Software & Python Dependencies
```bash
# Python Runtime
Python 3.8 or higher

# Required Libraries
pandas >= 1.3.0
numpy >= 1.21.0
matplotlib >= 3.4.0

# Install dependencies
pip install pandas numpy matplotlib

# Run application
python main.py

## 🔮 Future Upgrade

- [ ] **SQL Relational Database Integration:** Upgrade CSV file backends to PostgreSQL or SQLite for ACID-compliant transactions.
- [ ] **Graphical User Interface (GUI):** Transition terminal prompts into a modern PySide6 or PyQt desktop dashboard.
- [ ] **Automated PDF Invoicing:** Auto-generate downloadable customer booking receipts and financial summaries.
- [ ] **Role-Based Access Control (RBAC):** Separate Admin privileges (adding/removing tours) from standard customer access.

---

## 🔭 Scope

- **Primary Scope:** Internal desktop application for small-to-medium travel agencies and desk agents requiring quick catalog updates and booking metrics.
- **Out of Scope:** Online public web booking portals, payment gateway integrations (Stripe/PayPal), or live third-party flight API synchronizations.

---

## 💡 Conclusion

The **Tour & Travel Management System** demonstrates how fundamental Computer Science concepts—such as Object-Oriented Design, custom exception stack management, and DataFrame manipulations—can transform a command-line interface into an enterprise tool. By coupling structured data validation with immediate visual reporting, TTMS provides an all-in-one software solution that is both maintainable for developers and seamless for operators.


