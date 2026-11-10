import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 0. CUSTOM FLOW-CONTROL EXCEPTIONS
# =====================================================================
class NavigationBackException(Exception):
    # Raised when the user requests to go 'back' during interactive prompts.
    pass

# =====================================================================
# 1. DATA STACK (DSA) - SESSION HISTORY
# =====================================================================
class SessionHistory:
    # A simple LIFO stack to track navigation history.
    def __init__(self):
        self._stack = []

    def push(self, menu_state):
        self._stack.append(menu_state)

    def pop(self):
        if not self.is_empty():
            return self._stack.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self._stack[-1]
        return None

    def is_empty(self):
        return len(self._stack) == 0

# =====================================================================
# 2. BASE ENTITY CLASSES (OOP)
# =====================================================================
class DatabaseManager:
    # Handles database reads, writes, and auto-increment operations.
    def __init__(self):
        self.tours = pd.read_csv("/content/TOUR.csv", index_col='Tour_ID', dtype=str).fillna('')
        self.customers = pd.read_csv("/content/CUSTOMERS.csv", index_col='Customer_ID', dtype=str).fillna('')
        self.bookings = pd.read_csv("/content/BOOKING.csv", index_col='Booking_ID', dtype=str).fillna('')
        self.guides = pd.read_csv("/content/GUIDE.csv", index_col='Guide_ID', dtype=str).fillna('')

    def save(self, df, filename):
        df.to_csv(filename)

    def generate_new_id(self, df, prefix):
        if df.empty:
            return prefix + "1"
        last_id = df.index[-1]
        new_id_num = int(last_id[1:]) + 1
        return prefix + str(new_id_num)

db = DatabaseManager()

# =====================================================================
# 3. INTERACTIVE VALIDATION ENGINE
# =====================================================================
class PromptValidator:
    # Central utility for gathering and validating safe command-line inputs.
    @staticmethod
    def get_input(prompt, validation_func=None, error_msg="Invalid entry.", max_attempts=5):
        attempts = 0
        while True:
            user_input = input(f"{prompt} (or 'back'): ").strip()
            if user_input.lower() == 'back':
                raise NavigationBackException()

            if validation_func is None or validation_func(user_input):
                return user_input

            attempts += 1
            if attempts >= max_attempts:
                print("\nToo many invalid attempts. Transaction aborted.")
                raise NavigationBackException()
            print(error_msg)

# =====================================================================
# 4. OOP CONTROLLER SYSTEM (Standard Class without ABC)
# =====================================================================
class MenuController:
    # Standard base class representing a menu controller.
    def __init__(self, title):
        self.title = title
        self.dispatch_map = {}

    def show_menu(self):
        # To be overridden by subclasses
        pass

    def execute(self):
        while True:
            self.show_menu()
            options = list(self.dispatch_map.keys()) + ['4']
            try:
                choice = PromptValidator.get_input("Enter choice", lambda x: x in options, "Invalid choice selection.")
                if choice == '4':
                    break

                # Dispatch dynamically via the mapped routing dictionary
                action = self.dispatch_map.get(choice)
                if action:
                    action()
            except NavigationBackException:
                # Catch back signals globally for the sub-actions
                print("\nReturning to previous menu...")
                # If the exception happened at the main controller selection itself, exit loop
                break

