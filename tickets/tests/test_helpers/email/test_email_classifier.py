"""Tests for the email classifier."""

from django.test import TestCase
from tickets.helpers.email.email_classifier import (
    classify_email,
    match_keywords,
)
from tickets.helpers.email.email_keywords import FACULTY_KEYWORDS


class MatchKeywordsTest(TestCase):

    def test_returns_best_match(self):
        result = match_keywords(
            "I study computer science and engineering", FACULTY_KEYWORDS
        )
        self.assertEqual(result, "nmes")

    def test_returns_none_when_no_match(self):
        result = match_keywords("hello world", FACULTY_KEYWORDS)
        self.assertIsNone(result)

    def test_case_insensitive(self):
        result = match_keywords("COMPUTER SCIENCE", FACULTY_KEYWORDS)
        self.assertEqual(result, "nmes")


class ClassifyEmailTest(TestCase):

    def test_all_fields_detected(self):
        result = classify_email(
            "Assessment deadline extension",
            "I am an undergraduate in computer science and need an extension.",
        )
        self.assertEqual(result["faculty"], "nmes")
        self.assertEqual(result["study_level"], "undergraduate")
        self.assertEqual(result["category"], "assessment")

    def test_faculty_not_detected(self):
        result = classify_email("Assessment issue", "I am an undergraduate student.")
        self.assertIsNone(result["faculty"])
        self.assertEqual(result["study_level"], "undergraduate")
        self.assertEqual(result["category"], "assessment")

    def test_study_level_not_detected(self):
        result = classify_email(
            "Business school exam", "I have a question about my exam."
        )
        self.assertEqual(result["faculty"], "kbs")
        self.assertIsNone(result["study_level"])
        self.assertEqual(result["category"], "assessment")

    def test_category_not_detected(self):
        result = classify_email("Question about KBS", "I am an undergraduate.")
        self.assertEqual(result["faculty"], "kbs")
        self.assertEqual(result["study_level"], "undergraduate")
        self.assertIsNone(result["category"])

    def test_nothing_detected(self):
        result = classify_email("Hello", "Just wanted to say hi.")
        self.assertIsNone(result["faculty"])
        self.assertIsNone(result["study_level"])
        self.assertIsNone(result["category"])

    def test_phd_detected_as_postgraduate_research(self):
        result = classify_email(
            "PhD funding question",
            "I am a PhD student in psychiatry and neuroscience.",
        )
        self.assertEqual(result["study_level"], "postgraduate_research")
        self.assertEqual(result["faculty"], "ioppn")

    def test_housing_category(self):
        result = classify_email(
            "Accommodation issue", "I need help with my halls of residence."
        )
        self.assertEqual(result["category"], "housing_and_accommodation_support")

    def test_visa_category(self):
        result = classify_email(
            "Visa question", "I am an international student needing immigration advice."
        )
        self.assertEqual(result["category"], "visas_immigration_and_support")

    def test_law_faculty(self):
        result = classify_email(
            "Legal studies question", "I study law at Dickson Poon."
        )
        self.assertEqual(result["faculty"], "dpsol")
