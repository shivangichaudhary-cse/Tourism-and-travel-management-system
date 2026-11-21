# =====================================================================
# TOUR AND TRAVEL MANAGEMENT SYSTEM
# SECTION 1: FOUNDATION AND DATA MANAGEMENT
# =====================================================================

from datetime import datetime
import math
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# =====================================================================
# 0. CONFIGURATION
# =====================================================================

# __file__ is available when run/imported as a Python file, but not when
# pasted into a notebook cell. In notebooks, data files are expected in
# the current working directory (for example, Colab's /content folder).
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

FILES = {
    "tours": BASE_DIR / "TOUR.csv",
    "customers": BASE_DIR / "CUSTOMERS.csv",
    "bookings": BASE_DIR / "BOOKING.csv",
    "guides": BASE_DIR / "GUIDE.csv",
}

# These are the supplied CSV schemas and their original column order.
EXPECTED_COLUMNS = {
    "tours": [
        "Tour_Name", "Tour_Destination", "Tour_Price",
        "Start_Date", "End_Date",
    ],
    "customers": [
        "Customer_Name", "Customer_Address",
        "Customer_Phone", "Customer_Email",
    ],
    "bookings": ["Customer_ID", "Tour_ID", "Booking_Date"],
    "guides": ["Guide_Name", "Contact", "Tour_ID"],
}

ID_PREFIXES = {
    "tours": "T",
    "customers": "C",
    "bookings": "B",
    "guides": "G",
}

ID_COLUMNS = {
    "tours": "Tour_ID",
    "customers": "Customer_ID",
    "bookings": "Booking_ID",
    "guides": "Guide_ID",
}


# =====================================================================
# 1. CUSTOM EXCEPTIONS
# =====================================================================

class NavigationBackException(Exception):
    """Raised when the user requests to return to the previous menu."""


class DataValidationException(Exception):
    """Raised when a data operation fails validation."""


# =====================================================================
# 2. SESSION HISTORY STACK (LIFO)
# =====================================================================

class SessionHistory:
    def __init__(self):
        self._stack = []

    def push(self, menu_state):
        self._stack.append(menu_state)

    def pop(self):
        return self._stack.pop() if self._stack else None

    def peek(self):
        return self._stack[-1] if self._stack else None

    def is_empty(self):
        return not self._stack


# =====================================================================
# 3. DATABASE MANAGER
# =====================================================================

