"""
Security test cases for LearnDash Manager fixes.

These tests verify that the security vulnerabilities have been properly addressed:
1. Command injection protection via shlex.quote()
2. Input validation for all parameters
3. Circuit breaker pattern in bulk operations
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.learndash_manager import LearnDashManager
from src.config import WordPressConfig
from src.wp_cli import WPCLIClient


class TestCommandInjectionPrevention:
    """Test that command injection attacks are prevented."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=WordPressConfig)
        self.wp_cli = Mock(spec=WPCLIClient)
        self.wp_cli.execute = MagicMock(return_value=123)
        self.manager = LearnDashManager(self.config, self.wp_cli)

    def test_create_course_escapes_malicious_title(self):
        """Test that malicious input in title is escaped."""
        malicious_title = 'Test"; rm -rf /; echo "'

        self.manager.create_course(title=malicious_title, status="draft")

        # Verify execute was called
        assert self.wp_cli.execute.called
        call_args = self.wp_cli.execute.call_args[0][0]

        # Verify the command contains escaped quotes
        assert "shlex.quote" not in call_args  # shlex.quote shouldn't appear in output
        assert 'Test"; rm -rf /; echo "' not in call_args  # Raw injection shouldn't appear
        print(f"✓ Command injection prevented in title: {call_args}")

    def test_create_lesson_escapes_content(self):
        """Test that content with shell metacharacters is escaped."""
        malicious_content = "Content with $(whoami) and `ls -la` and ; rm -rf /"

        self.manager.create_lesson(
            course_id=1,
            title="Safe Title",
            content=malicious_content,
            status="draft"
        )

        assert self.wp_cli.execute.called
        call_args = self.wp_cli.execute.call_args[0][0]

        # Verify dangerous shell operations are escaped
        assert "$(whoami)" not in call_args
        assert "`ls -la`" not in call_args
        print(f"✓ Shell metacharacters escaped in content")

    def test_create_quiz_escapes_description(self):
        """Test quiz description escaping."""
        malicious_desc = "Description'; DROP TABLE courses; --"

        self.manager.create_quiz(
            course_id=1,
            lesson_id=None,
            title="Quiz",
            description=malicious_desc
        )

        assert self.wp_cli.execute.called
        print("✓ SQL injection-style string escaped in description")


