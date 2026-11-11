# ⚡ Code Optimization: Tour & Travel Management System (TTMS)

while most of the primary features are present here are some future upgrade scope that I want to work on 

### 1. Database Persistence Optimization (Lazy vs. Eager Loading)
* **Current Issue:** Loading *every single* CSV file immediately upon initialization (`db = DatabaseManager()`) and rewriting the entire file on every write operation (`df.to_csv()`).
* **Optimization:** Implement a lazy-loading property pattern or a batch-commit system so writes only happen when leaving a module or completing a transaction.

### 2. $O(1)$ Data Lookup with Indexing
* **Current Issue:** Using full DataFrame boolean masks (`db.tours['Tour_Destination'].str.lower() == dest.lower()`) for text searches, which scan the full table.
* **Optimization:** Lean heavily on `.loc[]` lookups using indices, and pre-normalize destination strings to lowercase upon loading to avoid redundant compute overhead.

### 3. Separation of Concerns (UI vs. Data Logic)
* **Current Issue:** Controller classes (`TourOperations`, `CustomerOperations`) are juggling terminal inputs (`input()`), validation, DataFrame transformations, and Matplotlib plots all at once.
* **Optimization:** Extract plotting and data-filtering logic into a separate reporting helper service to keep controllers testable and decoupled.

### 4. Memory Management for Matplotlib Plots
* **Current Issue:** Calling `plt.figure()` and `plt.show()` repeatedly without clearing or closing the figure context, causing memory leaks in long-running CLI sessions.
* **Optimization:** Always add `plt.close()` right after `plt.show()` to instantly free up system resources.
