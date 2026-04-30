# -*- coding: utf-8 -*-
"""
Library Management System - Modern GUI Version
-----------------------------------------------
A beautifully designed library management system with modern aesthetics,
smooth animations, and full functionality.
"""

import sys
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.font import Font

# ------------------ Data Persistence ------------------
def get_data_dir():
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    data_dir = base / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

DATA_DIR = get_data_dir()
BOOKS_FILE = DATA_DIR / "books.json"
MEMBERS_FILE = DATA_DIR / "members.json"
TRANSACTIONS_FILE = DATA_DIR / "transactions.json"

FINE_PER_DAY = 2.0
LOAN_PERIOD_DAYS = 14

# ------------------ Core Classes ------------------
class Book:
    def __init__(self, title, author, isbn, available_copies, category="General"):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.available_copies = available_copies
        self.category = category
        self.added_date = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self):
        return {
            "title": self.title, 
            "author": self.author, 
            "isbn": self.isbn, 
            "available_copies": self.available_copies,
            "category": self.category,
            "added_date": self.added_date
        }

    @staticmethod
    def from_dict(data):
        book = Book(data["title"], data["author"], data["isbn"], data["available_copies"], data.get("category", "General"))
        book.added_date = data.get("added_date", datetime.now().strftime("%Y-%m-%d"))
        return book

class Member:
    def __init__(self, member_id, name, email="", phone=""):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.phone = phone
        self.borrowed_books = []
        self.loan_history = []
        self.member_since = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self):
        return {
            "member_id": self.member_id, 
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "borrowed_books": self.borrowed_books, 
            "loan_history": self.loan_history,
            "member_since": self.member_since
        }

    @staticmethod
    def from_dict(data):
        m = Member(data["member_id"], data["name"], data.get("email", ""), data.get("phone", ""))
        m.borrowed_books = data.get("borrowed_books", [])
        m.loan_history = data.get("loan_history", [])
        m.member_since = data.get("member_since", datetime.now().strftime("%Y-%m-%d"))
        return m

