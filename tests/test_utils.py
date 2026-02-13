# tests/test_utils.py
"""Unit tests for the utils module — hashing and date parsing."""

import unittest

from src.utils import hash_with_salt, parse_date_flexibly


class TestHashing(unittest.TestCase):
    """Tests for the password hashing helper."""

    def test_deterministic(self):
        """Same inputs always produce the same hash."""
        h1 = hash_with_salt("password", "salt123")
        h2 = hash_with_salt("password", "salt123")
        self.assertEqual(h1, h2)

    def test_different_salts(self):
        """Different salts produce different hashes."""
        h1 = hash_with_salt("password", "salt_a")
        h2 = hash_with_salt("password", "salt_b")
        self.assertNotEqual(h1, h2)

    def test_different_passwords(self):
        """Different passwords produce different hashes."""
        h1 = hash_with_salt("pass1", "same_salt")
        h2 = hash_with_salt("pass2", "same_salt")
        self.assertNotEqual(h1, h2)

    def test_returns_hex_string(self):
        """Hash output is a 64-char hex string (SHA-256)."""
        h = hash_with_salt("test", "salt")
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))


class TestDateParsing(unittest.TestCase):
    """Tests for the flexible date parser."""

    def test_yyyy_mm_dd(self):
        self.assertEqual(parse_date_flexibly("2026-01-15"), "2026-01-15")

    def test_dd_mm_yyyy_slash(self):
        self.assertEqual(parse_date_flexibly("15/01/2026"), "2026-01-15")

    def test_dd_mm_yyyy_dash(self):
        self.assertEqual(parse_date_flexibly("15-01-2026"), "2026-01-15")

    def test_dd_mm_yyyy_dot(self):
        self.assertEqual(parse_date_flexibly("15.01.2026"), "2026-01-15")

    def test_invalid_returns_none(self):
        self.assertIsNone(parse_date_flexibly("not-a-date"))


if __name__ == "__main__":
    unittest.main()
