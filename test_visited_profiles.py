"""
Automated Test Suite for Visited Profiles and My Activity Feature.
Tests database operations, tracking rules, automatic updates, and REST API endpoints.

Rules tested:
1. "Visited Profiles" displays account names whose posts the user has liked or saved.
2. Only liked and saved posts are tracked (no tracking for watched, reposted, shared, commented).
3. Sample accounts and posts exist, with some posts marked as liked/saved.
4. "Visited Profiles" updates automatically when posts are liked/saved/unliked/unsaved.
5. All REST API endpoints function as expected.
"""

import unittest
import os
import json
import sqlite3
import threading
import http.server
from urllib.request import urlopen, Request

import database
import app


class TestDatabaseVisitedProfiles(unittest.TestCase):
    """Test SQLite database operations and Visited Profiles business logic."""

    def setUp(self):
        """Reset database to fresh seed state before each test."""
        database.reset_db()

    def test_initial_seed_state(self):
        """Verify initial sample accounts, posts, likes, saves, and visited profiles."""
        accounts = database.get_accounts()
        posts = database.get_posts()
        liked = database.get_liked_posts()
        saved = database.get_saved_posts()
        visited = database.get_visited_profiles()

        # 6 sample accounts
        self.assertEqual(len(accounts), 6)
        # 7 sample posts
        self.assertEqual(len(posts), 7)
        # Initial liked posts: 3
        self.assertEqual(len(liked), 3)
        # Initial saved posts: 3
        self.assertEqual(len(saved), 3)

        # Visited Profiles count: 4
        # Accounts with liked or saved posts:
        # - culinary_arts (post 4 liked)
        # - nature.photographer (post 1 liked, post 2 saved)
        # - tech.pulse (post 3 liked & saved)
        # - wanderlust_diaries (post 5 saved)
        visited_usernames = [v["username"] for v in visited]
        self.assertEqual(len(visited), 4)
        self.assertIn("culinary_arts", visited_usernames)
        self.assertIn("nature.photographer", visited_usernames)
        self.assertIn("tech.pulse", visited_usernames)
        self.assertIn("wanderlust_diaries", visited_usernames)

        # Accounts NOT in Visited Profiles (neither liked nor saved):
        self.assertNotIn("urban_architecture", visited_usernames)
        self.assertNotIn("minimalist.design", visited_usernames)

    def test_like_post_adds_account_to_visited_profiles(self):
        """Liking a post from an unvisited account automatically adds it to Visited Profiles."""
        # Post 6 belongs to urban_architecture (initially neither liked nor saved)
        visited_before = [v["username"] for v in database.get_visited_profiles()]
        self.assertNotIn("urban_architecture", visited_before)

        # Like post 6
        updated = database.toggle_like(6)
        self.assertEqual(updated["is_liked"], 1)

        # Verify urban_architecture is now in Visited Profiles
        visited_after = database.get_visited_profiles()
        visited_usernames = [v["username"] for v in visited_after]
        self.assertIn("urban_architecture", visited_usernames)
        self.assertEqual(len(visited_after), len(visited_before) + 1)

        # Verify badge and counts
        urban_prof = next(v for v in visited_after if v["username"] == "urban_architecture")
        self.assertEqual(urban_prof["liked_count"], 1)
        self.assertEqual(urban_prof["saved_count"], 0)
        self.assertEqual(urban_prof["interaction_type"], "liked")

    def test_save_post_adds_account_to_visited_profiles(self):
        """Saving a post from an unvisited account automatically adds it to Visited Profiles."""
        # Post 7 belongs to minimalist.design (initially neither liked nor saved)
        visited_before = [v["username"] for v in database.get_visited_profiles()]
        self.assertNotIn("minimalist.design", visited_before)

        # Save post 7
        updated = database.toggle_save(7)
        self.assertEqual(updated["is_saved"], 1)

        # Verify minimalist.design is now in Visited Profiles
        visited_after = database.get_visited_profiles()
        visited_usernames = [v["username"] for v in visited_after]
        self.assertIn("minimalist.design", visited_usernames)
        self.assertEqual(len(visited_after), len(visited_before) + 1)

        # Verify badge and counts
        design_prof = next(v for v in visited_after if v["username"] == "minimalist.design")
        self.assertEqual(design_prof["saved_count"], 1)
        self.assertEqual(design_prof["liked_count"], 0)
        self.assertEqual(design_prof["interaction_type"], "saved")

    def test_unlike_removes_account_when_no_interactions_remain(self):
        """Unliking a post removes the account if it has no other liked or saved posts."""
        # culinary_arts only has post 4 liked (not saved)
        visited_before = [v["username"] for v in database.get_visited_profiles()]
        self.assertIn("culinary_arts", visited_before)

        # Unlike post 4
        updated = database.toggle_like(4)
        self.assertEqual(updated["is_liked"], 0)

        # Verify culinary_arts is automatically removed from Visited Profiles
        visited_after = [v["username"] for v in database.get_visited_profiles()]
        self.assertNotIn("culinary_arts", visited_after)

    def test_unsave_removes_account_when_no_interactions_remain(self):
        """Unsaving a post removes the account if it has no other liked or saved posts."""
        # wanderlust_diaries only has post 5 saved (not liked)
        visited_before = [v["username"] for v in database.get_visited_profiles()]
        self.assertIn("wanderlust_diaries", visited_before)

        # Unsave post 5
        updated = database.toggle_save(5)
        self.assertEqual(updated["is_saved"], 0)

        # Verify wanderlust_diaries is automatically removed from Visited Profiles
        visited_after = [v["username"] for v in database.get_visited_profiles()]
        self.assertNotIn("wanderlust_diaries", visited_after)

    def test_account_remains_if_still_saved_after_unlike(self):
        """If an account has a saved post, unliking its other post keeps the account in Visited Profiles."""
        # nature.photographer has post 1 (liked) and post 2 (saved)
        # Unlike post 1
        database.toggle_like(1)

        visited = database.get_visited_profiles()
        nature_prof = next((v for v in visited if v["username"] == "nature.photographer"), None)
        self.assertIsNotNone(nature_prof)
        self.assertEqual(nature_prof["liked_count"], 0)
        self.assertEqual(nature_prof["saved_count"], 1)
        self.assertEqual(nature_prof["interaction_type"], "saved")

        # Now unsave post 2
        database.toggle_save(2)
        visited_after = [v["username"] for v in database.get_visited_profiles()]
        self.assertNotIn("nature.photographer", visited_after)

    def test_single_post_both_liked_and_saved(self):
        """Post 3 (tech.pulse) is both liked and saved."""
        visited = database.get_visited_profiles()
        tech_prof = next(v for v in visited if v["username"] == "tech.pulse")
        self.assertEqual(tech_prof["liked_count"], 1)
        self.assertEqual(tech_prof["saved_count"], 1)
        self.assertEqual(tech_prof["interaction_type"], "liked_and_saved")
        self.assertEqual(tech_prof["badge_label"], "Liked & Saved")

    def test_post_removed_from_visited_profiles_on_undo(self):
        """Undo action (unlike/unsave) immediately removes the post from Visited Profiles, reflecting only updated state."""
        # 1. Like post 6 (urban_architecture)
        database.toggle_like(6)
        visited = database.get_visited_profiles()
        urban_prof = next((v for v in visited if v["username"] == "urban_architecture"), None)
        self.assertIsNotNone(urban_prof)
        self.assertIn(6, [p["id"] for p in urban_prof["posts"]])

        # 2. Undo like action: Unlike post 6
        database.toggle_like(6)
        visited_after = database.get_visited_profiles()
        # Post and profile are completely removed from Visited Profiles
        self.assertNotIn("urban_architecture", [v["username"] for v in visited_after])

    def test_no_tracking_for_other_activity(self):
        """Confirms that only is_liked and is_saved columns control Visited Profiles tracking."""
        # Ensure schema strictly enforces tracking boundaries
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(posts)")
        columns = [row["name"] for row in cursor.fetchall()]
        conn.close()

        # Columns include is_liked and is_saved
        self.assertIn("is_liked", columns)
        self.assertIn("is_saved", columns)
        # Do not include watched, reposted, shared, commented
        self.assertNotIn("is_watched", columns)
        self.assertNotIn("is_reposted", columns)
        self.assertNotIn("is_shared", columns)
        self.assertNotIn("is_commented", columns)