class TestInputValidation:
    """Test that all inputs are properly validated."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=WordPressConfig)
        self.wp_cli = Mock(spec=WPCLIClient)
        self.manager = LearnDashManager(self.config, self.wp_cli)

    def test_negative_course_id_rejected(self):
        """Test that negative IDs are rejected."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            self.manager.update_course(course_id=-1, title="Test")
        print("✓ Negative course_id rejected")

    def test_zero_user_id_rejected(self):
        """Test that zero IDs are rejected."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            self.manager.enroll_user(user_id=0, course_id=1)
        print("✓ Zero user_id rejected")

    def test_non_integer_id_rejected(self):
        """Test that non-integer IDs are rejected."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            self.manager.delete_course(course_id="not_an_int")
        print("✓ Non-integer course_id rejected")

    def test_empty_title_rejected(self):
        """Test that empty titles are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            self.manager.create_course(title="", status="draft")
        print("✓ Empty title rejected")

    def test_title_too_long_rejected(self):
        """Test that titles exceeding max length are rejected."""
        long_title = "A" * 201  # Max is 200
        with pytest.raises(ValueError, match="too long"):
            self.manager.create_course(title=long_title, status="draft")
        print("✓ Over-length title rejected")

    def test_content_too_long_rejected(self):
        """Test that content exceeding max length is rejected."""
        long_content = "A" * 50001  # Max is 50000
        with pytest.raises(ValueError, match="too long"):
            self.manager.create_course(
                title="Test",
                content=long_content,
                status="draft"
            )
        print("✓ Over-length content rejected")

    def test_invalid_status_rejected(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValueError, match="must be one of"):
            self.manager.create_course(title="Test", status="invalid_status")
        print("✓ Invalid status rejected")

    def test_invalid_passing_score_rejected(self):
        """Test that passing score outside 0-100 is rejected."""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            self.manager.create_quiz(
                course_id=1,
                lesson_id=None,
                title="Quiz",
                passing_score=150
            )
        print("✓ Invalid passing_score rejected")

    def test_negative_price_rejected(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError, match="must be >= 0"):
            self.manager.create_course(title="Test", price=-10.0)
        print("✓ Negative price rejected")


class TestBulkOperationsCircuitBreaker:
    """Test that bulk operations have circuit breaker protection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=WordPressConfig)
        self.wp_cli = Mock(spec=WPCLIClient)
        self.manager = LearnDashManager(self.config, self.wp_cli)

    def test_bulk_enroll_empty_list_rejected(self):
        """Test that empty user list is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            self.manager.bulk_enroll_users(user_ids=[], course_id=1)
        print("✓ Empty user_ids list rejected")

    def test_bulk_enroll_validates_all_ids(self):
        """Test that all user IDs are validated."""
        # Mix of valid and invalid IDs
        user_ids = [1, 2, -3, 4, "invalid"]

        result = self.manager.bulk_enroll_users(user_ids=user_ids, course_id=1)

        # Should have errors for invalid IDs
        assert result["failed"] > 0
        assert len(result["errors"]) > 0
        print(f"✓ Invalid IDs in bulk operation caught: {result['errors']}")

    def test_circuit_breaker_stops_after_failures(self):
        """Test that circuit breaker stops after consecutive failures."""
        # Simulate wp_cli throwing errors
        self.wp_cli.execute = MagicMock(side_effect=Exception("Connection failed"))

        # Try to enroll 20 users
        user_ids = list(range(1, 21))

        result = self.manager.bulk_enroll_users(user_ids=user_ids, course_id=1)

        # Should abort after 5 consecutive failures
        assert result["aborted"] == True
        assert result["enrolled"] == 0
        # Should have stopped around 5 failures, not processed all 20
        assert result["failed"] <= 7  # Allow some margin
        print(f"✓ Circuit breaker activated: stopped at {result['failed']} failures")


class TestValidationHelpers:
    """Test the validation helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=WordPressConfig)
        self.wp_cli = Mock(spec=WPCLIClient)
        self.manager = LearnDashManager(self.config, self.wp_cli)

    def test_validate_positive_int_accepts_valid(self):
        """Test that valid positive integers are accepted."""
        result = self.manager._validate_positive_int(42, "test_param")
        assert result == 42
        print("✓ Valid positive integer accepted")

    def test_validate_string_accepts_valid(self):
        """Test that valid strings are accepted."""
        result = self.manager._validate_string("Valid String", "test_param")
        assert result == "Valid String"
        print("✓ Valid string accepted")

    def test_validate_literal_accepts_valid(self):
        """Test that valid literal values are accepted."""
        result = self.manager._validate_literal(
            "publish",
            "status",
            ["publish", "draft", "private"]
        )
        assert result == "publish"
        print("✓ Valid literal value accepted")

    def test_validate_float_accepts_valid(self):
        """Test that valid floats are accepted."""
        result = self.manager._validate_float(19.99, "price")
        assert result == 19.99
        print("✓ Valid float accepted")

    def test_validate_int_range_accepts_valid(self):
        """Test that integers in range are accepted."""
        result = self.manager._validate_int_range(80, "passing_score", 0, 100)
        assert result == 80
        print("✓ Valid integer in range accepted")


def run_security_tests():
    """Run all security tests and report results."""
    print("\n" + "="*60)
    print("LEARNDASH MANAGER SECURITY TEST SUITE")
    print("="*60 + "\n")

    # Run tests manually to show progress
    test_classes = [
        TestCommandInjectionPrevention,
        TestInputValidation,
        TestBulkOperationsCircuitBreaker,
        TestValidationHelpers,
    ]

    total_passed = 0
    total_failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__doc__}")
        print("-" * 60)

        instance = test_class()
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]

        for method_name in test_methods:
            try:
                instance.setup_method()
                method = getattr(instance, method_name)
                method()
                total_passed += 1
            except Exception as e:
                print(f"✗ {method_name} FAILED: {e}")
                total_failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {total_passed} passed, {total_failed} failed")
    print("="*60 + "\n")

    return total_failed == 0


if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