class DatabaseManager:
    def __init__(self, data_dir=None):
        # Optional data_dir makes the same manager usable with a notebook's
        # working directory and with isolated temporary datasets in tests.
        self.files = {
            name: Path(data_dir) / path.name if data_dir is not None else path
            for name, path in FILES.items()
        }
        for table_name in ID_COLUMNS:
            setattr(self, table_name, self._load(table_name))

    def _load(self, table_name):
        path = self.files[table_name]
        id_column = ID_COLUMNS[table_name]
        expected = [id_column] + EXPECTED_COLUMNS[table_name]

        if not path.exists():
            raise FileNotFoundError(f"Required dataset not found: {path}")

        try:
            # A zero-byte file represents an empty table; it will be written
            # with the correct header the next time it is saved.
            if path.stat().st_size == 0:
                df = pd.DataFrame(columns=expected)
            else:
                df = pd.read_csv(path, dtype=str, keep_default_na=False)
        except (OSError, pd.errors.ParserError, UnicodeError) as error:
            raise DataValidationException(
                f"Could not read {path.name}: {error}"
            ) from error
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=expected)

        missing = [column for column in expected if column not in df.columns]
        unexpected = [column for column in df.columns if column not in expected]
        if missing or unexpected:
            details = []
            if missing:
                details.append(f"missing columns: {missing}")
            if unexpected:
                details.append(f"unexpected columns: {unexpected}")
            raise DataValidationException(
                f"Invalid schema in {path.name} ({'; '.join(details)}). "
                f"Expected columns: {expected}"
            )

        # Normalize column order to the supplied schema without changing any
        # stored field names or values.
        df = df[expected]
        if df[id_column].eq("").any():
            raise DataValidationException(
                f"Blank IDs found in {path.name}."
            )
        if df[id_column].duplicated().any():
            raise DataValidationException(
                f"Duplicate IDs found in {path.name}."
            )
        return df.set_index(id_column)

    def save(self, table_name, df=None):
        """Persist a table using a temporary file to avoid partial CSV writes."""
        if table_name not in ID_COLUMNS:
            raise DataValidationException(f"Unknown table: {table_name}")
        df = getattr(self, table_name) if df is None else df
        expected = EXPECTED_COLUMNS[table_name]
        if list(df.columns) != expected:
            raise DataValidationException(
                f"Invalid in-memory schema for {table_name}: "
                f"expected {expected}, found {list(df.columns)}"
            )

        path = self.files[table_name]
        temp_path = path.with_name(path.name + ".tmp")
        try:
            df.to_csv(temp_path, index_label=ID_COLUMNS[table_name])
            os.replace(temp_path, path)
        except (OSError, ValueError) as error:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise DataValidationException(
                f"Could not save {path.name}: {error}"
            ) from error

    def generate_new_id(self, table_name):
        if table_name not in ID_COLUMNS:
            raise DataValidationException(f"Unknown table: {table_name}")
        prefix = ID_PREFIXES[table_name]
        numbers = []
        for record_id in getattr(self, table_name).index:
            value = str(record_id)
            if value.startswith(prefix):
                suffix = value[len(prefix):]
                if suffix.isdigit():
                    numbers.append(int(suffix))
        # Use the largest existing numeric suffix, not row order or row count.
        return f"{prefix}{max(numbers, default=0) + 1}"

    def add_record(self, table_name, values):
        if table_name not in ID_COLUMNS:
            raise DataValidationException(f"Unknown table: {table_name}")
        values = list(values)
        if len(values) != len(EXPECTED_COLUMNS[table_name]):
            raise DataValidationException("Incorrect number of record fields.")
        if any(not isinstance(value, str) for value in values):
            raise DataValidationException("Record fields must be strings.")
        df = getattr(self, table_name).copy()
        record_id = self.generate_new_id(table_name)
        if record_id in df.index:
            raise DataValidationException(f"Generated duplicate ID: {record_id}")
        df.loc[record_id] = values
        self.save(table_name, df)
        setattr(self, table_name, df)
        return record_id

    def update_record(self, table_name, record_id, values):
        df = getattr(self, table_name)
        if record_id not in df.index:
            raise DataValidationException("Record does not exist.")
        values = values.reindex(EXPECTED_COLUMNS[table_name])
        updated = df.copy()
        updated.loc[record_id] = values
        self.save(table_name, updated)
        setattr(self, table_name, updated)

    def delete_record(self, table_name, record_id):
        if table_name not in ID_COLUMNS:
            raise DataValidationException(f"Unknown table: {table_name}")
        df = getattr(self, table_name)
        if record_id not in df.index:
            raise DataValidationException("Record does not exist.")

        # Enforce relationship protection at the data layer as well as in the
        # menus, so another caller cannot accidentally create orphan records.
        if table_name == "customers" and (
            self.bookings["Customer_ID"] == record_id
        ).any():
            raise DataValidationException(
                "Cannot delete a customer with associated bookings."
            )
        if table_name == "tours":
            if (self.bookings["Tour_ID"] == record_id).any():
                raise DataValidationException(
                    "Cannot delete a tour with associated bookings."
                )
            if (self.guides["Tour_ID"] == record_id).any():
                raise DataValidationException(
                    "Cannot delete a tour assigned to a guide."
                )

        updated = df.drop(index=record_id)
        self.save(table_name, updated)
        setattr(self, table_name, updated)


# =====================================================================
# 4. INPUT VALIDATION ENGINE
# =====================================================================

class PromptValidator:
    @staticmethod
    def get_input(prompt, validation_func=None,
                  error_msg="Invalid entry.", max_attempts=5):
        attempts = 0
        while True:
            value = input(f"{prompt} (or 'back'): ").strip()
            if value.lower() == "back":
                raise NavigationBackException()
            if validation_func is None or validation_func(value):
                return value
            attempts += 1
            print(error_msg)
            if attempts >= max_attempts:
                print("\nToo many invalid attempts. Returning to previous menu.")
                raise NavigationBackException()

    @staticmethod
    def pause():
        value = input("\nPress Enter to continue (or type 'back'): ").strip()
        if value.lower() == "back":
            raise NavigationBackException()

    @staticmethod
    def valid_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime(
                "%Y-%m-%d"
            ) == value
        except (TypeError, ValueError):
            return False

    @staticmethod
    def valid_price(value):
        try:
            number = float(value)
            return math.isfinite(number) and number >= 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def valid_email(value):
        return (
            isinstance(value, str)
            and "@" in value
            and "." in value.rsplit("@", 1)[-1]
            and not any(character.isspace() for character in value)
        )

    @staticmethod
    def valid_date_range(start, end):
        if not PromptValidator.valid_date(start) or not PromptValidator.valid_date(end):
            return False
        return datetime.strptime(end, "%Y-%m-%d") >= datetime.strptime(
            start, "%Y-%m-%d"
        )


