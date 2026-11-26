CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    author VARCHAR(120) NOT NULL,
    category VARCHAR(80),
    total_copies INT NOT NULL,
    available_copies INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (total_copies >= 1),
    CHECK (available_copies >= 0),
    CHECK (available_copies <= total_copies)
);

CREATE TABLE IF NOT EXISTS members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    joined_on DATE NOT NULL DEFAULT (CURRENT_DATE)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    status ENUM('ISSUED','RETURNED') NOT NULL DEFAULT 'ISSUED',
    fine DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_tx_member FOREIGN KEY (member_id)
        REFERENCES members(member_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tx_book FOREIGN KEY (book_id)
        REFERENCES books(book_id) ON DELETE RESTRICT
);

CREATE INDEX idx_transaction_status ON transactions(status);
CREATE INDEX idx_transaction_due_date ON transactions(due_date);

INSERT INTO books(title, author, category, total_copies, available_copies) VALUES
('Python Crash Course', 'Eric Matthes', 'Programming', 5, 5),
('Database System Concepts', 'Silberschatz', 'Database', 3, 3),
('Clean Code', 'Robert C. Martin', 'Software Engineering', 4, 4);

INSERT INTO members(name, email, phone) VALUES
('Rahul Kumar', 'rahul@example.com', '9876543210'),
('Priya Sharma', 'priya@example.com', '9876501234');
