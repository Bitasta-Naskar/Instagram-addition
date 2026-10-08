"""
Database module for Instagram Activity Tracker.
Manages accounts, posts, likes, saves, and computes Visited Profiles.

Tracking Rule:
- Visited Profiles tracks ONLY accounts whose posts the user has liked or saved.
- Watched, reposted, shared, or commented posts are NOT tracked.
- Visited Profiles updates automatically when posts are liked or saved.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed: bool = True) -> None:
    """Initializes the database tables and populates sample data if requested."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Accounts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        avatar_url TEXT NOT NULL,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create Posts Table
    # Tracks is_liked and is_saved for the current user.
    # Watched, reposted, shared, commented are explicitly NOT tracked.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        caption TEXT NOT NULL,
        image_url TEXT NOT NULL,
        is_liked INTEGER NOT NULL DEFAULT 0 CHECK (is_liked IN (0, 1)),
        is_saved INTEGER NOT NULL DEFAULT 0 CHECK (is_saved IN (0, 1)),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    if seed:
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] == 0:
            seed_sample_data(conn)

    conn.close()


def seed_sample_data(conn: Optional[sqlite3.Connection] = None) -> None:
    """Seeds sample accounts and posts with initial liked and saved states."""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts")
    cursor.execute("DELETE FROM accounts")

    # Sample Accounts
    accounts_data = [
        (
            1,
            "nature.photographer",
            "Elena Rostova",
            "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
            "Landscape & wilderness photographer capturing quiet moments in nature 🌲🏔️"
        ),
        (
            2,
            "tech.pulse",
            "Alex Rivera",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
            "Minimalist workspace aesthetics & creative technology tools 💻⚡"
        ),
        (
            3,
            "culinary_arts",
            "Chef Marco",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "Artisan sourdough baker & modern seasonal gastronomy 🥖🍳"
        ),
        (
            4,
            "urban_architecture",
            "Maya Lin Studio",
            "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80",
            "Exploring brutalist geometry, modern textures & urban skylines 🏙️"
        ),
        (
            5,
            "wanderlust_diaries",
            "Sophie & Liam",
            "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80",
            "Full-time nomadic storytellers journeying through coastal escapes ✈️🌊"
        ),
        (
            6,
            "minimalist.design",
            "Studio Mono",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
            "Visual identity, Scandinavian interiors & typography studies 📐🖤"
        )
    ]

    cursor.executemany("""
    INSERT INTO accounts (id, username, full_name, avatar_url, bio)
    VALUES (?, ?, ?, ?, ?)
    """, accounts_data)

    # Sample Posts:
    # Notice:
    # Post 1 (nature.photographer): liked = 1, saved = 0 -> In Visited Profiles (liked)
    # Post 2 (nature.photographer): liked = 0, saved = 1 -> In Visited Profiles (saved)
    # Post 3 (tech.pulse): liked = 1, saved = 1 -> In Visited Profiles (liked & saved)
    # Post 4 (culinary_arts): liked = 1, saved = 0 -> In Visited Profiles (liked)
    # Post 5 (wanderlust_diaries): liked = 0, saved = 1 -> In Visited Profiles (saved)
    # Post 6 (urban_architecture): liked = 0, saved = 0 -> NOT in Visited Profiles
    # Post 7 (minimalist.design): liked = 0, saved = 0 -> NOT in Visited Profiles
    posts_data = [
        (
            1,
            1,  # nature.photographer
            "Morning mist settling over the misty alpine pine forest at dawn. The crisp mountain air was unforgettable. 🌲✨",
            "https://images.unsplash.com/photo-1511497584788-87676104235f?w=800&auto=format&fit=crop&q=80",
            1,  # is_liked
            0   # is_saved
        ),
        (
            2,
            1,  # nature.photographer
            "Sunset reflections creating a glass mirror across Lake Emerald. Serenity in its purest form. 🌅",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
            0,  # is_liked
            1   # is_saved
        ),
        (
            3,
            2,  # tech.pulse
            "Clean walnut desk setup with custom mechanical keyboard and ambient backlighting. Productivity sanctuary. 💻⚡",
            "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&auto=format&fit=crop&q=80",
            1,  # is_liked
            1   # is_saved
        ),
        (
            4,
            3,  # culinary_arts
            "Freshly baked wild yeast sourdough bread with golden crispy crust and open crumb. Best served warm with sea salt butter. 🥖🧈",
            "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&auto=format&fit=crop&q=80",
            1,  # is_liked
            0   # is_saved
        ),
        (
            5,
            5,  # wanderlust_diaries
            "Walking through narrow whitewashed alleys draped in blooming pink bougainvillea in Oia, Santorini. 🇬🇷🌊",
            "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800&auto=format&fit=crop&q=80",
            0,  # is_liked
            1   # is_saved
        ),
        (
            6,
            4,  # urban_architecture
            "Geometric concrete overhangs colliding with tinted glass reflections in downtown Tokyo. Brutalist elegance. 🏙️",
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&auto=format&fit=crop&q=80",
            0,  # is_liked
            0   # is_saved
        ),
        (
            7,
            6,  # minimalist.design
            "Warm afternoon light casting shadows in this Nordic minimalist living space. Less is always more. 🛋️📐",
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80",
            0,  # is_liked
            0   # is_saved
        )
    ]

    cursor.executemany("""
    INSERT INTO posts (id, account_id, caption, image_url, is_liked, is_saved)
    VALUES (?, ?, ?, ?, ?, ?)
    """, posts_data)

    conn.commit()
    if should_close:
        conn.close()