# =====================================================================
# 5. BASE MENU CONTROLLER
# =====================================================================

class MenuController:
    def __init__(self, title):
        self.title = title
        self.dispatch_map = {}

    def show_menu(self):
        raise NotImplementedError("Subclasses must implement show_menu().")

    def execute(self):
        while True:
            self.show_menu()
            options = list(self.dispatch_map) + ["4"]
            try:
                choice = PromptValidator.get_input(
                    "Enter choice", lambda value: value in options,
                    "Invalid menu selection."
                )
                if choice == "4":
                    break
                action = self.dispatch_map.get(choice)
                if action:
                    action()
            except NavigationBackException:
                print("\nReturning to previous menu...")
                break


# =====================================================================
# 6. TOUR OPERATIONS
# =====================================================================

class TourOperations(MenuController):
    def __init__(self, db):
        super().__init__("Tour Management")
        self.db = db
        self.dispatch_map = {
            "0": self.add_tour, "1": self.modify_tour,
            "2": self.remove_tour, "3": self.review_tour,
            "5": self.show_top_popular, "6": self.show_least_popular,
            "7": self.check_availability, "8": self.check_budget,
            "9": self.contract_info,
        }

    def show_menu(self):
        print("""
+----------------------------------------+
|              TOUR OPERATIONS           |
+----------------------------------------+
| 0 | ADD TOUR                            |
| 1 | MODIFY TOUR                         |
| 2 | REMOVE TOUR                         |
| 3 | REVIEW TOUR                          |
| 4 | RETURN TO MAIN MENU                  |
| 5 | TOP POPULAR TOURS                    |
| 6 | LEAST POPULAR TOURS                  |
| 7 | CHECK AVAILABILITY                   |
| 8 | CHECK BUDGET                         |
| 9 | CONTRACT INFORMATION                 |
+----------------------------------------+
""")

    def add_tour(self):
        name = PromptValidator.get_input("Tour name")
        destination = PromptValidator.get_input("Tour destination")
        price = PromptValidator.get_input(
            "Tour price", PromptValidator.valid_price,
            "Enter a valid non-negative price."
        )
        start = PromptValidator.get_input(
            "Start date (YYYY-MM-DD)", PromptValidator.valid_date,
            "Invalid date format."
        )
        end = PromptValidator.get_input(
            "End date (YYYY-MM-DD)", PromptValidator.valid_date,
            "Invalid date format."
        )
        if not PromptValidator.valid_date_range(start, end):
            print("End date cannot be earlier than start date.")
            return
        tour_id = self.db.add_record(
            "tours", [name, destination, price, start, end]
        )
        print(f"\nTour successfully registered! ID: {tour_id}")
        PromptValidator.pause()

    def modify_tour(self):
        tour_id = PromptValidator.get_input(
            "Enter Tour ID", lambda value: value in self.db.tours.index,
            "Tour not found."
        )
        print("\nCurrent configuration:\n", self.db.tours.loc[tour_id])
        fields = {
            "Tour_Name": "New name", "Tour_Destination": "New destination",
            "Tour_Price": "New price", "Start_Date": "New start date",
            "End_Date": "New end date",
        }
        updated = self.db.tours.loc[tour_id].copy()
        for column, prompt in fields.items():
            value = PromptValidator.get_input(f"{prompt} (blank to keep current)")
            if value:
                updated[column] = value
        if not PromptValidator.valid_price(updated["Tour_Price"]):
            print("Invalid price. No changes saved.")
            return
        if not PromptValidator.valid_date_range(
            updated["Start_Date"], updated["End_Date"]
        ):
            print("Invalid dates or date range. No changes saved.")
            return
        self.db.update_record("tours", tour_id, updated)
        print("\nTour updated successfully.")
        PromptValidator.pause()

    def remove_tour(self):
        tour_id = PromptValidator.get_input(
            "Enter Tour ID", lambda value: value in self.db.tours.index,
            "Tour not found."
        )
        linked_bookings = self.db.bookings[
            self.db.bookings["Tour_ID"] == tour_id
        ]
        linked_guides = self.db.guides[self.db.guides["Tour_ID"] == tour_id]
        if not linked_bookings.empty:
            print("Cannot delete this tour. Existing bookings are associated with it.")
            PromptValidator.pause()
            return
        if not linked_guides.empty:
            print("Cannot delete this tour. A guide is currently assigned to it.")
            PromptValidator.pause()
            return
        print(self.db.tours.loc[tour_id])
        confirm = PromptValidator.get_input(
            "Confirm deletion (Y/N)", lambda value: value.upper() in ["Y", "N"]
        )
        if confirm.upper() == "Y":
            self.db.delete_record("tours", tour_id)
            print("Tour deleted successfully.")
        else:
            print("Deletion cancelled.")
        PromptValidator.pause()

    def review_tour(self):
        tour_id = PromptValidator.get_input(
            "Enter Tour ID", lambda value: value in self.db.tours.index,
            "Tour not found."
        )
        print("\nTour information:\n")
        print(self.db.tours.loc[tour_id])
        PromptValidator.pause()

    def _booking_counts(self):
        valid = self.db.bookings[
            self.db.bookings["Tour_ID"].isin(self.db.tours.index)
        ]
        return valid["Tour_ID"].value_counts()

    def _show_popularity(self, most_popular):
        counts = self._booking_counts()
        if counts.empty:
            print("No valid booking data available.")
        else:
            # Preserve the original ranking population (booked tours only),
            # and the original single-result least-popular behaviour.
            selected = counts.nlargest(3) if most_popular else counts.nsmallest(1)
            result = self.db.tours.loc[selected.index].copy()
            result["Number_of_Bookings"] = selected
            heading = "Top 3 Popular Tours" if most_popular else "Least Popular Tour"
            print(f"\n{heading}:\n")
            print(result)
            plt.figure(figsize=(7, 4))
            plt.bar(result["Tour_Name"], result["Number_of_Bookings"])
            plt.title(
                "Top 3 Booked Tours" if most_popular
                else "Least Popular Booked Tour"
            )
            plt.ylabel("Booking Count")
            plt.xticks(rotation=30)
            plt.tight_layout()
            plt.show()
        PromptValidator.pause()

    def show_top_popular(self):
        self._show_popularity(most_popular=True)

    def show_least_popular(self):
        self._show_popularity(most_popular=False)

    def check_availability(self):
        destination = PromptValidator.get_input("Enter target destination")
        matches = self.db.tours[
            self.db.tours["Tour_Destination"].str.casefold()
            == destination.casefold()
        ]
        if matches.empty:
            print("No tours found for this destination.")
        else:
            print("\nAvailable Tours:\n")
            print(matches)
            prices = pd.to_numeric(matches["Tour_Price"], errors="coerce")
            plt.figure(figsize=(7, 4))
            plt.bar(matches["Tour_Name"], prices)
            plt.title(f"Tour Prices: {destination}")
            plt.ylabel("Price")
            plt.xticks(rotation=30)
            plt.tight_layout()
            plt.show()
        PromptValidator.pause()

    def check_budget(self):
        budget = PromptValidator.get_input(
            "Enter maximum budget", PromptValidator.valid_price,
            "Enter a valid non-negative amount."
        )
        prices = pd.to_numeric(self.db.tours["Tour_Price"], errors="coerce")
        matches = self.db.tours[prices <= float(budget)]
        if matches.empty:
            print("No tours match your budget.")
        else:
            print("\nTours within budget:\n")
            print(matches)
            plt.figure(figsize=(7, 4))
            plt.bar(matches["Tour_Name"], prices.loc[matches.index])
            plt.title(f"Tour Packages Under {budget}")
            plt.ylabel("Price")
            plt.xticks(rotation=30)
            plt.tight_layout()
            plt.show()
        PromptValidator.pause()

    def contract_info(self):
        # Placeholder: supplier contract management is not implemented.
        print("\nExternal supplier contract management is not implemented yet.")
        PromptValidator.pause()