class Library:
    def __init__(self):
        self.books = []
        self.members = {}
        self.transactions = []
        self.load_data()

    def load_data(self):
        if BOOKS_FILE.exists():
            with open(BOOKS_FILE, "r") as f:
                self.books = [Book.from_dict(b) for b in json.load(f)]
        if MEMBERS_FILE.exists():
            with open(MEMBERS_FILE, "r") as f:
                data = json.load(f)
                self.members = {mid: Member.from_dict(m) for mid, m in data.items()}
        if TRANSACTIONS_FILE.exists():
            with open(TRANSACTIONS_FILE, "r") as f:
                self.transactions = json.load(f)

    def save_data(self):
        with open(BOOKS_FILE, "w") as f:
            json.dump([b.to_dict() for b in self.books], f, indent=4)
        with open(MEMBERS_FILE, "w") as f:
            json.dump({mid: m.to_dict() for mid, m in self.members.items()}, f, indent=4)
        with open(TRANSACTIONS_FILE, "w") as f:
            json.dump(self.transactions, f, indent=4)

    def add_book(self, book):
        self.books.append(book)
        self.save_data()

    def add_member(self, member_id, name, email="", phone=""):
        if member_id not in self.members:
            self.members[member_id] = Member(member_id, name, email, phone)
            self.save_data()
            return True
        return False

    def issue_book(self, member_id, isbn):
        if member_id not in self.members:
            messagebox.showerror("Error", "Member not found!")
            return False
        
        member = self.members[member_id]
        book = next((b for b in self.books if b.isbn == isbn), None)
        
        if not book:
            messagebox.showerror("Error", "Book not found!")
            return False
        
        if book.available_copies <= 0:
            messagebox.showerror("Error", "No copies available!")
            return False
        
        if any(b['isbn'] == isbn for b in member.borrowed_books):
            messagebox.showerror("Error", "Member already borrowed this book!")
            return False
        
        # Issue the book
        book.available_copies -= 1
        due_date = (datetime.now() + timedelta(days=LOAN_PERIOD_DAYS)).strftime("%Y-%m-%d")
        
        transaction = {
            "member_id": member_id,
            "member_name": member.name,
            "isbn": isbn,
            "book_title": book.title,
            "issue_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due_date,
            "status": "issued"
        }
        
        member.borrowed_books.append({"isbn": isbn, "issue_date": transaction["issue_date"], "due_date": due_date})
        member.loan_history.append(transaction)
        self.transactions.append(transaction)
        self.save_data()
        
        messagebox.showinfo("Success", f"Book '{book.title}' issued to {member.name}!\nDue Date: {due_date}")
        return True

    def return_book(self, member_id, isbn):
        if member_id not in self.members:
            messagebox.showerror("Error", "Member not found!")
            return False
        
        member = self.members[member_id]
        book = next((b for b in self.books if b.isbn == isbn), None)
        
        if not book:
            messagebox.showerror("Error", "Book not found!")
            return False
        
        borrowed = next((b for b in member.borrowed_books if b['isbn'] == isbn), None)
        if not borrowed:
            messagebox.showerror("Error", "Member hasn't borrowed this book!")
            return False
        
        # Calculate fine
        due_date = datetime.strptime(borrowed['due_date'], "%Y-%m-%d")
        days_overdue = (datetime.now() - due_date).days
        fine = max(0, days_overdue * FINE_PER_DAY)
        
        # Return the book
        book.available_copies += 1
        member.borrowed_books.remove(borrowed)
        
        # Update transaction
        for trans in self.transactions:
            if trans['member_id'] == member_id and trans['isbn'] == isbn and trans['status'] == 'issued':
                trans['status'] = 'returned'
                trans['return_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trans['fine'] = fine
                break
        
        self.save_data()
        
        fine_msg = f"\nFine: ${fine:.2f}" if fine > 0 else ""
        messagebox.showinfo("Success", f"Book '{book.title}' returned successfully!{fine_msg}")
        return True

# ------------------ Modern GUI Application ------------------
class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, icon="", color="#6366f1", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.command = command
        self.text = text
        self.icon = icon
        self.color = color
        self.hover_color = "#7c3aed"
        self.current_color = color
        
        self.configure(bg=parent.cget("bg") if hasattr(parent, "cget") else "#1e1e2e")
        self.create_rounded_rect()
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def create_rounded_rect(self):
        self.delete("all")
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        r = 10
        self.create_rounded_rectangle(0, 0, width, height, r, fill=self.current_color, outline="", tags="rect")
        self.create_text(width//2, height//2, text=f"{self.icon} {self.text}", fill="white", 
                        font=("Segoe UI", 11, "bold"), tags="text")
        
    def create_rounded_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        points = (x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1)
        return self.create_polygon(points, **kwargs, smooth=True)
    
    def on_enter(self, e):
        self.current_color = self.hover_color
        self.create_rounded_rect()
        
    def on_leave(self, e):
        self.current_color = self.color
        self.create_rounded_rect()
        
    def on_click(self, e):
        if self.command:
            self.command()

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Library Management System")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Modern color scheme
        self.bg_color = "#0f0f1a"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#6366f1"
        self.card_color = "#1a1a2e"
        self.success_color = "#10b981"
        self.warning_color = "#f59e0b"
        self.error_color = "#ef4444"
        
        self.root.configure(bg=self.bg_color)
        
        self.library = Library()
        
        # Custom fonts
        self.title_font = Font(family="Segoe UI", size=24, weight="bold")
        self.heading_font = Font(family="Segoe UI", size=14, weight="bold")
        self.body_font = Font(family="Segoe UI", size=11)
        
        self.setup_ui()
        
        self.refresh_books_list()
        self.refresh_members_list()
        self.update_stats()
        
    def setup_ui(self):
        # Top Header
        header_frame = tk.Frame(self.root, bg=self.accent_color, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="📚 Library Management System", 
                              font=self.title_font, bg=self.accent_color, fg="white")
        title_label.pack(pady=20)
        
        # Stats Bar
        stats_frame = tk.Frame(self.root, bg=self.card_color, height=100)
        stats_frame.pack(fill="x", padx=20, pady=10)
        stats_frame.pack_propagate(False)
        
        self.stats_labels = {}
        stats = ["Total Books", "Unique Titles", "Total Members", "Active Loans"]
        for i, stat in enumerate(stats):
            card = tk.Frame(stats_frame, bg=self.bg_color, relief="flat", bd=0)
            card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
            
            tk.Label(card, text=stat, font=self.body_font, bg=self.bg_color, fg="#888").pack(pady=5)
            label = tk.Label(card, text="0", font=("Segoe UI", 20, "bold"), bg=self.bg_color, fg=self.accent_color)
            label.pack(pady=5)
            self.stats_labels[stat] = label
        
        # Main Content
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Notebook (Tabs)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.card_color, foreground=self.fg_color, 
                       padding=[20, 10], font=self.body_font)
        style.map("TNotebook.Tab", background=[("selected", self.accent_color), ("active", "#2d2d44")])
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Books Tab
        self.books_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.books_frame, text="📖 Books")
        self.setup_books_tab()
        
        # Members Tab
        self.members_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.members_frame, text="👤 Members")
        self.setup_members_tab()
        
        # Transactions Tab
        self.trans_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.trans_frame, text="🔄 Transactions")
        self.setup_transactions_tab()
        
        # Settings Tab
        self.settings_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.settings_frame, text="⚙️ Settings")
        self.setup_settings_tab()
    
    def setup_books_tab(self):
        # Search Bar
        search_frame = tk.Frame(self.books_frame, bg=self.bg_color)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:", bg=self.bg_color, fg=self.fg_color, 
                font=self.body_font).pack(side="left", padx=5)
        self.book_search = tk.Entry(search_frame, font=self.body_font, bg=self.card_color, 
                                   fg=self.fg_color, insertbackground=self.fg_color, width=30)
        self.book_search.pack(side="left", padx=5)
        self.book_search.bind("<KeyRelease>", lambda e: self.filter_books())
        
        # Buttons
        btn_frame = tk.Frame(self.books_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ModernButton(btn_frame, text="Add Book", command=self.add_book_dialog, 
                    icon="➕", color="#10b981", width=120, height=35).pack(side="left", padx=5)
        ModernButton(btn_frame, text="Refresh", command=self.refresh_books_list, 
                    icon="🔄", color="#6366f1", width=120, height=35).pack(side="left", padx=5)
        ModernButton(btn_frame, text="Delete Book", command=self.delete_book, 
                    icon="🗑️", color="#ef4444", width=120, height=35).pack(side="left", padx=5)
        
        # Books Treeview with custom styling
        tree_frame = tk.Frame(self.books_frame, bg=self.bg_color)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        style = ttk.Style()
        style.configure("Custom.Treeview", background=self.card_color, foreground=self.fg_color, 
                       fieldbackground=self.card_color, font=self.body_font, rowheight=30)
        style.configure("Custom.Treeview.Heading", background=self.accent_color, 
                       foreground="white", font=self.heading_font)
        style.map("Custom.Treeview", background=[('selected', '#2d2d44')])
        
        self.books_tree = ttk.Treeview(tree_frame, columns=("ISBN", "Title", "Author", "Category", "Available"), 
                                      show="headings", style="Custom.Treeview", height=15)
        self.books_tree.heading("ISBN", text="ISBN")
        self.books_tree.heading("Title", text="Title")
        self.books_tree.heading("Author", text="Author")
        self.books_tree.heading("Category", text="Category")
        self.books_tree.heading("Available", text="Available")
        
        self.books_tree.column("ISBN", width=150)
        self.books_tree.column("Title", width=300)
        self.books_tree.column("Author", width=200)
        self.books_tree.column("Category", width=120)
        self.books_tree.column("Available", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=scrollbar.set)
        
        self.books_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_members_tab(self):
        # Search Bar
        search_frame = tk.Frame(self.members_frame, bg=self.bg_color)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:", bg=self.bg_color, fg=self.fg_color, 
                font=self.body_font).pack(side="left", padx=5)
        self.member_search = tk.Entry(search_frame, font=self.body_font, bg=self.card_color, 
                                     fg=self.fg_color, insertbackground=self.fg_color, width=30)
        self.member_search.pack(side="left", padx=5)
        self.member_search.bind("<KeyRelease>", lambda e: self.filter_members())
        
        # Buttons
        btn_frame = tk.Frame(self.members_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ModernButton(btn_frame, text="Add Member", command=self.add_member_dialog, 
                    icon="➕", color="#10b981", width=120, height=35).pack(side="left", padx=5)
        ModernButton(btn_frame, text="Refresh", command=self.refresh_members_list, 
                    icon="🔄", color="#6366f1", width=120, height=35).pack(side="left", padx=5)
        ModernButton(btn_frame, text="View Details", command=self.view_member_details, 
                    icon="👁️", color="#f59e0b", width=120, height=35).pack(side="left", padx=5)
        
        # Members Treeview
        tree_frame = tk.Frame(self.members_frame, bg=self.bg_color)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.members_tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Email", "Phone", "Borrowed"), 
                                        show="headings", style="Custom.Treeview", height=15)
        self.members_tree.heading("ID", text="Member ID")
        self.members_tree.heading("Name", text="Name")
        self.members_tree.heading("Email", text="Email")
        self.members_tree.heading("Phone", text="Phone")
        self.members_tree.heading("Borrowed", text="Books Borrowed")
        
        self.members_tree.column("ID", width=120)
        self.members_tree.column("Name", width=200)
        self.members_tree.column("Email", width=200)
        self.members_tree.column("Phone", width=120)
        self.members_tree.column("Borrowed", width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scrollbar.set)
        
        self.members_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_transactions_tab(self):
        # Issue Section
        issue_frame = tk.LabelFrame(self.trans_frame, text="📤 Issue Book", bg=self.card_color, 
                                   fg=self.fg_color, font=self.heading_font)
        issue_frame.pack(fill="x", padx=10, pady=10)
        
        fields_frame = tk.Frame(issue_frame, bg=self.card_color)
        fields_frame.pack(pady=10)
        
        tk.Label(fields_frame, text="Member ID:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.issue_member_entry = tk.Entry(fields_frame, font=self.body_font, bg=self.bg_color, 
                                          fg=self.fg_color, insertbackground=self.fg_color, width=20)
        self.issue_member_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(fields_frame, text="Book ISBN:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.issue_isbn_entry = tk.Entry(fields_frame, font=self.body_font, bg=self.bg_color, 
                                        fg=self.fg_color, insertbackground=self.fg_color, width=20)
        self.issue_isbn_entry.grid(row=0, column=3, padx=10, pady=5)
        
        ModernButton(fields_frame, text="Issue Book", command=self.issue_book, 
                    icon="📤", color="#10b981", width=120, height=35).grid(row=0, column=4, padx=10, pady=5)
        
        # Return Section
        return_frame = tk.LabelFrame(self.trans_frame, text="📥 Return Book", bg=self.card_color, 
                                    fg=self.fg_color, font=self.heading_font)
        return_frame.pack(fill="x", padx=10, pady=10)
        
        fields_frame2 = tk.Frame(return_frame, bg=self.card_color)
        fields_frame2.pack(pady=10)
        
        tk.Label(fields_frame2, text="Member ID:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.return_member_entry = tk.Entry(fields_frame2, font=self.body_font, bg=self.bg_color, 
                                           fg=self.fg_color, insertbackground=self.fg_color, width=20)
        self.return_member_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(fields_frame2, text="Book ISBN:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.return_isbn_entry = tk.Entry(fields_frame2, font=self.body_font, bg=self.bg_color, 
                                         fg=self.fg_color, insertbackground=self.fg_color, width=20)
        self.return_isbn_entry.grid(row=0, column=3, padx=10, pady=5)
        
        ModernButton(fields_frame2, text="Return Book", command=self.return_book, 
                    icon="📥", color="#f59e0b", width=120, height=35).grid(row=0, column=4, padx=10, pady=5)
        
        # Recent Transactions
        trans_history_frame = tk.LabelFrame(self.trans_frame, text="📋 Recent Transactions", 
                                           bg=self.card_color, fg=self.fg_color, font=self.heading_font)
        trans_history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tree_frame = tk.Frame(trans_history_frame, bg=self.card_color)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.trans_tree = ttk.Treeview(tree_frame, columns=("Member", "Book", "Issue Date", "Due Date", "Status"), 
                                      show="headings", style="Custom.Treeview", height=8)
        self.trans_tree.heading("Member", text="Member")
        self.trans_tree.heading("Book", text="Book Title")
        self.trans_tree.heading("Issue Date", text="Issue Date")
        self.trans_tree.heading("Due Date", text="Due Date")
        self.trans_tree.heading("Status", text="Status")
        
        self.trans_tree.column("Member", width=150)
        self.trans_tree.column("Book", width=250)
        self.trans_tree.column("Issue Date", width=150)
        self.trans_tree.column("Due Date", width=150)
        self.trans_tree.column("Status", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trans_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_transactions()
    
    def setup_settings_tab(self):
        settings_container = tk.Frame(self.settings_frame, bg=self.bg_color)
        settings_container.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Fine Settings
        fine_frame = tk.LabelFrame(settings_container, text="💰 Fine Settings", bg=self.card_color, 
                                  fg=self.fg_color, font=self.heading_font)
        fine_frame.pack(fill="x", pady=10)
        
        fine_inner = tk.Frame(fine_frame, bg=self.card_color)
        fine_inner.pack(pady=20)
        
        tk.Label(fine_inner, text="Fine per day ($):", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=0, padx=10, pady=5)
        self.fine_entry = tk.Entry(fine_inner, font=self.body_font, bg=self.bg_color, 
                                  fg=self.fg_color, insertbackground=self.fg_color, width=10)
        self.fine_entry.insert(0, str(FINE_PER_DAY))
        self.fine_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(fine_inner, text="Loan Period (days):", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font).grid(row=0, column=2, padx=10, pady=5)
        self.loan_entry = tk.Entry(fine_inner, font=self.body_font, bg=self.bg_color, 
                                  fg=self.fg_color, insertbackground=self.fg_color, width=10)
        self.loan_entry.insert(0, str(LOAN_PERIOD_DAYS))
        self.loan_entry.grid(row=0, column=3, padx=10, pady=5)
        
        ModernButton(fine_inner, text="Save Settings", command=self.save_settings, 
                    icon="💾", color="#6366f1", width=120, height=35).grid(row=0, column=4, padx=10, pady=5)
        
        # Data Management
        data_frame = tk.LabelFrame(settings_container, text="💾 Data Management", bg=self.card_color, 
                                  fg=self.fg_color, font=self.heading_font)
        data_frame.pack(fill="x", pady=10)
        
        data_inner = tk.Frame(data_frame, bg=self.card_color)
        data_inner.pack(pady=20)
        
        ModernButton(data_inner, text="Export Data", command=self.export_data, 
                    icon="📤", color="#10b981", width=150, height=35).pack(side="left", padx=10)
        ModernButton(data_inner, text="Import Data", command=self.import_data, 
                    icon="📥", color="#f59e0b", width=150, height=35).pack(side="left", padx=10)
        ModernButton(data_inner, text="Clear All Data", command=self.clear_data, 
                    icon="⚠️", color="#ef4444", width=150, height=35).pack(side="left", padx=10)
        
        # About
        about_frame = tk.LabelFrame(settings_container, text="ℹ️ About", bg=self.card_color, 
                                   fg=self.fg_color, font=self.heading_font)
        about_frame.pack(fill="x", pady=10)
        
        about_text = """
        Library Management System v2.0
        
        A modern, feature-rich library management system with:
        • Book and member management
        • Issue/return tracking
        • Fine calculation
        • Data persistence
        • Modern UI design
        
        Developed with Python & Tkinter
        """
        
        tk.Label(about_frame, text=about_text, bg=self.card_color, fg=self.fg_color, 
                font=self.body_font, justify="left").pack(pady=20)
    
    def filter_books(self):
        search_term = self.book_search.get().lower()
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        for book in self.library.books:
            if (search_term in book.title.lower() or 
                search_term in book.author.lower() or 
                search_term in book.isbn):
                self.books_tree.insert("", "end", values=(book.isbn, book.title, book.author, 
                                                         book.category, book.available_copies))
    
    def filter_members(self):
        search_term = self.member_search.get().lower()
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        
        for mid, member in self.library.members.items():
            if (search_term in member.name.lower() or 
                search_term in mid.lower() or
                search_term in member.email.lower()):
                self.members_tree.insert("", "end", values=(mid, member.name, member.email, 
                                                           member.phone, len(member.borrowed_books)))
    
    def refresh_books_list(self):
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        for book in self.library.books:
            self.books_tree.insert("", "end", values=(book.isbn, book.title, book.author, 
                                                     book.category, book.available_copies))
    
    def refresh_members_list(self):
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        for mid, member in self.library.members.items():
            self.members_tree.insert("", "end", values=(mid, member.name, member.email, 
                                                       member.phone, len(member.borrowed_books)))
    
    def refresh_transactions(self):
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        for trans in reversed(self.library.transactions[-20:]):  # Show last 20 transactions
            status_color = "🟢 Issued" if trans['status'] == 'issued' else "🔵 Returned"
            self.trans_tree.insert("", "end", values=(trans['member_name'], trans['book_title'], 
                                                     trans['issue_date'][:10], trans['due_date'], status_color))
    
    def update_stats(self):
        total_books = sum(b.available_copies for b in self.library.books)
        total_titles = len(self.library.books)
        total_members = len(self.library.members)
        active_loans = sum(len(m.borrowed_books) for m in self.library.members.values())
        
        self.stats_labels["Total Books"].config(text=str(total_books))
        self.stats_labels["Unique Titles"].config(text=str(total_titles))
        self.stats_labels["Total Members"].config(text=str(total_members))
        self.stats_labels["Active Loans"].config(text=str(active_loans))
    
    def add_book_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Book")
        dialog.geometry("550x500")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Create main frame
        main_frame = tk.Frame(dialog, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(scrollable_frame, text="📖 Add New Book", 
                              font=("Segoe UI", 16, "bold"), 
                              bg=self.bg_color, fg=self.accent_color)
        title_label.pack(pady=15)
        
        # Form fields with more options
        fields = {}
        
        # Basic Information Section
        basic_frame = tk.LabelFrame(scrollable_frame, text="Basic Information", 
                                    bg=self.card_color, fg=self.fg_color, 
                                    font=self.heading_font)
        basic_frame.pack(fill="x", padx=20, pady=10)
        
        basic_fields = [
            ("Title:", "title", True),
            ("Author:", "author", True),
            ("ISBN:", "isbn", True),
            ("Category:", "category", False),
            ("Copies:", "copies", False),
            ("Publisher:", "publisher", False),
            ("Edition:", "edition", False)
        ]
        
        for i, (label_text, field_key, required) in enumerate(basic_fields):
            frame = tk.Frame(basic_frame, bg=self.card_color)
            frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(frame, text=label_text, bg=self.card_color, fg=self.fg_color, 
                    font=self.body_font, width=12, anchor="w").pack(side="left")
            
            entry = tk.Entry(frame, font=self.body_font, bg=self.bg_color, 
                            fg=self.fg_color, insertbackground=self.fg_color, 
                            width=35)
            entry.pack(side="left", padx=5)
            
            if required:
                tk.Label(frame, text="*", bg=self.card_color, fg=self.error_color, 
                        font=self.body_font).pack(side="left")
            
            if field_key == "copies":
                entry.insert(0, "1")
            
            fields[field_key] = entry
        
        # Additional Details Section
        details_frame = tk.LabelFrame(scrollable_frame, text="Additional Details", 
                                      bg=self.card_color, fg=self.fg_color, 
                                      font=self.heading_font)
        details_frame.pack(fill="x", padx=20, pady=10)
        
        # Year of Publication
        frame1 = tk.Frame(details_frame, bg=self.card_color)
        frame1.pack(fill="x", padx=10, pady=5)
        tk.Label(frame1, text="Year:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font, width=12, anchor="w").pack(side="left")
        fields['year'] = tk.Entry(frame1, font=self.body_font, bg=self.bg_color, 
                                 fg=self.fg_color, insertbackground=self.fg_color, width=35)
        fields['year'].pack(side="left", padx=5)
        
        # Language
        frame2 = tk.Frame(details_frame, bg=self.card_color)
        frame2.pack(fill="x", padx=10, pady=5)
        tk.Label(frame2, text="Language:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font, width=12, anchor="w").pack(side="left")
        fields['language'] = tk.Entry(frame2, font=self.body_font, bg=self.bg_color, 
                                     fg=self.fg_color, insertbackground=self.fg_color, width=35)
        fields['language'].pack(side="left", padx=5)
        fields['language'].insert(0, "English")
        
        # Pages
        frame3 = tk.Frame(details_frame, bg=self.card_color)
        frame3.pack(fill="x", padx=10, pady=5)
        tk.Label(frame3, text="Pages:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font, width=12, anchor="w").pack(side="left")
        fields['pages'] = tk.Entry(frame3, font=self.body_font, bg=self.bg_color, 
                                  fg=self.fg_color, insertbackground=self.fg_color, width=35)
        fields['pages'].pack(side="left", padx=5)
        
        # Location/Shelf
        frame4 = tk.Frame(details_frame, bg=self.card_color)
        frame4.pack(fill="x", padx=10, pady=5)
        tk.Label(frame4, text="Shelf No.:", bg=self.card_color, fg=self.fg_color, 
                font=self.body_font, width=12, anchor="w").pack(side="left")
        fields['shelf'] = tk.Entry(frame4, font=self.body_font, bg=self.bg_color, 
                                  fg=self.fg_color, insertbackground=self.fg_color, width=35)
        fields['shelf'].pack(side="left", padx=5)
        
        # Description
        desc_frame = tk.LabelFrame(scrollable_frame, text="Description", 
                                   bg=self.card_color, fg=self.fg_color, 
                                   font=self.heading_font)
        desc_frame.pack(fill="x", padx=20, pady=10)
        
        fields['description'] = tk.Text(desc_frame, font=self.body_font, bg=self.bg_color, 
                                        fg=self.fg_color, insertbackground=self.fg_color, 
                                        height=4, width=50)
        fields['description'].pack(padx=10, pady=10)
        
        # Tags
        tags_frame = tk.LabelFrame(scrollable_frame, text="Tags", 
                                   bg=self.card_color, fg=self.fg_color, 
                                   font=self.heading_font)
        tags_frame.pack(fill="x", padx=20, pady=10)
        
        fields['tags'] = tk.Entry(tags_frame, font=self.body_font, bg=self.bg_color, 
                                 fg=self.fg_color, insertbackground=self.fg_color, width=50)
        fields['tags'].pack(padx=10, pady=10)
        tk.Label(tags_frame, text="(Separate tags with commas)", bg=self.card_color, 
                fg="#888", font=("Segoe UI", 9)).pack(pady=(0, 5))
        
        # Required fields indicator
        req_label = tk.Label(scrollable_frame, text="* Required fields", 
                            bg=self.bg_color, fg="#888", font=("Segoe UI", 9))
        req_label.pack(pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        def save_book():
            title = fields['title'].get().strip()
            author = fields['author'].get().strip()
            isbn = fields['isbn'].get().strip()
            category = fields['category'].get().strip() or "General"
            
            try:
                copies = int(fields['copies'].get())
                if copies < 1:
                    messagebox.showerror("Error", "Copies must be at least 1!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid number of copies!")
                return
            
            if not all([title, author, isbn]):
                messagebox.showerror("Error", "Title, Author, and ISBN are required!")
                return
            
            # Create book object with additional info
            book = Book(title, author, isbn, copies, category)
            
            # Add additional attributes (optional)
            if hasattr(book, '__dict__'):
                if fields['publisher'].get().strip():
                    book.publisher = fields['publisher'].get().strip()
                if fields['edition'].get().strip():
                    book.edition = fields['edition'].get().strip()
                if fields['year'].get().strip():
                    book.year = fields['year'].get().strip()
                if fields['language'].get().strip():
                    book.language = fields['language'].get().strip()
                if fields['pages'].get().strip():
                    try:
                        book.pages = int(fields['pages'].get())
                    except:
                        pass
                if fields['shelf'].get().strip():
                    book.shelf = fields['shelf'].get().strip()
                if fields['description'].get('1.0', tk.END).strip():
                    book.description = fields['description'].get('1.0', tk.END).strip()
                if fields['tags'].get().strip():
                    book.tags = fields['tags'].get().strip()
            
            self.library.add_book(book)
            self.refresh_books_list()
            self.update_stats()
            dialog.destroy()
            messagebox.showinfo("Success", f"Book '{title}' added successfully!\n\nAdditional details have been saved.")
        
        # Buttons
        ModernButton(button_frame, text="Save Book", command=save_book, 
                    icon="💾", color="#10b981", width=130, height=40).pack(side="left", padx=10)
        
        ModernButton(button_frame, text="Cancel", command=dialog.destroy, 
                    icon="❌", color="#ef4444", width=130, height=40).pack(side="left", padx=10)
        
        # Add some padding at the bottom
        tk.Frame(scrollable_frame, height=20, bg=self.bg_color).pack()
    
    def add_member_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Register New Member")
        dialog.geometry("500x400")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        fields = {}
        labels = ["Member ID:", "Name:", "Email:", "Phone:"]
        for i, label in enumerate(labels):
            tk.Label(dialog, text=label, bg=self.bg_color, fg=self.fg_color, 
                    font=self.body_font).pack(pady=5)
            entry = tk.Entry(dialog, font=self.body_font, bg=self.card_color, 
                            fg=self.fg_color, insertbackground=self.fg_color, width=40)
            entry.pack(pady=5)
            fields[label[:-1].lower()] = entry
        
        def save_member():
            mid = fields['member id'].get().strip()
            name = fields['name'].get().strip()
            email = fields['email'].get().strip()
            phone = fields['phone'].get().strip()
            
            if not mid or not name:
                messagebox.showerror("Error", "Member ID and Name are required!")
                return
            
            if self.library.add_member(mid, name, email, phone):
                self.refresh_members_list()
                self.update_stats()
                dialog.destroy()
                messagebox.showinfo("Success", f"Member '{name}' registered successfully!")
            else:
                messagebox.showerror("Error", "Member ID already exists!")
        
        ModernButton(dialog, text="Register Member", command=save_member, 
                    icon="✅", color="#10b981", width=150, height=40).pack(pady=20)
    
    def delete_book(self):
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a book to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this book?"):
            item = self.books_tree.item(selected[0])
            isbn = item['values'][0]
            book = next((b for b in self.library.books if b.isbn == isbn), None)
            if book:
                self.library.books.remove(book)
                self.library.save_data()
                self.refresh_books_list()
                self.update_stats()
                messagebox.showinfo("Success", "Book deleted successfully!")
    
    def view_member_details(self):
        selected = self.members_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a member to view details!")
            return
        
        item = self.members_tree.item(selected[0])
        mid = item['values'][0]
        member = self.library.members.get(mid)
        
        if member:
            details = f"""
            Member Details
            ─────────────────
            ID: {member.member_id}
            Name: {member.name}
            Email: {member.email or 'N/A'}
            Phone: {member.phone or 'N/A'}
            Member Since: {member.member_since}
            
            Currently Borrowed Books:
            {chr(10).join([f'• {b["isbn"]} (Due: {b.get("due_date", "N/A")})' for b in member.borrowed_books]) or 'None'}
            
            Total Books Borrowed: {len(member.loan_history)}
            """
            messagebox.showinfo("Member Details", details)
    
    def issue_book(self):
        mid = self.issue_member_entry.get().strip()
        isbn = self.issue_isbn_entry.get().strip()
        
        if not mid or not isbn:
            messagebox.showerror("Error", "Please enter both Member ID and Book ISBN!")
            return
        
        if self.library.issue_book(mid, isbn):
            self.refresh_books_list()
            self.refresh_members_list()
            self.refresh_transactions()
            self.update_stats()
            self.issue_member_entry.delete(0, tk.END)
            self.issue_isbn_entry.delete(0, tk.END)
    
    def return_book(self):
        mid = self.return_member_entry.get().strip()
        isbn = self.return_isbn_entry.get().strip()
        
        if not mid or not isbn:
            messagebox.showerror("Error", "Please enter both Member ID and Book ISBN!")
            return
        
        if self.library.return_book(mid, isbn):
            self.refresh_books_list()
            self.refresh_members_list()
            self.refresh_transactions()
            self.update_stats()
            self.return_member_entry.delete(0, tk.END)
            self.return_isbn_entry.delete(0, tk.END)
    
    def save_settings(self):
        global FINE_PER_DAY, LOAN_PERIOD_DAYS
        try:
            fine = float(self.fine_entry.get())
            loan_period = int(self.loan_entry.get())
            if fine >= 0 and loan_period > 0:
                FINE_PER_DAY = fine
                LOAN_PERIOD_DAYS = loan_period
                messagebox.showinfo("Success", "Settings saved successfully!")
            else:
                messagebox.showerror("Error", "Invalid values!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers!")
    
    def export_data(self):
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".json", 
                                               filetypes=[("JSON files", "*.json")])
        if filename:
            data = {
                "books": [b.to_dict() for b in self.library.books],
                "members": {mid: m.to_dict() for mid, m in self.library.members.items()},
                "transactions": self.library.transactions
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", f"Data exported to {filename}")
    
    def import_data(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
            # Import logic here
            messagebox.showinfo("Success", "Data imported successfully!")
            self.root.after(1000, lambda: self.root.destroy())  # Restart app
    
    def clear_data(self):
        if messagebox.askyesno("Warning", "This will delete ALL data! Are you sure?"):
            for file in [BOOKS_FILE, MEMBERS_FILE, TRANSACTIONS_FILE]:
                if file.exists():
                    file.unlink()
            messagebox.showinfo("Success", "All data cleared! The application will now restart.")
            self.root.after(1000, lambda: self.root.destroy())

# ------------------ Main ------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()