import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta, datetime
import mysql.connector
from mysql.connector import Error

# -------------------- DATABASE CONFIGURATION --------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "library_db",
}

LOAN_DAYS = 14
MAX_ACTIVE_ISSUES = 3
FINE_PER_DAY = 5.0


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# -------------------- DATABASE HELPERS --------------------
def fetch_all(query, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def execute_query(query, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# -------------------- MAIN APPLICATION --------------------
class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1120x700")
        self.minsize(1000, 620)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.create_menu()
        self.create_header()
        self.create_tabs()

        try:
            self.refresh_all()
        except Error as e:
            messagebox.showerror(
                "Database Error",
                "Could not connect to MySQL.\n\n"
                "Check DB_CONFIG in app.py and run database/schema.sql.\n\n"
                f"Details: {e}"
            )

    def create_menu(self):
        menu = tk.Menu(self)
        help_menu = tk.Menu(menu, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu)

    def create_header(self):
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(
            header, text="LIBRARY MANAGEMENT SYSTEM",
            font=("Arial", 20, "bold")
        ).pack(side="left")
        ttk.Label(
            header, text="Tkinter + MySQL | Final Year Project",
            font=("Arial", 10)
        ).pack(side="right")

    def create_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.books_tab = ttk.Frame(self.tabs)
        self.members_tab = ttk.Frame(self.tabs)
        self.transactions_tab = ttk.Frame(self.tabs)
        self.dashboard_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.tabs.add(self.books_tab, text="Books")
        self.tabs.add(self.members_tab, text="Members")
        self.tabs.add(self.transactions_tab, text="Issue / Return")

        self.build_dashboard()
        self.build_books()
        self.build_members()
        self.build_transactions()

    # -------------------- DASHBOARD --------------------
    def build_dashboard(self):
        top = ttk.Frame(self.dashboard_tab, padding=20)
        top.pack(fill="x")

        self.stat_books = tk.StringVar(value="0")
        self.stat_members = tk.StringVar(value="0")
        self.stat_issued = tk.StringVar(value="0")
        self.stat_overdue = tk.StringVar(value="0")

        stats = [
            ("Total Books", self.stat_books),
            ("Members", self.stat_members),
            ("Active Issues", self.stat_issued),
            ("Overdue", self.stat_overdue),
        ]
        for i, (title, variable) in enumerate(stats):
            box = ttk.LabelFrame(top, text=title, padding=25)
            box.grid(row=0, column=i, padx=8, sticky="nsew")
            ttk.Label(box, textvariable=variable, font=("Arial", 24, "bold")).pack()
            top.columnconfigure(i, weight=1)

        info = ttk.LabelFrame(self.dashboard_tab, text="Business Rules", padding=20)
        info.pack(fill="x", padx=20, pady=10)
        rules = (
            f"• Maximum {MAX_ACTIVE_ISSUES} active books per member\n"
            f"• Standard loan period: {LOAN_DAYS} days\n"
            f"• Late fine: ₹{FINE_PER_DAY:.2f} per overdue day\n"
            "• A book cannot be issued when no copies are available\n"
            "• A member cannot be deleted while they have active issues\n"
            "• Returning a book automatically increases available copies"
        )
        ttk.Label(info, text=rules, justify="left").pack(anchor="w")

        ttk.Button(
            self.dashboard_tab, text="Refresh Dashboard",
            command=self.refresh_dashboard
        ).pack(pady=15)

    # -------------------- BOOKS CRUD --------------------
    def build_books(self):
        form = ttk.LabelFrame(self.books_tab, text="Book Details", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        self.book_id = tk.StringVar()
        self.book_title = tk.StringVar()
        self.book_author = tk.StringVar()
        self.book_category = tk.StringVar()
        self.book_copies = tk.StringVar(value="1")

        fields = [
            ("ID", self.book_id), ("Title", self.book_title),
            ("Author", self.book_author), ("Category", self.book_category),
            ("Copies", self.book_copies)
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i*2, padx=5, pady=5)
            ttk.Entry(form, textvariable=var, width=20).grid(row=0, column=i*2+1, padx=5, pady=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=1, column=0, columnspan=10, pady=8)
        ttk.Button(buttons, text="Add", command=self.add_book).pack(side="left", padx=5)
        ttk.Button(buttons, text="Update", command=self.update_book).pack(side="left", padx=5)
        ttk.Button(buttons, text="Delete", command=self.delete_book).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear", command=self.clear_book).pack(side="left", padx=5)
        ttk.Button(buttons, text="Refresh", command=self.refresh_books).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.books_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("id", "title", "author", "category", "total", "available")
        self.books_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        headings = {
            "id": "ID", "title": "Title", "author": "Author",
            "category": "Category", "total": "Total Copies",
            "available": "Available"
        }
        widths = {"id": 60, "title": 240, "author": 180, "category": 130, "total": 100, "available": 100}
        for c in cols:
            self.books_tree.heading(c, text=headings[c])
            self.books_tree.column(c, width=widths[c])
        self.books_tree.pack(side="left", fill="both", expand=True)
        self.books_tree.bind("<<TreeviewSelect>>", self.select_book)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.books_tree.yview)
        scroll.pack(side="right", fill="y")
        self.books_tree.configure(yscrollcommand=scroll.set)

    def validate_book(self):
        if not self.book_title.get().strip() or not self.book_author.get().strip():
            messagebox.showwarning("Validation", "Title and author are required.")
            return False
        try:
            copies = int(self.book_copies.get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Copies must be a positive integer.")
            return False
        return True

    def add_book(self):
        if not self.validate_book():
            return
        try:
            execute_query(
                "INSERT INTO books(title, author, category, total_copies, available_copies) "
                "VALUES (%s,%s,%s,%s,%s)",
                (self.book_title.get().strip(), self.book_author.get().strip(),
                 self.book_category.get().strip(), int(self.book_copies.get()),
                 int(self.book_copies.get()))
            )
            messagebox.showinfo("Success", "Book added successfully.")
            self.clear_book()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def update_book(self):
        if not self.book_id.get():
            messagebox.showwarning("Select", "Select a book first.")
            return
        if not self.validate_book():
            return
        try:
            book = fetch_all(
                "SELECT total_copies, available_copies FROM books WHERE book_id=%s",
                (self.book_id.get(),)
            )
            if not book:
                return
            old_total, old_available = book[0]
            new_total = int(self.book_copies.get())
            issued = old_total - old_available
            if new_total < issued:
                messagebox.showwarning(
                    "Validation",
                    f"Cannot reduce copies below currently issued copies ({issued})."
                )
                return
            new_available = new_total - issued
            execute_query(
                "UPDATE books SET title=%s, author=%s, category=%s, "
                "total_copies=%s, available_copies=%s WHERE book_id=%s",
                (self.book_title.get().strip(), self.book_author.get().strip(),
                 self.book_category.get().strip(), new_total, new_available,
                 self.book_id.get())
            )
            messagebox.showinfo("Success", "Book updated successfully.")
            self.clear_book()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def delete_book(self):
        if not self.book_id.get():
            messagebox.showwarning("Select", "Select a book first.")
            return
        active = fetch_all(
            "SELECT COUNT(*) FROM transactions WHERE book_id=%s AND status='ISSUED'",
            (self.book_id.get(),)
        )[0][0]
        if active:
            messagebox.showwarning("Business Rule", "Cannot delete a book that is currently issued.")
            return
        if messagebox.askyesno("Confirm", "Delete selected book?"):
            try:
                execute_query("DELETE FROM books WHERE book_id=%s", (self.book_id.get(),))
                self.clear_book()
                self.refresh_all()
            except Error as e:
                messagebox.showerror("Database Error", str(e))

    def select_book(self, _event=None):
        selected = self.books_tree.selection()
        if not selected:
            return
        values = self.books_tree.item(selected[0], "values")
        self.book_id.set(values[0])
        self.book_title.set(values[1])
        self.book_author.set(values[2])
        self.book_category.set(values[3])
        self.book_copies.set(values[4])

    def clear_book(self):
        self.book_id.set("")
        self.book_title.set("")
        self.book_author.set("")
        self.book_category.set("")
        self.book_copies.set("1")

    def refresh_books(self):
        for row in self.books_tree.get_children():
            self.books_tree.delete(row)
        for row in fetch_all(
            "SELECT book_id,title,author,category,total_copies,available_copies "
            "FROM books ORDER BY book_id DESC"
        ):
            self.books_tree.insert("", "end", values=row)

    # -------------------- MEMBERS CRUD --------------------
    def build_members(self):
        form = ttk.LabelFrame(self.members_tab, text="Member Details", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        self.member_id = tk.StringVar()
        self.member_name = tk.StringVar()
        self.member_email = tk.StringVar()
        self.member_phone = tk.StringVar()

        fields = [
            ("ID", self.member_id), ("Name", self.member_name),
            ("Email", self.member_email), ("Phone", self.member_phone)
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i*2, padx=5)
            ttk.Entry(form, textvariable=var, width=25).grid(row=0, column=i*2+1, padx=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=1, column=0, columnspan=8, pady=8)
        ttk.Button(buttons, text="Add", command=self.add_member).pack(side="left", padx=5)
        ttk.Button(buttons, text="Update", command=self.update_member).pack(side="left", padx=5)
        ttk.Button(buttons, text="Delete", command=self.delete_member).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear", command=self.clear_member).pack(side="left", padx=5)
        ttk.Button(buttons, text="Refresh", command=self.refresh_members).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.members_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("id", "name", "email", "phone", "joined")
        self.members_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        headings = {"id":"ID","name":"Name","email":"Email","phone":"Phone","joined":"Joined On"}
        widths = {"id":70,"name":220,"email":260,"phone":150,"joined":130}
        for c in cols:
            self.members_tree.heading(c, text=headings[c])
            self.members_tree.column(c, width=widths[c])
        self.members_tree.pack(side="left", fill="both", expand=True)
        self.members_tree.bind("<<TreeviewSelect>>", self.select_member)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.members_tree.yview)
        scroll.pack(side="right", fill="y")
        self.members_tree.configure(yscrollcommand=scroll.set)

    def validate_member(self):
        if not self.member_name.get().strip() or not self.member_email.get().strip():
            messagebox.showwarning("Validation", "Name and email are required.")
            return False
        if "@" not in self.member_email.get():
            messagebox.showwarning("Validation", "Enter a valid email address.")
            return False
        return True

    def add_member(self):
        if not self.validate_member():
            return
        try:
            execute_query(
                "INSERT INTO members(name,email,phone) VALUES (%s,%s,%s)",
                (self.member_name.get().strip(), self.member_email.get().strip(),
                 self.member_phone.get().strip())
            )
            messagebox.showinfo("Success", "Member added successfully.")
            self.clear_member()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def update_member(self):
        if not self.member_id.get():
            messagebox.showwarning("Select", "Select a member first.")
            return
        if not self.validate_member():
            return
        try:
            execute_query(
                "UPDATE members SET name=%s,email=%s,phone=%s WHERE member_id=%s",
                (self.member_name.get().strip(), self.member_email.get().strip(),
                 self.member_phone.get().strip(), self.member_id.get())
            )
            messagebox.showinfo("Success", "Member updated successfully.")
            self.clear_member()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def delete_member(self):
        if not self.member_id.get():
            messagebox.showwarning("Select", "Select a member first.")
            return
        active = fetch_all(
            "SELECT COUNT(*) FROM transactions WHERE member_id=%s AND status='ISSUED'",
            (self.member_id.get(),)
        )[0][0]
        if active:
            messagebox.showwarning("Business Rule", "Cannot delete a member with active issued books.")
            return
        if messagebox.askyesno("Confirm", "Delete selected member?"):
            try:
                execute_query("DELETE FROM members WHERE member_id=%s", (self.member_id.get(),))
                self.clear_member()
                self.refresh_all()
            except Error as e:
                messagebox.showerror("Database Error", str(e))

    def select_member(self, _event=None):
        selected = self.members_tree.selection()
        if not selected:
            return
        values = self.members_tree.item(selected[0], "values")
        self.member_id.set(values[0])
        self.member_name.set(values[1])
        self.member_email.set(values[2])
        self.member_phone.set(values[3])

    def clear_member(self):
        self.member_id.set("")
        self.member_name.set("")
        self.member_email.set("")
        self.member_phone.set("")

    def refresh_members(self):
        for row in self.members_tree.get_children():
            self.members_tree.delete(row)
        for row in fetch_all(
            "SELECT member_id,name,email,phone,joined_on FROM members ORDER BY member_id DESC"
        ):
            self.members_tree.insert("", "end", values=row)

    # -------------------- ISSUE / RETURN --------------------
    def build_transactions(self):
        form = ttk.LabelFrame(self.transactions_tab, text="Issue / Return Book", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        self.issue_member = tk.StringVar()
        self.issue_book = tk.StringVar()
        self.return_transaction = tk.StringVar()

        ttk.Label(form, text="Member ID").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(form, textvariable=self.issue_member, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Book ID").grid(row=0, column=2, padx=5)
        ttk.Entry(form, textvariable=self.issue_book, width=15).grid(row=0, column=3, padx=5)

        ttk.Button(form, text="Issue Book", command=self.issue_book_action).grid(row=0, column=4, padx=10)
        ttk.Button(form, text="Clear", command=self.clear_issue).grid(row=0, column=5, padx=5)

        ttk.Label(form, text="Transaction ID").grid(row=1, column=0, padx=5, pady=8)
        ttk.Entry(form, textvariable=self.return_transaction, width=15).grid(row=1, column=1, padx=5)
        ttk.Button(form, text="Return Book", command=self.return_book_action).grid(row=1, column=2, padx=10)

        table_frame = ttk.Frame(self.transactions_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("id","member","member_name","book","title","issue","due","return","status","fine")
        self.trans_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        headings = {
            "id":"Txn ID","member":"Member ID","member_name":"Member",
            "book":"Book ID","title":"Book","issue":"Issue Date",
            "due":"Due Date","return":"Return Date","status":"Status","fine":"Fine ₹"
        }
        widths = {"id":65,"member":80,"member_name":150,"book":65,"title":190,
                  "issue":100,"due":100,"return":100,"status":90,"fine":80}
        for c in cols:
            self.trans_tree.heading(c, text=headings[c])
            self.trans_tree.column(c, width=widths[c])
        self.trans_tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.trans_tree.yview)
        scroll.pack(side="right", fill="y")
        self.trans_tree.configure(yscrollcommand=scroll.set)

        self.trans_tree.bind("<<TreeviewSelect>>", self.select_transaction)

    def issue_book_action(self):
        try:
            member_id = int(self.issue_member.get())
            book_id = int(self.issue_book.get())
        except ValueError:
            messagebox.showwarning("Validation", "Member ID and Book ID must be integers.")
            return

        try:
            member = fetch_all("SELECT member_id FROM members WHERE member_id=%s", (member_id,))
            book = fetch_all(
                "SELECT book_id, available_copies FROM books WHERE book_id=%s",
                (book_id,)
            )
            if not member:
                messagebox.showwarning("Business Rule", "Member does not exist.")
                return
            if not book:
                messagebox.showwarning("Business Rule", "Book does not exist.")
                return
            if book[0][1] <= 0:
                messagebox.showwarning("Business Rule", "No available copies of this book.")
                return

            active = fetch_all(
                "SELECT COUNT(*) FROM transactions WHERE member_id=%s AND status='ISSUED'",
                (member_id,)
            )[0][0]
            if active >= MAX_ACTIVE_ISSUES:
                messagebox.showwarning(
                    "Business Rule",
                    f"Member already has {MAX_ACTIVE_ISSUES} active books."
                )
                return

            duplicate = fetch_all(
                "SELECT COUNT(*) FROM transactions WHERE member_id=%s AND book_id=%s AND status='ISSUED'",
                (member_id, book_id)
            )[0][0]
            if duplicate:
                messagebox.showwarning("Business Rule", "This member already has this book.")
                return

            issue_date = date.today()
            due_date = issue_date + timedelta(days=LOAN_DAYS)

            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO transactions(member_id,book_id,issue_date,due_date,status) "
                    "VALUES (%s,%s,%s,%s,'ISSUED')",
                    (member_id, book_id, issue_date, due_date)
                )
                cur.execute(
                    "UPDATE books SET available_copies=available_copies-1 WHERE book_id=%s",
                    (book_id,)
                )
                conn.commit()
            except Error:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()

            messagebox.showinfo(
                "Success",
                f"Book issued successfully.\nDue date: {due_date.strftime('%d-%m-%Y')}"
            )
            self.clear_issue()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def return_book_action(self):
        try:
            txn_id = int(self.return_transaction.get())
        except ValueError:
            messagebox.showwarning("Validation", "Transaction ID must be an integer.")
            return

        try:
            txn = fetch_all(
                "SELECT transaction_id, book_id, issue_date, due_date, status "
                "FROM transactions WHERE transaction_id=%s",
                (txn_id,)
            )
            if not txn:
                messagebox.showwarning("Validation", "Transaction not found.")
                return
            _, book_id, _, due_date, status = txn[0]
            if status == "RETURNED":
                messagebox.showwarning("Business Rule", "This transaction is already returned.")
                return

            return_date = date.today()
            overdue_days = max(0, (return_date - due_date).days)
            fine = overdue_days * FINE_PER_DAY

            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE transactions SET return_date=%s,status='RETURNED',fine=%s "
                    "WHERE transaction_id=%s",
                    (return_date, fine, txn_id)
                )
                cur.execute(
                    "UPDATE books SET available_copies=available_copies+1 WHERE book_id=%s",
                    (book_id,)
                )
                conn.commit()
            except Error:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()

            messagebox.showinfo(
                "Book Returned",
                f"Book returned successfully.\nFine: ₹{fine:.2f}"
            )
            self.clear_issue()
            self.refresh_all()
        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def select_transaction(self, _event=None):
        selected = self.trans_tree.selection()
        if selected:
            values = self.trans_tree.item(selected[0], "values")
            self.return_transaction.set(values[0])

    def clear_issue(self):
        self.issue_member.set("")
        self.issue_book.set("")
        self.return_transaction.set("")

    def refresh_transactions(self):
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        query = """
            SELECT t.transaction_id, m.member_id, m.name, b.book_id, b.title,
                   t.issue_date, t.due_date, t.return_date, t.status, t.fine
            FROM transactions t
            JOIN members m ON t.member_id=m.member_id
            JOIN books b ON t.book_id=b.book_id
            ORDER BY t.transaction_id DESC
        """
        for row in fetch_all(query):
            self.trans_tree.insert("", "end", values=row)

    # -------------------- DASHBOARD / REFRESH --------------------
    def refresh_dashboard(self):
        self.stat_books.set(fetch_all("SELECT COALESCE(SUM(total_copies),0) FROM books")[0][0])
        self.stat_members.set(fetch_all("SELECT COUNT(*) FROM members")[0][0])
        self.stat_issued.set(fetch_all(
            "SELECT COUNT(*) FROM transactions WHERE status='ISSUED'"
        )[0][0])
        self.stat_overdue.set(fetch_all(
            "SELECT COUNT(*) FROM transactions WHERE status='ISSUED' AND due_date < CURDATE()"
        )[0][0])

    def refresh_all(self):
        self.refresh_books()
        self.refresh_members()
        self.refresh_transactions()
        self.refresh_dashboard()

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Library Management System\n"
            "Final Year Project\n\n"
            "Frontend: Python Tkinter\n"
            "Backend: MySQL\n"
            "Driver: mysql-connector-python"
        )


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