# =====================================================================
# 7. CUSTOMER OPERATIONS
# =====================================================================

class CustomerOperations(MenuController):
    def __init__(self, db):
        super().__init__("Customer Management")
        self.db = db
        self.dispatch_map = {
            "0": self.add_customer, "1": self.modify_customer,
            "2": self.remove_customer, "3": self.view_profile,
        }

    def show_menu(self):
        print("""
+----------------------------------------+
|            CUSTOMER OPERATIONS          |
+----------------------------------------+
| 0 | ADD CUSTOMER                        |
| 1 | MODIFY CUSTOMER                     |
| 2 | REMOVE CUSTOMER                     |
| 3 | VIEW CUSTOMER PROFILE               |
| 4 | RETURN TO MAIN MENU                  |
+----------------------------------------+
""")

    def add_customer(self):
        name = PromptValidator.get_input("Enter full name")
        address = PromptValidator.get_input("Enter address")
        phone = PromptValidator.get_input("Enter contact phone")
        email = PromptValidator.get_input(
            "Enter email address", PromptValidator.valid_email,
            "Enter a valid email address."
        )
        customer_id = self.db.add_record(
            "customers", [name, address, phone, email]
        )
        print(f"\nCustomer successfully registered: {customer_id}")
        PromptValidator.pause()

    def modify_customer(self):
        cid = PromptValidator.get_input(
            "Enter Customer ID", lambda value: value in self.db.customers.index,
            "Customer not found."
        )
        print("\nCurrent customer information:\n")
        print(self.db.customers.loc[cid])
        updated = self.db.customers.loc[cid].copy()
        for column in EXPECTED_COLUMNS["customers"]:
            value = PromptValidator.get_input(
                f"New {column} (blank to keep current)"
            )
            if value:
                updated[column] = value
        if not PromptValidator.valid_email(updated["Customer_Email"]):
            print("Invalid email. No changes saved.")
            return
        self.db.update_record("customers", cid, updated)
        print("\nCustomer information updated.")
        PromptValidator.pause()

    def remove_customer(self):
        cid = PromptValidator.get_input(
            "Enter Customer ID", lambda value: value in self.db.customers.index,
            "Customer not found."
        )
        linked = self.db.bookings[self.db.bookings["Customer_ID"] == cid]
        if not linked.empty:
            print("Cannot delete this customer because booking records are associated with this profile.")
            PromptValidator.pause()
            return
        print(self.db.customers.loc[cid])
        confirm = PromptValidator.get_input(
            "Confirm deletion (Y/N)", lambda value: value.upper() in ["Y", "N"]
        )
        if confirm.upper() == "Y":
            self.db.delete_record("customers", cid)
            print("Customer deleted successfully.")
        else:
            print("Deletion cancelled.")
        PromptValidator.pause()

    def view_profile(self):
        cid = PromptValidator.get_input(
            "Enter Customer ID", lambda value: value in self.db.customers.index,
            "Customer not found."
        )
        print("\nCustomer Profile:\n")
        print(self.db.customers.loc[cid])
        bookings = self.db.bookings[self.db.bookings["Customer_ID"] == cid]
        if bookings.empty:
            print("\nNo booking history found.")
        else:
            print("\nBooking History:\n")
            print(bookings)
            valid = bookings[bookings["Tour_ID"].isin(self.db.tours.index)]
            counts = valid["Tour_ID"].value_counts()
            if not counts.empty:
                names = self.db.tours.loc[counts.index, "Tour_Name"]
                plt.figure(figsize=(7, 4))
                plt.bar(names, counts.values)
                plt.title(f"Tour-wise Booking History: {cid}")
                plt.ylabel("Booking Count")
                plt.xticks(rotation=30)
                plt.tight_layout()
                plt.show()
        PromptValidator.pause()