# =====================================================================
# 5. CONCRETE CONTROLLER: TOUR OPERATIONS
# =====================================================================
class TourOperations(MenuController):
    def __init__(self):
        super().__init__("Tour Management Module")
        self.dispatch_map = {
            '0': self.add_tour,
            '1': self.modify_tour,
            '2': self.remove_tour,
            '3': self.review_tour,
            '5': self.show_top_popular,
            '6': self.show_least_popular,
            '7': self.check_availability,
            '8': self.check_budget,
            '9': self.contract_info
        }

    def show_menu(self):
        print("""+----------------------------------------+
| OPT(S) | TOUR OPERATIONS               |
+----------------------------------------+
| 0      | ADD A NEW TOUR                |
| 1      | MODIFY EXISTING TOUR          |
| 2      | REMOVE TOUR                   |
| 3      | REVIEW TOUR INFORMATION       |
| 4      | RETURN TO MAIN MENU           |
| 5      | TOP POPULAR TOURS             |
| 6      | LEAST POPULAR TOURS           |
| 7      | AVAILABILITY                  |
| 8      | BUDGETING                     |
| 9      | CONTRACTS INFORMATION         |
+----------------------------------------+""")

    def add_tour(self):
        name = PromptValidator.get_input("Enter Tour Name")
        dest = PromptValidator.get_input("Enter Tour Destination")
        price = PromptValidator.get_input("Enter Tour Price", lambda x: x.isdigit(), "Price must be an integer.")
        start = PromptValidator.get_input("Enter Start Date (YYYY-MM-DD)")
        end = PromptValidator.get_input("Enter End Date (YYYY-MM-DD)")

        tour_id = db.generate_new_id(db.tours, "T")
        db.tours.loc[tour_id] = [name, dest, price, start, end]
        db.save(db.tours, "Tours.csv")
        print(f"\nTour Registered Successfully! ID: {tour_id}")
        print(db.tours.loc[tour_id])
        input("\nPress Enter to continue...")

    def modify_tour(self):
        tour_id = PromptValidator.get_input("Enter Tour ID", lambda x: x in db.tours.index, "ID not found.")
        print("\nCurrent configuration:\n", db.tours.loc[tour_id])

        new_name = PromptValidator.get_input("New Name (skip to keep current)")
        new_dest = PromptValidator.get_input("New Destination (skip to keep current)")
        new_price = PromptValidator.get_input("New Price (skip to keep current)", lambda x: x == '' or x.isdigit(), "Must be digits.")
        new_start = PromptValidator.get_input("New Start Date (skip to keep current)")
        new_end = PromptValidator.get_input("New End Date (skip to keep current)")

        if new_name: db.tours.at[tour_id, 'Tour_Name'] = new_name
        if new_dest: db.tours.at[tour_id, 'Tour_Destination'] = new_dest
        if new_price: db.tours.at[tour_id, 'Tour_Price'] = new_price
        if new_start: db.tours.at[tour_id, 'Start_Date'] = new_start
        if new_end: db.tours.at[tour_id, 'End_Date'] = new_end
        db.save(db.tours, "Tours.csv")
        print("\nTour package updated.")
        input("\nPress Enter to continue...")

    def remove_tour(self):
        tour_id = PromptValidator.get_input("Enter Tour ID to Remove", lambda x: x in db.tours.index, "ID does not exist.")
        print(db.tours.loc[tour_id])

        confirm = PromptValidator.get_input("Proceed with removal? (Y/N)", lambda x: x.upper() in ['Y','N'])
        if confirm.upper() == 'Y':
            db.tours.drop(tour_id, inplace=True)
            db.save(db.tours, "Tours.csv")
            print("Tour successfully purged.")
        else:
            print("Aborted.")
        input("\nPress Enter to continue...")

    def review_tour(self):
        tour_id = PromptValidator.get_input("Enter Tour ID", lambda x: x in db.tours.index, "Invalid Tour ID.")
        print(db.tours.loc[tour_id])
        input("\nPress Enter to continue...")

    def show_top_popular(self):
        if not db.bookings.empty:
            top_ids = db.bookings['Tour_ID'].value_counts().nlargest(3).index
            top_tours = db.tours.loc[top_ids].copy()
            top_tours['Number_of_Bookings'] = db.bookings['Tour_ID'].value_counts().nlargest(3).values
            print("\nTop 3 Popular Packages:\n", top_tours)

            plt.figure(figsize=(7,4))
            plt.bar(top_tours['Tour_Name'], top_tours['Number_of_Bookings'], color='skyblue')
            plt.title("Top 3 Booked Tours")
            plt.ylabel("Bookings Count")
            plt.show()
        else:
            print("Insufficient booking data.")
        input("\nPress Enter to continue...")

    def show_least_popular(self):
        if db.bookings.empty or db.tours.empty:
            print("Data pool unavailable.")
        else:
            least_id = db.bookings['Tour_ID'].value_counts().idxmin()
            if least_id in db.tours.index:
                print("Least Demanded Tour:\n", db.tours.loc[least_id])
                least_pop = db.tours.loc[least_id]
                plt.figure(figsize=(5,3.5))
                plt.bar(least_pop['Tour_Name'], db.bookings['Tour_ID'].value_counts().min(), color='salmon')
                plt.title("Least Popular Record")
                plt.show()
        input("\nPress Enter to continue...")

    def check_availability(self):
        dest = PromptValidator.get_input("Enter target destination")
        matches = db.tours[db.tours['Tour_Destination'].str.lower() == dest.lower()]
        if matches.empty:
            print("No open schedules to that destination.")
        else:
            print("Available Runs:\n", matches)
            plt.figure(figsize=(7,4))
            plt.bar(matches['Tour_Name'], matches['Tour_Price'].astype(int), color='lightgreen')
            plt.ylabel("Cost (USD)")
            plt.title(f"Active Departures: {dest}")
            plt.show()
        input("\nPress Enter to continue...")

    def check_budget(self):
        budget_val = PromptValidator.get_input("Enter upper budget limit", lambda x: x.replace('.','',1).isdigit(), "Invalid number.")
        limit = float(budget_val)
        matches = db.tours[db.tours['Tour_Price'].astype(int) <= limit]
        if matches.empty:
            print("No adventures match your price segment.")
        else:
            print(matches)
            plt.figure(figsize=(7,4))
            plt.bar(matches['Tour_Name'], matches['Tour_Price'].astype(int), color='violet')
            plt.title(f"Schedules Under ${limit}")
            plt.show()
        input("\nPress Enter to continue...")

    def contract_info(self):
        print("\nExternal contracts active: [Supplier Node Placeholder]")
        input("\nPress Enter to continue...")