class TestApiEndpoints(unittest.TestCase):
    """Test HTTP API endpoints provided by app.py."""

    @classmethod
    def setUpClass(cls):
        """Start a test HTTP server on an ephemeral port."""
        database.reset_db()
        cls.server = http.server.HTTPServer(("127.0.0.1", 5001), app.InstagramRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:5001"

    @classmethod
    def tearDownClass(cls):
        """Shut down the test server."""
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        database.reset_db()

    def _get(self, path):
        req = Request(f"{self.base_url}{path}")
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path):
        req = Request(f"{self.base_url}{path}", data=b"", method="POST")
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_get_visited_profiles_api(self):
        """Test GET /api/activity/visited-profiles."""
        data = self._get("/api/activity/visited-profiles")
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 4)
        names = [p["username"] for p in data["data"]]
        self.assertIn("culinary_arts", names)
        self.assertIn("nature.photographer", names)
        self.assertIn("tech.pulse", names)
        self.assertIn("wanderlust_diaries", names)

    def test_get_liked_posts_api(self):
        """Test GET /api/activity/liked."""
        data = self._get("/api/activity/liked")
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 3)
        for post in data["data"]:
            self.assertEqual(post["is_liked"], 1)

    def test_get_saved_posts_api(self):
        """Test GET /api/activity/saved."""
        data = self._get("/api/activity/saved")
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 3)
        for post in data["data"]:
            self.assertEqual(post["is_saved"], 1)

    def test_get_posts_api(self):
        """Test GET /api/posts."""
        data = self._get("/api/posts")
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 7)

    def test_toggle_like_api(self):
        """Test POST /api/posts/<id>/toggle-like."""
        # Initially post 6 is unliked
        res = self._post("/api/posts/6/toggle-like")
        self.assertTrue(res["success"])
        self.assertEqual(res["post"]["is_liked"], 1)
        self.assertEqual(res["visited_profiles_count"], 5)

        # Toggle again to unlike
        res2 = self._post("/api/posts/6/toggle-like")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["post"]["is_liked"], 0)
        self.assertEqual(res2["visited_profiles_count"], 4)

    def test_toggle_save_api(self):
        """Test POST /api/posts/<id>/toggle-save."""
        # Initially post 7 is unsaved
        res = self._post("/api/posts/7/toggle-save")
        self.assertTrue(res["success"])
        self.assertEqual(res["post"]["is_saved"], 1)
        self.assertEqual(res["visited_profiles_count"], 5)

        # Toggle again to unsave
        res2 = self._post("/api/posts/7/toggle-save")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["post"]["is_saved"], 0)
        self.assertEqual(res2["visited_profiles_count"], 4)

    def test_reset_api(self):
        """Test POST /api/reset."""
        # Like post 6
        self._post("/api/posts/6/toggle-like")
        self.assertEqual(len(self._get("/api/activity/visited-profiles")["data"]), 5)

        # Call reset
        res = self._post("/api/reset")
        self.assertTrue(res["success"])
        self.assertEqual(len(self._get("/api/activity/visited-profiles")["data"]), 4)


if __name__ == "__main__":
    unittest.main()