def get_accounts() -> List[Dict[str, Any]]:
    """Returns all accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_posts() -> List[Dict[str, Any]]:
    """Returns all posts with author account information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        p.id,
        p.account_id,
        p.caption,
        p.image_url,
        p.is_liked,
        p.is_saved,
        p.created_at,
        a.username,
        a.full_name,
        a.avatar_url
    FROM posts p
    JOIN accounts a ON p.account_id = a.id
    ORDER BY p.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_liked_posts() -> List[Dict[str, Any]]:
    """
    Returns all posts liked by the user (My Activity -> Liked).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        p.id,
        p.account_id,
        p.caption,
        p.image_url,
        p.is_liked,
        p.is_saved,
        p.created_at,
        a.username,
        a.full_name,
        a.avatar_url
    FROM posts p
    JOIN accounts a ON p.account_id = a.id
    WHERE p.is_liked = 1
    ORDER BY p.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_saved_posts() -> List[Dict[str, Any]]:
    """
    Returns all posts saved by the user (My Activity -> Saved).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        p.id,
        p.account_id,
        p.caption,
        p.image_url,
        p.is_liked,
        p.is_saved,
        p.created_at,
        a.username,
        a.full_name,
        a.avatar_url
    FROM posts p
    JOIN accounts a ON p.account_id = a.id
    WHERE p.is_saved = 1
    ORDER BY p.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_visited_profiles() -> List[Dict[str, Any]]:
    """
    Returns the account names whose posts the user has liked or saved.
    (My Activity -> Visited Profiles)

    Rule:
    - Tracks ONLY accounts where at least one post has is_liked = 1 OR is_saved = 1.
    - Watched, reposted, shared, or commented posts are NOT tracked.
    - Automatically updates based on liked/saved posts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
    ORDER BY a.username ASC
    """)
    rows = []
    raw_accounts = cursor.fetchall()
    for r in raw_accounts:
        item = dict(r)
        liked_c = item["liked_count"]
        saved_c = item["saved_count"]
        if liked_c > 0 and saved_c > 0:
            item["interaction_type"] = "liked_and_saved"
            item["badge_label"] = "Liked & Saved"
        elif liked_c > 0:
            item["interaction_type"] = "liked"
            item["badge_label"] = "Liked"
        else:
            item["interaction_type"] = "saved"
            item["badge_label"] = "Saved"

        # Fetch only active liked/saved posts for this profile
        # So undoing like/save removes the post from this section immediately
        cursor.execute("""
        SELECT id, caption, image_url, is_liked, is_saved, created_at
        FROM posts
        WHERE account_id = ? AND (is_liked = 1 OR is_saved = 1)
        ORDER BY id DESC
        """, (item["id"],))
        item["posts"] = [dict(p) for p in cursor.fetchall()]

        rows.append(item)
    conn.close()
    return rows


def toggle_like(post_id: int) -> Optional[Dict[str, Any]]:
    """
    Toggles the is_liked status for the specified post.
    Automatically impacts Visited Profiles if no other interactions remain.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_liked, is_saved, account_id FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    new_liked = 0 if row["is_liked"] == 1 else 1
    cursor.execute("UPDATE posts SET is_liked = ? WHERE id = ?", (new_liked, post_id))
    conn.commit()

    cursor.execute("""
    SELECT 
        p.id,
        p.account_id,
        p.caption,
        p.image_url,
        p.is_liked,
        p.is_saved,
        a.username
    FROM posts p
    JOIN accounts a ON p.account_id = a.id
    WHERE p.id = ?
    """, (post_id,))
    updated_post = dict(cursor.fetchone())
    conn.close()
    return updated_post


def toggle_save(post_id: int) -> Optional[Dict[str, Any]]:
    """
    Toggles the is_saved status for the specified post.
    Automatically impacts Visited Profiles if no other interactions remain.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_liked, is_saved, account_id FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    new_saved = 0 if row["is_saved"] == 1 else 1
    cursor.execute("UPDATE posts SET is_saved = ? WHERE id = ?", (new_saved, post_id))
    conn.commit()

    cursor.execute("""
    SELECT 
        p.id,
        p.account_id,
        p.caption,
        p.image_url,
        p.is_liked,
        p.is_saved,
        a.username
    FROM posts p
    JOIN accounts a ON p.account_id = a.id
    WHERE p.id = ?
    """, (post_id,))
    updated_post = dict(cursor.fetchone())
    conn.close()
    return updated_post


def reset_db() -> None:
    """Resets the database to initial sample data."""
    init_db(seed=False)
    seed_sample_data()


if __name__ == "__main__":
    init_db(seed=True)
    print("Database initialized successfully.")
    print(f"Sample accounts: {len(get_accounts())}")
    print(f"Sample posts: {len(get_posts())}")
    print(f"Liked posts: {len(get_liked_posts())}")
    print(f"Saved posts: {len(get_saved_posts())}")
    visited = get_visited_profiles()
    print(f"Visited Profiles count: {len(visited)}")
    print("Visited Profile account names:")
    for v in visited:
        print(f"  - @{v['username']} ({v['badge_label']}: {v['liked_count']} liked, {v['saved_count']} saved)")