# =====================================================================
# 8. GUIDE OPERATIONS
# =====================================================================

class GuideOperations(MenuController):
    def __init__(self, db):
        super().__init__("Guide Management")
        self.db = db
        self.dispatch_map = {
            "0": self.add_guide, "1": self.modify_guide,
            "2": self.remove_guide, "3": self.view_guide,
        }

    def show_menu(self):
        print("""
+----------------------------------------+
|              GUIDE OPERATIONS           |
+----------------------------------------+
| 0 | ADD GUIDE                           |
| 1 | MODIFY GUIDE                        |
| 2 | REMOVE GUIDE                        |
| 3 | VIEW GUIDE                           |
| 4 | RETURN TO MAIN MENU                  |
+----------------------------------------+
""")

    def add_guide(self):
        name = PromptValidator.get_input("Enter guide name")
        contact = PromptValidator.get_input("Enter guide contact")
        tour_id = PromptValidator.get_input(
            "Assigned Tour ID (blank if unassigned)"
        )
        if tour_id and tour_id not in self.db.tours.index:
            print("Specified tour does not exist.")
            return
        guide_id = self.db.add_record("guides", [name, contact, tour_id])
        print(f"\nGuide successfully registered: {guide_id}")
        PromptValidator.pause()

    def modify_guide(self):
        gid = PromptValidator.get_input(
            "Enter Guide ID", lambda value: value in self.db.guides.index,
            "Guide not found."
        )
        print("\nCurrent guide information:\n")
        print(self.db.guides.loc[gid])
        updated = self.db.guides.loc[gid].copy()
        for column in ["Guide_Name", "Contact"]:
            value = PromptValidator.get_input(
                f"New {column} (blank to keep current)"
            )
            if value:
                updated[column] = value
        tour_id = PromptValidator.get_input(
            "New Tour ID (blank to keep current assignment)"
        )
        if tour_id:
            if tour_id not in self.db.tours.index:
                print("Specified tour does not exist.")
                return
            updated["Tour_ID"] = tour_id
        self.db.update_record("guides", gid, updated)
        print("\nGuide information updated.")
        PromptValidator.pause()

    def remove_guide(self):
        gid = PromptValidator.get_input(
            "Enter Guide ID", lambda value: value in self.db.guides.index,
            "Guide not found."
        )
        print(self.db.guides.loc[gid])
        confirm = PromptValidator.get_input(
            "Confirm guide deletion (Y/N)", lambda value: value.upper() in ["Y", "N"]
        )
        if confirm.upper() == "Y":
            self.db.delete_record("guides", gid)
            print("Guide successfully removed.")
        else:
            print("Deletion cancelled.")
        PromptValidator.pause()

    def view_guide(self):
        gid = PromptValidator.get_input(
            "Enter Guide ID", lambda value: value in self.db.guides.index,
            "Guide not found."
        )
        guide = self.db.guides.loc[gid]
        print("\nGuide Information:\n")
        print(guide)
        tour_id = guide["Tour_ID"]
        if tour_id and tour_id in self.db.tours.index:
            print("\nAssigned Tour:\n")
            print(self.db.tours.loc[tour_id])
        elif tour_id:
            print("\nAssigned tour reference is invalid.")
        else:
            print("\nNo tour currently assigned.")
        PromptValidator.pause()


