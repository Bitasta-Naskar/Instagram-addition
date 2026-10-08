# Instagram Activity Tracker • Visited Profiles Feature

This repository implements the **"Visited Profiles"** feature under **"My Activity"**, alongside the existing **"Saved"** and **"Liked"** sections.

---

## 🎯 Feature Overview

Under **"My Activity"**, users can navigate between three core sections:
1. **Liked**: Displays posts the user has liked, with options to unlike.
2. **Saved**: Displays posts the user has saved, with options to unsave.
3. **Visited Profiles** *(New Feature)*: Displays the account names whose posts the user has liked or saved.

### 📌 Business Rules & Tracking Criteria
- **Tracked Interactions**: Tracks **only** accounts whose posts the user has **liked** or **saved**.
- **Excluded Interactions**: Per requirements, tracking is **not** implemented for watched, reposted, shared, or commented posts.
- **Automatic Dynamic Updates**:
  - Liking or saving a post immediately adds the author's account to **Visited Profiles** (if not already present).
  - Unliking or unsaving a post automatically recalculates the list. If no liked or saved posts remain for that account, the account is automatically removed from **Visited Profiles**.
  - If an account has multiple posts (or a post with both like and save), removing one interaction keeps the account tracked as long as another interaction remains.

---

## 🗄️ Database Design

The database is built using **SQLite** with the following schema:

### `accounts` Table
Stores user account profiles.
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    avatar_url TEXT NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `posts` Table
Stores posts associated with accounts and user interaction flags (`is_liked`, `is_saved`).
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    caption TEXT NOT NULL,
    image_url TEXT NOT NULL,
    is_liked INTEGER NOT NULL DEFAULT 0 CHECK (is_liked IN (0, 1)),
    is_saved INTEGER NOT NULL DEFAULT 0 CHECK (is_saved IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
```

### 🔍 Visited Profiles Query
The Visited Profiles section queries accounts based on the interaction condition:
```sql
SELECT 
    a.id,
    a.username,
    a.full_name,
    a.avatar_url,
    a.bio,
    SUM(CASE WHEN p.is_liked = 1 THEN 1 ELSE 0 END) AS liked_count,
    SUM(CASE WHEN p.is_saved = 1 THEN 1 ELSE 0 END) AS saved_count,
    MAX(p.created_at) AS last_interaction_at
FROM accounts a
JOIN posts p ON a.id = p.account_id
WHERE p.is_liked = 1 OR p.is_saved = 1
GROUP BY a.id, a.username, a.full_name, a.avatar_url, a.bio
ORDER BY a.username ASC;
```

---

## 📊 Sample Seed Data

The database comes pre-seeded with 6 accounts and 7 posts:

| Account | Initial Liked Posts | Initial Saved Posts | Initial Visited Profiles Status |
| :--- | :---: | :---: | :--- |
| `@culinary_arts` | 1 | 0 | **Tracked** (Interaction: Liked) |
| `@nature.photographer` | 1 | 1 | **Tracked** (Interaction: Liked & Saved) |
| `@tech.pulse` | 1 | 1 | **Tracked** (Interaction: Liked & Saved) |
| `@wanderlust_diaries` | 0 | 1 | **Tracked** (Interaction: Saved) |
| `@urban_architecture` | 0 | 0 | *Not tracked* (neither liked nor saved) |
| `@minimalist.design` | 0 | 0 | *Not tracked* (neither liked nor saved) |

---

## 🚀 Running the Application

The application has **zero external dependencies** and uses Python's built-in standard library (`sqlite3`, `http.server`).

### 1. Start the Server
```bash
python app.py
```
By default, the server runs on port **5000**. To specify a custom port:
```bash
python app.py 8000
```

### 2. Open in Browser
Visit [http://localhost:5000](http://localhost:5000) to view the interactive interface:
- Navigate to **"Visited Profiles"** under **"My Activity"** to see currently tracked accounts.
- Switch to **"Liked"** or **"Saved"** to view and manage liked/saved posts.
- Switch to **"Explore Posts"** to like/save posts from `@urban_architecture` or `@minimalist.design`, and observe them automatically appear in **Visited Profiles**!
- Click **"Reset Sample Data"** in the header anytime to revert to the initial seed state.

---

## 🧪 Running Automated Tests

Run the full automated test suite covering database queries, edge cases, and REST API routes:

```bash
python -m unittest test_visited_profiles.py -v
```

### Test Coverage Highlights:
- ✅ Initial sample accounts and posts verification.
- ✅ Correct query filtering: only accounts with liked or saved posts appear in Visited Profiles.
- ✅ Dynamic addition to Visited Profiles upon liking a post.
- ✅ Dynamic addition to Visited Profiles upon saving a post.
- ✅ Dynamic removal from Visited Profiles when all liked/saved posts are unliked/unsaved.
- ✅ Persistence in Visited Profiles if an account has remaining saved posts after unliking.
- ✅ Accounts with both liked and saved posts properly tagged.
- ✅ Verification that watched/reposted/commented posts are not tracked.
- ✅ All REST API endpoints (`/api/activity/visited-profiles`, `/api/activity/liked`, `/api/activity/saved`, `/api/posts`, `/api/posts/<id>/toggle-like`, `/api/posts/<id>/toggle-save`, `/api/reset`).

---

## 📁 Project Structure

```
Instagram-addition/
├── app.py                      # HTTP server & REST API routes (Standard library)
├── database.py                 # SQLite database schema, seed data, queries
├── test_visited_profiles.py    # Comprehensive automated test suite
├── instagram.db                # SQLite database file
├── README.md                   # Project documentation
└── static/
    ├── index.html              # HTML structure with My Activity sections
    ├── style.css               # Modern Instagram-inspired CSS
    └── app.js                  # Frontend state management & live updates
```