# =====================================================================
# 6. CONCRETE CONTROLLER: CUSTOMER OPERATIONS
# =====================================================================
class CustomerOperations(MenuController):
    def __init__(self):
        super().__init__("Customer Operations Module")
        self.dispatch_map = {
            '0': self.add_customer,
            '1': self.modify_customer,
            '2': self.remove_customer,
            '3': self.view_profile
        }

    def show_menu(self):
        print("""
+----------------------------------------+
| CUSTOMER OPERATIONS                    |
+----------------------------------------+
| 0      | ADD A NEW CUSTOMER            |
| 1      | MODIFY CUSTOMER INFORMATION   |
| 2      | REMOVE A CUSTOMER             |
| 3      | VIEW CUSTOMER INFORMATION     |
| 4      | RETURN TO MAIN MENU           |
+----------------------------------------+""")

    def add_customer(self):
        name = PromptValidator.get_input("Enter Full Name")
        addr = PromptValidator.get_input("Enter Address")
        phone = PromptValidator.get_input("Enter Contact Phone")
        email = PromptValidator.get_input("Enter Email ID")

        cid = db.generate_new_id(db.customers, "C")
        db.customers.loc[cid] = [name, addr, phone, email]
        db.save(db.customers, "Customers.csv")
        print(f"\nSuccess! Customer account created. ID: {cid}")
        input("\nPress Enter to continue...")

    def modify_customer(self):
        cid = PromptValidator.get_input("Enter Customer ID", lambda x: x in db.customers.index, "No customer profile matched.")
        print(db.customers.loc[cid])

        new_name = PromptValidator.get_input("Update Name (blank to keep)")
        new_addr = PromptValidator.get_input("Update Address (blank to keep)")
        new_phone = PromptValidator.get_input("Update Phone (blank to keep)")
        new_email = PromptValidator.get_input("Update Email (blank to keep)")

        if new_name: db.customers.at[cid, 'Customer_Name'] = new_name
        if new_addr: db.customers.at[cid, 'Customer_Address'] = new_addr
        if new_phone: db.customers.at[cid, 'Customer_Phone'] = new_phone
        if new_email: db.customers.at[cid, 'Customer_Email'] = new_email
        db.save(db.customers, "Customers.csv")
        print("\nCustomer record modified.")
        input("\nPress Enter to continue...")

    def remove_customer(self):
        cid = PromptValidator.get_input("Enter Customer ID for deletion", lambda x: x in db.customers.index, "ID not found.")
        print(db.customers.loc[cid])

        confirm = PromptValidator.get_input("Confirm profile termination? (Y/N)", lambda x: x.upper() in ['Y','N'])
        if confirm.upper() == 'Y':
            db.customers.drop(cid, inplace=True)
            db.save(db.customers, "Customers.csv")
            print("Profile successfully removed.")
        else:
            print("Cancelled.")
        input("\nPress Enter to continue...")

    def view_profile(self):
        cid = PromptValidator.get_input("Enter Customer ID", lambda x: x in db.customers.index, "No customer profile matched.")
        print(db.customers.loc[cid])

        profile_bookings = db.bookings[db.bookings['Customer_ID'] == cid]
        if profile_bookings.empty:
            print("No prior booking logs found.")
        else:
            print("\nActive Bookings:\n", profile_bookings)
            val_counts = profile_bookings['Tour_ID'].value_counts()
            names = db.tours.loc[val_counts.index]['Tour_Name']

            plt.figure(figsize=(7,4))
            plt.bar(names, val_counts.values, color='orange')
            plt.title(f"Booking History metrics - ID {cid}")
            plt.ylabel("Frequency")
            plt.show()
        input("\nPress Enter to continue...")

# =====================================================================
# 7. CENTRAL APP RUNTIME (DSA STATE CONTROLLER)
# =====================================================================
class AppEngine:
    def __init__(self):
        self.history = SessionHistory()
        # Instantiate our OOP Controller components
        self.modules = {
            '1': TourOperations(),
            '2': CustomerOperations()
        }

    def start(self):
        while True:
            print("""
+----------------------------------------+
| OPT(S) | OPERATIONS                    |
+----------------------------------------+
| 0      | INTRODUCTION TO PROJECT        |
| 1      | TOUR OPERATIONS               |
| 2      | CUSTOMER OPERATIONS           |
| 4      | EXIT                          |
+----------------------------------------+""")
            try:
                choice = PromptValidator.get_input("Enter your choice", lambda x: x in ['0','1','2','4'])
                if choice == '4':
                    print("Exiting application database. Goodbye!")
                    break

                if choice == '0':
                    print("\nWelcome to the Tour and Travel Management System – your gateway to seamless travel!\n")
                    input("\nPress Enter to continue...")
                else:
                    module = self.modules.get(choice)
                    if module:
                        # Keep trace of state in our DSA Stack
                        self.history.push(module)
                        module.execute()
                        self.history.pop()  # Pop frame when user exits to return cleanly
            except NavigationBackException:
                print("\nReturned to Main Console.")

if __name__ == "__main__":
    engine = AppEngine()
    engine.start()