# =====================================================================
# 9. CENTRAL APPLICATION ENGINE
# =====================================================================

class AppEngine:
    def __init__(self, data_dir=None):
        self.db = DatabaseManager(data_dir=data_dir)
        self.history = SessionHistory()
        self.modules = {
            "1": TourOperations(self.db),
            "2": CustomerOperations(self.db),
            "3": GuideOperations(self.db),
        }

    def show_main_menu(self):
        print("""
+----------------------------------------+
|       TOUR AND TRAVEL MANAGEMENT        |
+----------------------------------------+
| 0 | PROJECT INTRODUCTION                |
| 1 | TOUR OPERATIONS                     |
| 2 | CUSTOMER OPERATIONS                 |
| 3 | GUIDE OPERATIONS                    |
| 4 | EXIT                                |
+----------------------------------------+
""")

    def start(self):
        while True:
            self.show_main_menu()
            try:
                choice = PromptValidator.get_input(
                    "Enter your choice",
                    lambda value: value in ["0", "1", "2", "3", "4"],
                    "Invalid menu selection."
                )
                if choice == "4":
                    print("\nExiting application database. Goodbye!")
                    break
                if choice == "0":
                    print("""
Welcome to the Tour and Travel Management System!

This application provides a centralized CLI interface
for managing tour packages, customer profiles,
and tour guide information.

It uses:
- Object-Oriented Programming
- CSV-based data persistence
- Pandas DataFrames
- Custom exception handling
- Stack-based session tracking
- Matplotlib visualizations
""")
                    PromptValidator.pause()
                    continue
                module = self.modules.get(choice)
                if module:
                    self.history.push(choice)
                    try:
                        module.execute()
                    finally:
                        self.history.pop()
            except NavigationBackException:
                print("\nReturned to main menu.")


# =====================================================================
# 10. APPLICATION ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    try:
        engine = AppEngine()
        engine.start()
    except FileNotFoundError as error:
        print(f"\nApplication startup failed: {error}")
    except DataValidationException as error:
        print(f"\nDataset validation failed: {error}")
    except (KeyboardInterrupt, EOFError):
        print("\nApplication interrupted by user.")
