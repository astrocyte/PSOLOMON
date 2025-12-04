"""LearnDash LMS management for course creation and editing."""

import json
import shlex
import logging
from typing import Optional, Literal, Union, Any
from .config import WordPressConfig
from .wp_cli import WPCLIClient


class LearnDashManager:
    """Manage LearnDash courses, lessons, quizzes, and enrollments."""

    def __init__(self, config: WordPressConfig, wp_cli: WPCLIClient):
        self.config = config
        self.cli = wp_cli
        self.logger = logging.getLogger(__name__)

    # ==================== VALIDATION HELPERS ====================

    def _validate_positive_int(self, value: Any, name: str) -> int:
        """
        Validate and return positive integer.

        Args:
            value: Value to validate
            name: Parameter name for error messages

        Returns:
            Validated integer

        Raises:
            ValueError: If value is not a positive integer
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer, got {value}")
        return value

    def _validate_string(
        self,
        value: Any,
        name: str,
        max_length: Optional[int] = None,
        allow_empty: bool = False,
    ) -> str:
        """
        Validate and return string.

        Args:
            value: Value to validate
            name: Parameter name for error messages
            max_length: Maximum allowed length (optional)
            allow_empty: Whether empty strings are allowed

        Returns:
            Validated string

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string, got {type(value).__name__}")

        if not allow_empty and not value.strip():
            raise ValueError(f"{name} cannot be empty")

        if max_length and len(value) > max_length:
            raise ValueError(
                f"{name} too long (max {max_length} chars, got {len(value)})"
            )

        return value

    def _validate_literal(
        self, value: Any, name: str, allowed_values: list[str]
    ) -> str:
        """
        Validate that value is one of allowed literal values.

        Args:
            value: Value to validate
            name: Parameter name for error messages
            allowed_values: List of allowed values

        Returns:
            Validated value

        Raises:
            ValueError: If value not in allowed values
        """
        if value not in allowed_values:
            raise ValueError(
                f"{name} must be one of {allowed_values}, got {value}"
            )
        return value

    def _validate_float(self, value: Any, name: str, min_value: float = 0.0) -> float:
        """
        Validate and return float.

        Args:
            value: Value to validate
            name: Parameter name for error messages
            min_value: Minimum allowed value

        Returns:
            Validated float

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number, got {type(value).__name__}")

        value = float(value)
        if value < min_value:
            raise ValueError(f"{name} must be >= {min_value}, got {value}")

        return value

    def _validate_int_range(
        self, value: Any, name: str, min_value: int, max_value: int
    ) -> int:
        """
        Validate integer is within range.

        Args:
            value: Value to validate
            name: Parameter name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, int):
            raise ValueError(f"{name} must be an integer, got {type(value).__name__}")

        if value < min_value or value > max_value:
            raise ValueError(
                f"{name} must be between {min_value} and {max_value}, got {value}"
            )

        return value

    def _get_meta(self, post_id: int, meta_key: str) -> Optional[str]:
        """
        Get post meta value.

        Args:
            post_id: Post ID
            meta_key: Meta key to retrieve

        Returns:
            Meta value or None if not found
        """
        try:
            # Security: Quote all parameters to prevent command injection
            cmd = f'post meta get {shlex.quote(str(post_id))} {shlex.quote(meta_key)}'
            result = self.cli.execute(cmd)
            return result if result else None
        except Exception:
            return None

    # ==================== COURSE MANAGEMENT ====================

    def create_course(
        self,
        title: str,
        content: str = "",
        status: Literal["publish", "draft", "private"] = "draft",
        price: Optional[float] = None,
        certificate_id: Optional[int] = None,
    ) -> dict:
        """
        Create a new LearnDash course.

        Args:
            title: Course title
            content: Course description/content
            status: Post status (publish, draft, private)
            price: Course price (optional)
            certificate_id: Certificate template ID (optional)

        Returns:
            Created course data with ID

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        title = self._validate_string(title, "title", max_length=200)
        if content:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        status = self._validate_literal(status, "status", ["publish", "draft", "private"])
        if price is not None:
            price = self._validate_float(price, "price", min_value=0.0)
        if certificate_id is not None:
            certificate_id = self._validate_positive_int(certificate_id, "certificate_id")

        # Create course post with properly escaped values
        cmd = f'post create --post_type=sfwd-courses --post_title={shlex.quote(title)} --post_status={status}'

        if content:
            cmd += f' --post_content={shlex.quote(content)}'

        result = self.cli.execute(cmd, format="json")
        course_id = result if isinstance(result, int) else int(result)

        # Set course meta (Security: quote all parameters)
        if price is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(course_id))} {shlex.quote("_sfwd-courses")} '
                f'{shlex.quote("_sfwd-courses[sfwd-courses_course_price]")} {shlex.quote(str(price))}'
            )

        if certificate_id:
            self.cli.execute(
                f'post meta update {shlex.quote(str(course_id))} {shlex.quote("_sfwd-courses")} '
                f'{shlex.quote("_sfwd-courses[sfwd-courses_certificate]")} {shlex.quote(str(certificate_id))}'
            )

        self.logger.info(f"Created course {course_id}: {title}")

        return {
            "id": course_id,
            "title": title,
            "status": status,
            "type": "course",
            "price": price,
        }

    def update_course(
        self,
        course_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        price: Optional[float] = None,
    ) -> dict:
        """
        Update an existing course.

        Args:
            course_id: Course post ID
            title: New title (optional)
            content: New content (optional)
            status: New status (optional)
            price: New price (optional)

        Returns:
            Updated course data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")
        if title is not None:
            title = self._validate_string(title, "title", max_length=200)
        if content is not None:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        if status is not None:
            status = self._validate_literal(
                status, "status", ["publish", "draft", "private"]
            )
        if price is not None:
            price = self._validate_float(price, "price", min_value=0.0)

        updates = []

        if title:
            updates.append(f'--post_title={shlex.quote(title)}')
        if content is not None:
            updates.append(f'--post_content={shlex.quote(content)}')
        if status:
            updates.append(f'--post_status={status}')

        if updates:
            cmd = f'post update {shlex.quote(str(course_id))} {" ".join(updates)}'
            self.cli.execute(cmd)

        if price is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(course_id))} {shlex.quote("_sfwd-courses")} '
                f'{shlex.quote("_sfwd-courses[sfwd-courses_course_price]")} {shlex.quote(str(price))}'
            )

        self.logger.info(f"Updated course {course_id}")

        return {"id": course_id, "updated": True}

    def list_courses(self, status: str = "any", limit: int = 50) -> list[dict]:
        """
        List all LearnDash courses.

        Args:
            status: Post status filter (any, publish, draft)
            limit: Maximum number to return

        Returns:
            List of courses with metadata
        """
        return self.cli.list_posts(
            post_type="sfwd-courses",
            post_status=status,
            limit=limit
        )

    def delete_course(self, course_id: int, force: bool = False) -> dict:
        """
        Delete a course.

        Args:
            course_id: Course post ID
            force: Permanently delete (bypass trash)

        Returns:
            Deletion confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        cmd = f'post delete {shlex.quote(str(course_id))}'
        if force:
            cmd += ' --force'

        self.cli.execute(cmd)
        self.logger.info(f"Deleted course {course_id} (force={force})")
        return {"id": course_id, "deleted": True, "permanent": force}

    # ==================== LESSON MANAGEMENT ====================

    def create_lesson(
        self,
        course_id: int,
        title: str,
        content: str = "",
        status: Literal["publish", "draft"] = "draft",
        order: Optional[int] = None,
    ) -> dict:
        """
        Create a new lesson and associate with course.

        Args:
            course_id: Parent course ID
            title: Lesson title
            content: Lesson content
            status: Post status
            order: Lesson order (optional)

        Returns:
            Created lesson data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")
        title = self._validate_string(title, "title", max_length=200)
        if content:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        status = self._validate_literal(status, "status", ["publish", "draft"])
        if order is not None:
            order = self._validate_positive_int(order, "order")

        cmd = f'post create --post_type=sfwd-lessons --post_title={shlex.quote(title)} --post_status={status}'

        if content:
            cmd += f' --post_content={shlex.quote(content)}'

        result = self.cli.execute(cmd, format="json")
        lesson_id = result if isinstance(result, int) else int(result)

        # Associate with course (Security: quote all parameters)
        self.cli.execute(
            f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("course_id")} {shlex.quote(str(course_id))}'
        )
        self.cli.execute(
            f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote(f"ld_course_{course_id}")} {shlex.quote(str(course_id))}'
        )

        # Set order if provided
        if order is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("lesson_order")} {shlex.quote(str(order))}'
            )

        self.logger.info(f"Created lesson {lesson_id}: {title} for course {course_id}")

        return {
            "id": lesson_id,
            "title": title,
            "course_id": course_id,
            "status": status,
            "type": "lesson",
        }

    def update_lesson(
        self,
        lesson_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        order: Optional[int] = None,
    ) -> dict:
        """
        Update lesson details.

        Args:
            lesson_id: Lesson post ID
            title: New title (optional)
            content: New content (optional)
            order: New order (optional)

        Returns:
            Updated lesson data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")
        if title is not None:
            title = self._validate_string(title, "title", max_length=200)
        if content is not None:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        if order is not None:
            order = self._validate_positive_int(order, "order")

        updates = []

        if title:
            updates.append(f'--post_title={shlex.quote(title)}')
        if content is not None:
            updates.append(f'--post_content={shlex.quote(content)}')

        if updates:
            cmd = f'post update {shlex.quote(str(lesson_id))} {" ".join(updates)}'
            self.cli.execute(cmd)

        if order is not None:
            self.cli.execute(f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("lesson_order")} {shlex.quote(str(order))}')

        self.logger.info(f"Updated lesson {lesson_id}")

        return {"id": lesson_id, "updated": True}

    def list_course_lessons(self, course_id: int) -> list[dict]:
        """
        Get all lessons for a course.

        Args:
            course_id: Course post ID

        Returns:
            List of lessons

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        cmd = f'post list --post_type=sfwd-lessons --meta_key=course_id --meta_value={shlex.quote(str(course_id))} --orderby=menu_order --order=ASC'
        return self.cli.execute(cmd, format="json")

    # ==================== QUIZ MANAGEMENT ====================

    def create_quiz(
        self,
        course_id: int,
        lesson_id: Optional[int],
        title: str,
        description: str = "",
        passing_score: int = 80,
        certificate_id: Optional[int] = None,
    ) -> dict:
        """
        Create a new quiz.

        Args:
            course_id: Associated course ID
            lesson_id: Associated lesson ID (optional)
            title: Quiz title
            description: Quiz description
            passing_score: Passing percentage (0-100)
            certificate_id: Certificate for passing (optional)

        Returns:
            Created quiz data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")
        if lesson_id is not None:
            lesson_id = self._validate_positive_int(lesson_id, "lesson_id")
        title = self._validate_string(title, "title", max_length=200)
        if description:
            description = self._validate_string(
                description, "description", max_length=50000, allow_empty=True
            )
        passing_score = self._validate_int_range(
            passing_score, "passing_score", 0, 100
        )
        if certificate_id is not None:
            certificate_id = self._validate_positive_int(certificate_id, "certificate_id")

        cmd = f'post create --post_type=sfwd-quiz --post_title={shlex.quote(title)} --post_status=publish'

        if description:
            cmd += f' --post_content={shlex.quote(description)}'

        result = self.cli.execute(cmd, format="json")
        quiz_id = result if isinstance(result, int) else int(result)

        # Set quiz meta (Security: quote all parameters)
        self.cli.execute(f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("course_id")} {shlex.quote(str(course_id))}')

        if lesson_id:
            self.cli.execute(f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("lesson_id")} {shlex.quote(str(lesson_id))}')

        # Set passing score
        self.cli.execute(
            f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("_sfwd-quiz")} '
            f'{shlex.quote("_sfwd-quiz[sfwd-quiz_passingpercentage]")} {shlex.quote(str(passing_score))}'
        )

        if certificate_id:
            self.cli.execute(
                f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("_sfwd-quiz")} '
                f'{shlex.quote("_sfwd-quiz[sfwd-quiz_certificate]")} {shlex.quote(str(certificate_id))}'
            )

        self.logger.info(f"Created quiz {quiz_id}: {title} for course {course_id}")

        return {
            "id": quiz_id,
            "title": title,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "passing_score": passing_score,
            "type": "quiz",
        }

    def add_quiz_question(
        self,
        quiz_id: int,
        question_text: str,
        question_type: Literal["single", "multiple", "free_answer", "essay"] = "single",
        answers: Optional[list[dict]] = None,
        points: int = 1,
    ) -> dict:
        """
        Add a question to a quiz.

        Args:
            quiz_id: Quiz post ID
            question_text: The question text
            question_type: Question type (single, multiple, free_answer, essay)
            answers: List of answer dicts with 'text' and 'correct' keys
            points: Points for correct answer

        Returns:
            Created question data

        Raises:
            ValueError: If input validation fails

        Example answers:
            [
                {"text": "Answer 1", "correct": True},
                {"text": "Answer 2", "correct": False},
            ]
        """
        # Validate inputs
        quiz_id = self._validate_positive_int(quiz_id, "quiz_id")
        question_text = self._validate_string(question_text, "question_text", max_length=1000)
        question_type = self._validate_literal(
            question_type,
            "question_type",
            ["single", "multiple", "free_answer", "essay"]
        )
        points = self._validate_positive_int(points, "points")

        cmd = f'post create --post_type=sfwd-question --post_title={shlex.quote(question_text)} --post_status=publish'

        result = self.cli.execute(cmd, format="json")
        question_id = result if isinstance(result, int) else int(result)

        # Associate with quiz (Security: quote all parameters)
        self.cli.execute(f'post meta update {shlex.quote(str(question_id))} {shlex.quote("quiz_id")} {shlex.quote(str(quiz_id))}')

        # Set question type
        type_map = {
            "single": "single",
            "multiple": "multiple",
            "free_answer": "free_answer",
            "essay": "essay_text",
        }
        self.cli.execute(
            f'post meta update {shlex.quote(str(question_id))} {shlex.quote("question_type")} {shlex.quote(type_map[question_type])}'
        )

        # Set points
        self.cli.execute(f'post meta update {shlex.quote(str(question_id))} {shlex.quote("question_points")} {shlex.quote(str(points))}')

        # Add answers if provided
        if answers and question_type in ["single", "multiple"]:
            # Note: This is simplified - actual LearnDash uses complex serialized data
            # For production, you'd need to properly serialize answer data
            pass

        self.logger.info(f"Added question {question_id} to quiz {quiz_id}")

        return {
            "id": question_id,
            "quiz_id": quiz_id,
            "text": question_text,
            "type": question_type,
            "points": points,
        }

    # ==================== USER ENROLLMENT ====================

    def enroll_user(self, user_id: int, course_id: int) -> dict:
        """
        Enroll a user in a course.

        Args:
            user_id: WordPress user ID
            course_id: Course post ID

        Returns:
            Enrollment confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")
        course_id = self._validate_positive_int(course_id, "course_id")

        # LearnDash stores enrollments in user meta (Security: quote all parameters)
        self.cli.execute(
            f'user meta add {shlex.quote(str(user_id))} {shlex.quote(f"course_enrolled_{course_id}")} {shlex.quote(str(course_id))}'
        )

        # Also update course user list
        cmd = f'post meta add {shlex.quote(str(course_id))} {shlex.quote("learndash_course_users")} {shlex.quote(str(user_id))}'
        self.cli.execute(cmd)

        self.logger.info(f"Enrolled user {user_id} in course {course_id}")

        return {
            "user_id": user_id,
            "course_id": course_id,
            "enrolled": True,
        }

    def unenroll_user(self, user_id: int, course_id: int) -> dict:
        """
        Unenroll a user from a course.

        Args:
            user_id: WordPress user ID
            course_id: Course post ID

        Returns:
            Unenrollment confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")
        course_id = self._validate_positive_int(course_id, "course_id")

        self.cli.execute(
            f'user meta delete {shlex.quote(str(user_id))} {shlex.quote(f"course_enrolled_{course_id}")}'
        )
        self.cli.execute(
            f'post meta delete {shlex.quote(str(course_id))} {shlex.quote("learndash_course_users")} {shlex.quote(str(user_id))}'
        )

        self.logger.info(f"Unenrolled user {user_id} from course {course_id}")

        return {
            "user_id": user_id,
            "course_id": course_id,
            "enrolled": False,
        }

    def get_user_courses(self, user_id: int) -> list[dict]:
        """
        Get all courses a user is enrolled in.

        Args:
            user_id: WordPress user ID

        Returns:
            List of enrolled courses

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")

        # Get all user meta keys starting with course_enrolled_
        cmd = f'user meta list {shlex.quote(str(user_id))} --fields=meta_key,meta_value'
        meta = self.cli.execute(cmd, format="json")

        course_ids = [
            int(m['meta_value'])
            for m in meta
            if m['meta_key'].startswith('course_enrolled_')
        ]

        courses = []
        for cid in course_ids:
            course_data = self.cli.get_post(cid)
            courses.append(course_data)

        return courses

    def get_course_students(self, course_id: int) -> list[dict]:
        """
        Get all students enrolled in a course.

        Args:
            course_id: Course post ID

        Returns:
            List of enrolled users

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        cmd = f'post meta get {shlex.quote(str(course_id))} {shlex.quote("learndash_course_users")}'
        user_ids = self.cli.execute(cmd)

        # Parse serialized data if needed (LearnDash stores as serialized array)
        # For now, return raw data - would need parsing in production
        return {"user_ids": user_ids, "course_id": course_id}

    # ==================== GROUP MANAGEMENT ====================

    def create_group(
        self,
        title: str,
        description: str = "",
        course_ids: Optional[list[int]] = None,
    ) -> dict:
        """
        Create a LearnDash group.

        Args:
            title: Group name
            description: Group description
            course_ids: List of course IDs to associate

        Returns:
            Created group data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        title = self._validate_string(title, "title", max_length=200)
        if description:
            description = self._validate_string(
                description, "description", max_length=50000, allow_empty=True
            )
        if course_ids:
            # Validate each course ID
            course_ids = [
                self._validate_positive_int(cid, f"course_ids[{i}]")
                for i, cid in enumerate(course_ids)
            ]

        cmd = f'post create --post_type=groups --post_title={shlex.quote(title)} --post_status=publish'

        if description:
            cmd += f' --post_content={shlex.quote(description)}'

        result = self.cli.execute(cmd, format="json")
        group_id = result if isinstance(result, int) else int(result)

        # Associate courses (Security: quote all parameters)
        if course_ids:
            for course_id in course_ids:
                self.cli.execute(
                    f'post meta add {shlex.quote(str(group_id))} {shlex.quote(f"learndash_group_enrolled_{course_id}")} {shlex.quote(str(course_id))}'
                )

        self.logger.info(f"Created group {group_id}: {title}")

        return {
            "id": group_id,
            "title": title,
            "course_ids": course_ids or [],
            "type": "group",
        }

    def add_user_to_group(self, user_id: int, group_id: int) -> dict:
        """
        Add user to a LearnDash group.

        Args:
            user_id: WordPress user ID
            group_id: Group post ID

        Returns:
            Group addition confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")
        group_id = self._validate_positive_int(group_id, "group_id")

        self.cli.execute(
            f'user meta add {shlex.quote(str(user_id))} {shlex.quote(f"learndash_group_users_{group_id}")} {shlex.quote(str(group_id))}'
        )
        self.cli.execute(
            f'post meta add {shlex.quote(str(group_id))} {shlex.quote("learndash_group_users")} {shlex.quote(str(user_id))}'
        )

        self.logger.info(f"Added user {user_id} to group {group_id}")

        return {"user_id": user_id, "group_id": group_id, "added": True}

    def set_group_leader(self, user_id: int, group_id: int) -> dict:
        """
        Assign a user as group leader.

        Args:
            user_id: WordPress user ID
            group_id: Group post ID

        Returns:
            Group leader assignment confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")
        group_id = self._validate_positive_int(group_id, "group_id")

        # Add group leader meta (Security: quote all parameters)
        self.cli.execute(
            f'post meta add {shlex.quote(str(group_id))} {shlex.quote("learndash_group_leaders")} {shlex.quote(str(user_id))}'
        )
        self.cli.execute(
            f'user meta add {shlex.quote(str(user_id))} {shlex.quote(f"learndash_group_leaders_{group_id}")} {shlex.quote(str(group_id))}'
        )

        self.logger.info(f"Set user {user_id} as leader of group {group_id}")

        return {
            "user_id": user_id,
            "group_id": group_id,
            "role": "group_leader",
            "assigned": True,
        }

    # ==================== TOPIC MANAGEMENT ====================

    def create_topic(
        self,
        lesson_id: int,
        title: str,
        content: str = "",
        status: Literal["publish", "draft"] = "draft",
        order: Optional[int] = None,
    ) -> dict:
        """
        Create a new topic under a lesson.

        Args:
            lesson_id: Parent lesson ID
            title: Topic title
            content: Topic content
            status: Post status
            order: Topic order (optional)

        Returns:
            Created topic data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")
        title = self._validate_string(title, "title", max_length=200)
        if content:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        status = self._validate_literal(status, "status", ["publish", "draft"])
        if order is not None:
            order = self._validate_positive_int(order, "order")

        cmd = f'post create --post_type=sfwd-topic --post_title={shlex.quote(title)} --post_status={status}'

        if content:
            cmd += f' --post_content={shlex.quote(content)}'

        result = self.cli.execute(cmd, format="json")
        topic_id = result if isinstance(result, int) else int(result)

        # Get course ID from lesson
        lesson_data = self.cli.get_post(lesson_id)
        course_id = None
        if lesson_data and 'meta' in lesson_data:
            course_id = lesson_data['meta'].get('course_id')

        # Associate with lesson and course (Security: quote all parameters)
        self.cli.execute(f'post meta update {shlex.quote(str(topic_id))} {shlex.quote("lesson_id")} {shlex.quote(str(lesson_id))}')

        if course_id:
            self.cli.execute(f'post meta update {shlex.quote(str(topic_id))} {shlex.quote("course_id")} {shlex.quote(str(course_id))}')
            self.cli.execute(f'post meta update {shlex.quote(str(topic_id))} {shlex.quote(f"ld_course_{course_id}")} {shlex.quote(str(course_id))}')

        # Set order if provided
        if order is not None:
            self.cli.execute(f'post meta update {shlex.quote(str(topic_id))} {shlex.quote("topic_order")} {shlex.quote(str(order))}')

        self.logger.info(f"Created topic {topic_id}: {title} for lesson {lesson_id}")

        return {
            "id": topic_id,
            "title": title,
            "lesson_id": lesson_id,
            "course_id": course_id,
            "status": status,
            "type": "topic",
        }

    def list_lesson_topics(self, lesson_id: int) -> list[dict]:
        """
        Get all topics for a lesson.

        Args:
            lesson_id: Lesson post ID

        Returns:
            List of topics

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")

        cmd = f'post list --post_type=sfwd-topic --meta_key=lesson_id --meta_value={shlex.quote(str(lesson_id))} --orderby=menu_order --order=ASC'
        return self.cli.execute(cmd, format="json")

    def update_topic(
        self,
        topic_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        order: Optional[int] = None,
        status: Optional[str] = None,
    ) -> dict:
        """
        Update an existing topic.

        Args:
            topic_id: Topic post ID
            title: New title (optional)
            content: New content (optional)
            order: New order/position (optional)
            status: New status (publish, draft) (optional)

        Returns:
            Updated topic data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        topic_id = self._validate_positive_int(topic_id, "topic_id")
        if title is not None:
            title = self._validate_string(title, "title", max_length=200)
        if content is not None:
            content = self._validate_string(
                content, "content", max_length=50000, allow_empty=True
            )
        if order is not None:
            order = self._validate_positive_int(order, "order")
        if status is not None:
            status = self._validate_literal(status, "status", ["publish", "draft"])

        updates = []

        if title:
            updates.append(f'--post_title={shlex.quote(title)}')
        if content is not None:
            updates.append(f'--post_content={shlex.quote(content)}')
        if status:
            updates.append(f'--post_status={status}')

        if updates:
            cmd = f'post update {shlex.quote(str(topic_id))} {" ".join(updates)}'
            self.cli.execute(cmd)

        if order is not None:
            self.cli.execute(f'post meta update {shlex.quote(str(topic_id))} {shlex.quote("topic_order")} {shlex.quote(str(order))}')

        self.logger.info(f"Updated topic {topic_id}")

        return {"id": topic_id, "updated": True}

    # ==================== QUIZ MODIFICATION ====================

    def update_quiz(
        self,
        quiz_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        passing_score: Optional[int] = None,
        quiz_attempts: Optional[int] = None,
        time_limit: Optional[int] = None,
    ) -> dict:
        """
        Update quiz settings like title, passing score, attempts, time limit.

        Args:
            quiz_id: Quiz post ID
            title: New title (optional)
            description: New description (optional)
            passing_score: New passing percentage 0-100 (optional)
            quiz_attempts: Number of allowed attempts (optional)
            time_limit: Time limit in minutes (optional)

        Returns:
            Updated quiz data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        quiz_id = self._validate_positive_int(quiz_id, "quiz_id")
        if title is not None:
            title = self._validate_string(title, "title", max_length=200)
        if description is not None:
            description = self._validate_string(
                description, "description", max_length=50000, allow_empty=True
            )
        if passing_score is not None:
            passing_score = self._validate_int_range(
                passing_score, "passing_score", 0, 100
            )
        if quiz_attempts is not None:
            quiz_attempts = self._validate_positive_int(quiz_attempts, "quiz_attempts")
        if time_limit is not None:
            time_limit = self._validate_positive_int(time_limit, "time_limit")

        updates = []

        if title:
            updates.append(f'--post_title={shlex.quote(title)}')
        if description is not None:
            updates.append(f'--post_content={shlex.quote(description)}')

        if updates:
            cmd = f'post update {shlex.quote(str(quiz_id))} {" ".join(updates)}'
            self.cli.execute(cmd)

        # Update LearnDash quiz meta (Security: quote all parameters)
        if passing_score is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("_sfwd-quiz")} '
                f'{shlex.quote("_sfwd-quiz[sfwd-quiz_passingpercentage]")} {shlex.quote(str(passing_score))}'
            )

        if quiz_attempts is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("_sfwd-quiz")} '
                f'{shlex.quote("_sfwd-quiz[sfwd-quiz_repeats]")} {shlex.quote(str(quiz_attempts))}'
            )

        if time_limit is not None:
            self.cli.execute(
                f'post meta update {shlex.quote(str(quiz_id))} {shlex.quote("_sfwd-quiz")} '
                f'{shlex.quote("_sfwd-quiz[sfwd-quiz_time_limit]")} {shlex.quote(str(time_limit))}'
            )

        self.logger.info(f"Updated quiz {quiz_id}")

        return {"success": True, "id": quiz_id, "action": "updated", "data": {"updated": True}}

    # ==================== CONTENT REORDERING ====================

    def reorder_lessons(
        self,
        course_id: int,
        lesson_order: list[int],
    ) -> dict:
        """
        Reorder lessons in a course.

        Args:
            course_id: Course post ID
            lesson_order: List of lesson IDs in desired order [123, 456, 789]

        Returns:
            Confirmation with new order

        Raises:
            ValueError: If input validation fails

        Example:
            # Put lesson 456 first, then 123, then 789
            reorder_lessons(course_id=1, lesson_order=[456, 123, 789])
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        if not isinstance(lesson_order, list):
            raise ValueError("lesson_order must be a list")
        if not lesson_order:
            raise ValueError("lesson_order cannot be empty")

        # Check for duplicate IDs
        if len(lesson_order) != len(set(lesson_order)):
            raise ValueError("lesson_order contains duplicate IDs. Each lesson can only appear once.")

        # Validate each lesson ID
        validated_lessons = [
            self._validate_positive_int(lid, f"lesson_order[{i}]")
            for i, lid in enumerate(lesson_order)
        ]

        # Verify all lessons belong to the specified course
        self.logger.info(f"Verifying all {len(validated_lessons)} lessons belong to course {course_id}")
        for lesson_id in validated_lessons:
            try:
                lesson_course_id = self._get_meta(lesson_id, 'course_id')
                if lesson_course_id and int(lesson_course_id) != course_id:
                    raise ValueError(
                        f"Lesson {lesson_id} belongs to course {lesson_course_id}, not course {course_id}. "
                        f"Cannot reorder lessons from different courses."
                    )
            except Exception as e:
                raise ValueError(f"Could not verify ownership of lesson {lesson_id}: {e}")

        # Update menu_order for each lesson (Security: quote all parameters)
        for index, lesson_id in enumerate(validated_lessons):
            # menu_order starts at 0
            menu_order = index
            self.cli.execute(f'post update {shlex.quote(str(lesson_id))} --menu_order={shlex.quote(str(menu_order))}')
            self.logger.info(f"Set lesson {lesson_id} to position {menu_order}")

        self.logger.info(f"Reordered {len(validated_lessons)} lessons in course {course_id}")

        return {
            "success": True,
            "id": course_id,
            "action": "reordered",
            "data": {
                "course_id": course_id,
                "lesson_order": validated_lessons,
                "total_lessons": len(validated_lessons),
            }
        }

    def reorder_topics(
        self,
        lesson_id: int,
        topic_order: list[int],
    ) -> dict:
        """
        Reorder topics within a lesson using menu_order.

        Args:
            lesson_id: Lesson post ID
            topic_order: List of topic IDs in desired order [123, 456, 789]

        Returns:
            Confirmation with new order

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")

        if not isinstance(topic_order, list):
            raise ValueError("topic_order must be a list")
        if not topic_order:
            raise ValueError("topic_order cannot be empty")

        # Check for duplicate IDs
        if len(topic_order) != len(set(topic_order)):
            raise ValueError("topic_order contains duplicate IDs. Each topic can only appear once.")

        # Validate each topic ID
        validated_topics = [
            self._validate_positive_int(tid, f"topic_order[{i}]")
            for i, tid in enumerate(topic_order)
        ]

        # Verify all topics belong to the specified lesson
        self.logger.info(f"Verifying all {len(validated_topics)} topics belong to lesson {lesson_id}")
        for topic_id in validated_topics:
            try:
                topic_lesson_id = self._get_meta(topic_id, 'lesson_id')
                if topic_lesson_id and int(topic_lesson_id) != lesson_id:
                    raise ValueError(
                        f"Topic {topic_id} belongs to lesson {topic_lesson_id}, not lesson {lesson_id}. "
                        f"Cannot reorder topics from different lessons."
                    )
            except Exception as e:
                raise ValueError(f"Could not verify ownership of topic {topic_id}: {e}")

        # Update menu_order for each topic (Security: quote all parameters)
        for index, topic_id in enumerate(validated_topics):
            # menu_order starts at 0
            menu_order = index
            self.cli.execute(f'post update {shlex.quote(str(topic_id))} --menu_order={shlex.quote(str(menu_order))}')
            self.logger.info(f"Set topic {topic_id} to position {menu_order}")

        self.logger.info(f"Reordered {len(validated_topics)} topics in lesson {lesson_id}")

        return {
            "success": True,
            "id": lesson_id,
            "action": "reordered",
            "data": {
                "lesson_id": lesson_id,
                "topic_order": validated_topics,
                "total_topics": len(validated_topics),
            }
        }

    # ==================== CONTENT MOVEMENT ====================

    def move_lesson_to_course(
        self,
        lesson_id: int,
        from_course_id: int,
        to_course_id: int,
        new_order: Optional[int] = None,
    ) -> dict:
        """
        Move a lesson from one course to another.

        Args:
            lesson_id: Lesson post ID
            from_course_id: Source course ID
            to_course_id: Destination course ID
            new_order: New order/position in destination course (optional)

        Returns:
            Move confirmation

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")
        from_course_id = self._validate_positive_int(from_course_id, "from_course_id")
        to_course_id = self._validate_positive_int(to_course_id, "to_course_id")
        if new_order is not None:
            new_order = self._validate_positive_int(new_order, "new_order")

        # Verify lesson belongs to from_course_id
        lesson_data = self.cli.get_post(lesson_id)
        if not lesson_data:
            raise ValueError(f"Lesson {lesson_id} not found")

        current_course = None
        if 'meta' in lesson_data:
            current_course = lesson_data['meta'].get('course_id')

        if current_course and int(current_course) != from_course_id:
            self.logger.warning(
                f"Lesson {lesson_id} belongs to course {current_course}, not {from_course_id}"
            )

        # Update course association (Security: quote all parameters)
        self.cli.execute(f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("course_id")} {shlex.quote(str(to_course_id))}')
        self.cli.execute(f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote(f"ld_course_{to_course_id}")} {shlex.quote(str(to_course_id))}')

        # Remove old course association
        self.cli.execute(f'post meta delete {shlex.quote(str(lesson_id))} {shlex.quote(f"ld_course_{from_course_id}")}')

        # Set new order if provided
        if new_order is not None:
            self.cli.execute(f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("lesson_order")} {shlex.quote(str(new_order))}')

        self.logger.info(
            f"Moved lesson {lesson_id} from course {from_course_id} to course {to_course_id}"
        )

        return {
            "success": True,
            "id": lesson_id,
            "action": "moved",
            "data": {
                "lesson_id": lesson_id,
                "from_course_id": from_course_id,
                "to_course_id": to_course_id,
                "new_order": new_order,
            }
        }

    # ==================== CONTENT DUPLICATION ====================

    def duplicate_lesson(
        self,
        lesson_id: int,
        new_title: Optional[str] = None,
        include_topics: bool = True,
    ) -> dict:
        """
        Duplicate a lesson (and optionally its topics).

        Args:
            lesson_id: Lesson post ID to duplicate
            new_title: Title for duplicated lesson (optional, defaults to "Copy of [original]")
            include_topics: Whether to duplicate topics as well (default: True)

        Returns:
            New lesson ID and list of duplicated topic IDs

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")
        if new_title is not None:
            new_title = self._validate_string(new_title, "new_title", max_length=200)

        # Get original lesson data
        original = self.cli.get_post(lesson_id)
        if not original:
            raise ValueError(f"Lesson {lesson_id} not found")

        # Determine new title
        original_title = original.get('title', {}).get('rendered', 'Untitled')
        duplicate_title = new_title if new_title else f"Copy of {original_title}"

        # Get lesson metadata
        course_id = None
        if 'meta' in original:
            course_id = original['meta'].get('course_id')

        # Get lesson content
        content = original.get('content', {}).get('rendered', '')

        # Create duplicate lesson
        if course_id:
            new_lesson = self.create_lesson(
                course_id=int(course_id),
                title=duplicate_title,
                content=content,
                status="draft",
            )
        else:
            raise ValueError(f"Lesson {lesson_id} has no associated course")

        new_lesson_id = new_lesson['id']

        # Duplicate topics if requested
        duplicated_topics = []
        if include_topics:
            original_topics = self.list_lesson_topics(lesson_id)
            for topic in original_topics:
                topic_id = topic.get('ID') or topic.get('id')
                topic_title = topic.get('post_title') or topic.get('title', {}).get('rendered', 'Untitled')

                # Get topic data
                topic_data = self.cli.get_post(topic_id)
                topic_content = topic_data.get('content', {}).get('rendered', '')

                # Create duplicate topic
                new_topic = self.create_topic(
                    lesson_id=new_lesson_id,
                    title=f"Copy of {topic_title}",
                    content=topic_content,
                    status="draft",
                )
                duplicated_topics.append(new_topic['id'])

        self.logger.info(
            f"Duplicated lesson {lesson_id} as {new_lesson_id} "
            f"with {len(duplicated_topics)} topics"
        )

        return {
            "success": True,
            "id": new_lesson_id,
            "action": "duplicated",
            "data": {
                "original_lesson_id": lesson_id,
                "new_lesson_id": new_lesson_id,
                "new_title": duplicate_title,
                "duplicated_topics": duplicated_topics,
                "topics_count": len(duplicated_topics),
            }
        }

    # ==================== BATCH OPERATIONS ====================

    def batch_update_lesson_content(
        self,
        updates: list[dict],
    ) -> dict:
        """
        Update multiple lessons in one call.

        Args:
            updates: List of dicts like:
                [
                    {"lesson_id": 123, "title": "New Title", "content": "..."},
                    {"lesson_id": 456, "order": 2},
                ]

        Returns:
            Success/failure for each update

        Raises:
            ValueError: If input validation fails
        """
        # Validate updates list
        if not isinstance(updates, list):
            raise ValueError("updates must be a list")
        if not updates:
            raise ValueError("updates cannot be empty")

        results = {
            "total_updates": len(updates),
            "successful": 0,
            "failed": 0,
            "details": [],
            "aborted": False,
        }

        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 5

        for i, update_dict in enumerate(updates):
            try:
                if not isinstance(update_dict, dict):
                    raise ValueError(f"updates[{i}] must be a dict")

                lesson_id = update_dict.get("lesson_id")
                if not lesson_id:
                    raise ValueError(f"updates[{i}] missing lesson_id")

                # Perform update
                result = self.update_lesson(
                    lesson_id=lesson_id,
                    title=update_dict.get("title"),
                    content=update_dict.get("content"),
                    order=update_dict.get("order"),
                )

                results["successful"] += 1
                results["details"].append({
                    "lesson_id": lesson_id,
                    "status": "success",
                    "result": result,
                })
                consecutive_failures = 0  # Reset on success

            except Exception as e:
                self.logger.error(f"Failed to update lesson in batch (index {i}): {e}")
                results["failed"] += 1
                results["details"].append({
                    "lesson_id": update_dict.get("lesson_id", "unknown"),
                    "status": "failed",
                    "error": str(e),
                })
                consecutive_failures += 1

                # Circuit breaker: abort if too many consecutive failures
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    self.logger.error(
                        f"Aborting batch update after {MAX_CONSECUTIVE_FAILURES} consecutive failures"
                    )
                    results["aborted"] = True
                    # Mark remaining lessons as not attempted
                    for remaining_update in updates[i+1:]:
                        results["details"].append({
                            "lesson_id": remaining_update.get("lesson_id"),
                            "status": "not_attempted",
                            "error": "Batch operation aborted due to consecutive failures"
                        })
                    break

        self.logger.info(
            f"Batch update completed: {results['successful']} successful, "
            f"{results['failed']} failed"
        )

        return {
            "success": results["failed"] == 0,
            "id": None,
            "action": "batch_updated",
            "data": results,
        }

    # ==================== LESSON PREREQUISITES ====================

    def set_lesson_prerequisites(
        self,
        lesson_id: int,
        prerequisite_lesson_ids: list[int],
    ) -> dict:
        """
        Set which lessons must be completed before this one.

        Args:
            lesson_id: Lesson post ID
            prerequisite_lesson_ids: List of prerequisite lesson IDs (empty to clear)

        Returns:
            Update confirmation

        Note:
            This currently uses comma-separated format for multiple prerequisites.
            If this doesn't work with LearnDash in production, it may need to be
            updated to use PHP serialized array format.

        Example:
            # Single prerequisite
            set_lesson_prerequisites(lesson_id=2, prerequisite_lesson_ids=[1])

            # Multiple prerequisites
            set_lesson_prerequisites(lesson_id=3, prerequisite_lesson_ids=[1, 2])

            # Clear prerequisites
            set_lesson_prerequisites(lesson_id=3, prerequisite_lesson_ids=[])

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        lesson_id = self._validate_positive_int(lesson_id, "lesson_id")

        if not isinstance(prerequisite_lesson_ids, list):
            raise ValueError("prerequisite_lesson_ids must be a list")

        # Validate each prerequisite ID and check for circular dependencies
        validated_prerequisites = []
        for i, prereq_id in enumerate(prerequisite_lesson_ids):
            prereq_id = self._validate_positive_int(prereq_id, f"prerequisite_lesson_ids[{i}]")

            # Prevent lesson from being its own prerequisite
            if prereq_id == lesson_id:
                raise ValueError(
                    f"Circular dependency: Lesson {lesson_id} cannot be its own prerequisite"
                )

            validated_prerequisites.append(prereq_id)

        # LearnDash stores prerequisites as a serialized array
        # For single prerequisite, use lesson_prerequisite meta
        # For multiple, we need to use the LearnDash settings array

        if len(validated_prerequisites) == 1:
            self.cli.execute(
                f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("lesson_prerequisite")} {shlex.quote(str(validated_prerequisites[0]))}'
            )
        elif len(validated_prerequisites) > 1:
            # Store as comma-separated for now
            # In production, this should be properly serialized
            prereq_str = ','.join(map(str, validated_prerequisites))
            self.cli.execute(
                f'post meta update {shlex.quote(str(lesson_id))} {shlex.quote("lesson_prerequisites")} {shlex.quote(prereq_str)}'
            )
        else:
            # Clear prerequisites (Security: quote all parameters)
            self.cli.execute(f'post meta delete {shlex.quote(str(lesson_id))} {shlex.quote("lesson_prerequisite")}')
            self.cli.execute(f'post meta delete {shlex.quote(str(lesson_id))} {shlex.quote("lesson_prerequisites")}')

        self.logger.info(
            f"Set {len(validated_prerequisites)} prerequisites for lesson {lesson_id}"
        )

        return {
            "success": True,
            "id": lesson_id,
            "action": "prerequisites_set",
            "data": {
                "lesson_id": lesson_id,
                "prerequisite_lesson_ids": validated_prerequisites,
                "count": len(validated_prerequisites),
            }
        }

    # ==================== COURSE BUILDER STRUCTURE ====================

    def update_course_builder_structure(
        self,
        course_id: int,
        structure: dict,
    ) -> dict:
        """
        Update the entire course structure in one call.

        IMPORTANT: This is a custom implementation that stores structure in a
        custom meta field (ld_course_builder). It may not integrate with LearnDash's
        native course builder UI. Use for custom course management workflows.

        For native LearnDash integration, consider using individual lesson operations
        (create_lesson, reorder_lessons, etc.) which are guaranteed to work with
        LearnDash's course builder.

        Args:
            course_id: Course post ID
            structure: Dict defining the course structure with sections and lessons

        Returns:
            Update confirmation with lesson count

        Example structure:
            {
                "sections": [
                    {
                        "heading": "Module 1: Introduction",
                        "lessons": [
                            {"lesson_id": 123, "order": 0},
                            {"lesson_id": 456, "order": 1},
                        ]
                    }
                ]
            }

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        if not isinstance(structure, dict):
            raise ValueError("structure must be a dict")
        if "sections" not in structure:
            raise ValueError("structure must contain 'sections' key")
        if not isinstance(structure["sections"], list):
            raise ValueError("structure['sections'] must be a list")

        # Validate and process each section
        total_lessons = 0
        for i, section in enumerate(structure["sections"]):
            if not isinstance(section, dict):
                raise ValueError(f"sections[{i}] must be a dict")

            if "heading" not in section:
                raise ValueError(f"sections[{i}] missing 'heading'")

            heading = self._validate_string(
                section["heading"], f"sections[{i}].heading", max_length=200
            )

            if "lessons" in section:
                if not isinstance(section["lessons"], list):
                    raise ValueError(f"sections[{i}]['lessons'] must be a list")

                # Validate lesson IDs
                for j, lesson_info in enumerate(section["lessons"]):
                    if not isinstance(lesson_info, dict):
                        raise ValueError(f"sections[{i}].lessons[{j}] must be a dict")
                    if "lesson_id" not in lesson_info:
                        raise ValueError(f"sections[{i}].lessons[{j}] missing 'lesson_id'")

                    lesson_id = self._validate_positive_int(
                        lesson_info["lesson_id"],
                        f"sections[{i}].lessons[{j}].lesson_id"
                    )
                    total_lessons += 1

        # Store the course builder structure
        # LearnDash uses a complex serialized structure
        # For now, we'll store as JSON in a custom meta field
        import json
        structure_json = json.dumps(structure)

        self.cli.execute(
            f'post meta update {shlex.quote(str(course_id))} {shlex.quote("ld_course_builder")} {shlex.quote(structure_json)}'
        )

        # Also update individual lesson orders (Security: quote all parameters)
        global_order = 0
        for section in structure["sections"]:
            if "lessons" in section:
                for lesson_info in section["lessons"]:
                    lesson_id = lesson_info["lesson_id"]
                    order = lesson_info.get("order", global_order)
                    self.cli.execute(f'post update {shlex.quote(str(lesson_id))} --menu_order={shlex.quote(str(order))}')
                    global_order += 1

        self.logger.info(
            f"Updated course builder structure for course {course_id} "
            f"with {len(structure['sections'])} sections and {total_lessons} lessons"
        )

        return {
            "success": True,
            "id": course_id,
            "action": "structure_updated",
            "data": {
                "course_id": course_id,
                "sections_count": len(structure["sections"]),
                "total_lessons": total_lessons,
                "structure": structure,
            }
        }

    # ==================== ANALYTICS & PROGRESS ====================

    def get_user_progress(self, user_id: int, course_id: int) -> dict:
        """
        Get detailed progress for a user in a specific course.

        Args:
            user_id: WordPress user ID
            course_id: Course post ID

        Returns:
            Detailed progress data including lessons, topics, quizzes

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")
        course_id = self._validate_positive_int(course_id, "course_id")

        # Get user course progress meta (Security: quote all parameters)
        cmd = f'user meta get {shlex.quote(str(user_id))} {shlex.quote(f"course_progress_{course_id}")}'
        progress_data = self.cli.execute(cmd)

        # Get completed lessons
        cmd = f'user meta list {shlex.quote(str(user_id))} --fields=meta_key,meta_value'
        all_meta = self.cli.execute(cmd, format="json")

        completed_lessons = [
            int(m['meta_value'])
            for m in all_meta
            if m['meta_key'].startswith(f'course_{course_id}_lesson_') and m['meta_key'].endswith('_completed')
        ]

        # Get quiz attempts
        quiz_attempts = [
            m for m in all_meta
            if 'quiz_' in m['meta_key'] and 'attempt_' in m['meta_key']
        ]

        # Calculate completion percentage
        lessons = self.list_course_lessons(course_id)
        total_lessons = len(lessons)
        completed_count = len(completed_lessons)
        completion_percent = (completed_count / total_lessons * 100) if total_lessons > 0 else 0

        return {
            "user_id": user_id,
            "course_id": course_id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_count,
            "completion_percent": round(completion_percent, 2),
            "completed_lesson_ids": completed_lessons,
            "quiz_attempts": len(quiz_attempts),
            "progress_data": progress_data,
        }

    def get_course_completion_rate(self, course_id: int) -> dict:
        """
        Get completion statistics for a course.

        Args:
            course_id: Course post ID

        Returns:
            Course completion statistics

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")

        # Get all enrolled users (Security: quote all parameters)
        cmd = f'post meta get {shlex.quote(str(course_id))} {shlex.quote("learndash_course_users")}'
        enrolled_users_data = self.cli.execute(cmd)

        # Parse user IDs (this might be serialized data)
        # For now, we'll return raw data with explanation

        # Get course lessons count
        lessons = self.list_course_lessons(course_id)
        total_lessons = len(lessons)

        return {
            "course_id": course_id,
            "total_lessons": total_lessons,
            "enrolled_users_data": enrolled_users_data,
            "note": "enrolled_users_data may contain serialized PHP array - parse accordingly",
        }

    def get_group_progress(self, group_id: int) -> dict:
        """
        Get group-wide progress statistics.

        Args:
            group_id: Group post ID

        Returns:
            Group progress data for all members

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        group_id = self._validate_positive_int(group_id, "group_id")

        # Get group users (Security: quote all parameters)
        cmd = f'post meta get {shlex.quote(str(group_id))} {shlex.quote("learndash_group_users")}'
        group_users_data = self.cli.execute(cmd)

        # Get associated courses
        cmd = f'post meta list {shlex.quote(str(group_id))} --fields=meta_key,meta_value'
        group_meta = self.cli.execute(cmd, format="json")

        course_ids = [
            int(m['meta_value'])
            for m in group_meta
            if m['meta_key'].startswith('learndash_group_enrolled_')
        ]

        return {
            "group_id": group_id,
            "associated_courses": course_ids,
            "group_users_data": group_users_data,
            "note": "group_users_data may contain serialized PHP array - parse accordingly",
        }

    # ==================== BULK OPERATIONS ====================

    def bulk_enroll_users(self, user_ids: list[int], course_id: int) -> dict:
        """
        Enroll multiple users in a course at once.

        Args:
            user_ids: List of WordPress user IDs
            course_id: Course post ID

        Returns:
            Bulk enrollment results with circuit breaker protection

        Raises:
            ValueError: If input validation fails
        """
        # Validate course_id upfront
        course_id = self._validate_positive_int(course_id, "course_id")

        # Validate user_ids list
        if not isinstance(user_ids, list):
            raise ValueError("user_ids must be a list")
        if not user_ids:
            raise ValueError("user_ids cannot be empty")

        results = {
            "course_id": course_id,
            "total_users": len(user_ids),
            "enrolled": 0,
            "failed": 0,
            "errors": [],
            "aborted": False,
        }

        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 5

        for i, user_id in enumerate(user_ids):
            try:
                # Validate this user_id
                user_id = self._validate_positive_int(user_id, f"user_ids[{i}]")

                # Attempt enrollment
                result = self.enroll_user(user_id, course_id)
                if result.get("enrolled"):
                    results["enrolled"] += 1
                    consecutive_failures = 0
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": user_id,
                        "error": result.get("error", "Unknown error")
                    })
                    consecutive_failures += 1

            except ValueError as e:
                # Validation error
                self.logger.error(f"Validation error for user {user_id}: {e}")
                results["failed"] += 1
                results["errors"].append({"user_id": user_id, "error": str(e)})
                consecutive_failures += 1

            except Exception as e:
                # Other errors
                self.logger.error(f"Failed to enroll user {user_id}: {e}")
                results["failed"] += 1
                results["errors"].append({"user_id": user_id, "error": str(e)})
                consecutive_failures += 1

            # Circuit breaker: abort if too many consecutive failures
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                self.logger.error(
                    f"Aborting bulk enrollment after {MAX_CONSECUTIVE_FAILURES} consecutive failures"
                )
                results["aborted"] = True
                break

        self.logger.info(
            f"Bulk enrollment completed: {results['enrolled']} enrolled, "
            f"{results['failed']} failed, aborted={results['aborted']}"
        )

        return results

    def bulk_add_to_group(self, user_ids: list[int], group_id: int) -> dict:
        """
        Add multiple users to a group at once.

        Args:
            user_ids: List of WordPress user IDs
            group_id: Group post ID

        Returns:
            Bulk group addition results with circuit breaker protection

        Raises:
            ValueError: If input validation fails
        """
        # Validate group_id upfront
        group_id = self._validate_positive_int(group_id, "group_id")

        # Validate user_ids list
        if not isinstance(user_ids, list):
            raise ValueError("user_ids must be a list")
        if not user_ids:
            raise ValueError("user_ids cannot be empty")

        results = {
            "group_id": group_id,
            "total_users": len(user_ids),
            "added": 0,
            "failed": 0,
            "errors": [],
            "aborted": False,
        }

        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 5

        for i, user_id in enumerate(user_ids):
            try:
                # Validate this user_id
                user_id = self._validate_positive_int(user_id, f"user_ids[{i}]")

                # Attempt to add to group
                result = self.add_user_to_group(user_id, group_id)
                if result.get("added"):
                    results["added"] += 1
                    consecutive_failures = 0
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": user_id,
                        "error": result.get("error", "Unknown error")
                    })
                    consecutive_failures += 1

            except ValueError as e:
                # Validation error
                self.logger.error(f"Validation error for user {user_id}: {e}")
                results["failed"] += 1
                results["errors"].append({"user_id": user_id, "error": str(e)})
                consecutive_failures += 1

            except Exception as e:
                # Other errors
                self.logger.error(f"Failed to add user {user_id} to group: {e}")
                results["failed"] += 1
                results["errors"].append({"user_id": user_id, "error": str(e)})
                consecutive_failures += 1

            # Circuit breaker: abort if too many consecutive failures
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                self.logger.error(
                    f"Aborting bulk group addition after {MAX_CONSECUTIVE_FAILURES} consecutive failures"
                )
                results["aborted"] = True
                break

        self.logger.info(
            f"Bulk group addition completed: {results['added']} added, "
            f"{results['failed']} failed, aborted={results['aborted']}"
        )

        return results

    # ==================== QUIZ STATISTICS ====================

    def get_quiz_statistics(self, quiz_id: int) -> dict:
        """
        Get quiz performance statistics.

        Args:
            quiz_id: Quiz post ID

        Returns:
            Quiz statistics including attempts, average score, pass rate

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        quiz_id = self._validate_positive_int(quiz_id, "quiz_id")

        # Get quiz meta (Security: quote all parameters)
        cmd = f'post meta list {shlex.quote(str(quiz_id))} --fields=meta_key,meta_value'
        quiz_meta = self.cli.execute(cmd, format="json")

        # Get quiz settings
        passing_score = next(
            (int(m['meta_value']) for m in quiz_meta
             if 'passingpercentage' in m['meta_key']),
            80
        )

        # Get quiz questions count
        questions_cmd = f'post list --post_type=sfwd-question --meta_key=quiz_id --meta_value={shlex.quote(str(quiz_id))}'
        questions = self.cli.execute(questions_cmd, format="json")
        total_questions = len(questions) if questions else 0

        return {
            "quiz_id": quiz_id,
            "total_questions": total_questions,
            "passing_score": passing_score,
            "note": "Detailed attempt statistics require querying user meta across all users",
        }

    # ==================== CERTIFICATES ====================

    def list_certificates(self) -> list[dict]:
        """
        List all certificate templates.

        Returns:
            List of all certificate templates
        """
        cmd = 'post list --post_type=sfwd-certificates --post_status=publish'
        return self.cli.execute(cmd, format="json")

    def get_user_certificates(self, user_id: int) -> list[dict]:
        """
        Get all certificates earned by a user.

        Args:
            user_id: WordPress user ID

        Returns:
            List of earned certificates with course/quiz associations

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        user_id = self._validate_positive_int(user_id, "user_id")

        # Get user meta for certificates (Security: quote all parameters)
        cmd = f'user meta list {shlex.quote(str(user_id))} --fields=meta_key,meta_value'
        all_meta = self.cli.execute(cmd, format="json")

        certificates = []
        for meta in all_meta:
            if 'course_completed_' in meta['meta_key']:
                course_id = meta['meta_key'].replace('course_completed_', '')
                certificates.append({
                    "type": "course_certificate",
                    "course_id": int(course_id),
                    "timestamp": meta['meta_value'],
                })
            elif 'quiz_completed_' in meta['meta_key']:
                quiz_id = meta['meta_key'].replace('quiz_completed_', '')
                certificates.append({
                    "type": "quiz_certificate",
                    "quiz_id": int(quiz_id),
                    "timestamp": meta['meta_value'],
                })

        return {
            "user_id": user_id,
            "certificates": certificates,
            "total": len(certificates),
        }

    # ==================== REPORTING ====================

    def export_completion_report(self, course_id: int, format: str = "json") -> dict:
        """
        Generate a compliance/completion report for a course.

        Args:
            course_id: Course post ID
            format: Output format (json, csv)

        Returns:
            Completion report data

        Raises:
            ValueError: If input validation fails
        """
        # Validate inputs
        course_id = self._validate_positive_int(course_id, "course_id")
        format = self._validate_literal(format, "format", ["json", "csv"])

        # Get all enrolled users (Security: quote all parameters)
        cmd = f'post meta get {shlex.quote(str(course_id))} {shlex.quote("learndash_course_users")}'
        enrolled_users_data = self.cli.execute(cmd)

        # Get course info
        course = self.cli.get_post(course_id)
        lessons = self.list_course_lessons(course_id)

        report = {
            "course_id": course_id,
            "course_title": course.get('title', {}).get('rendered', 'Unknown'),
            "report_date": self.cli.execute('eval "date +%Y-%m-%d"'),
            "total_lessons": len(lessons),
            "enrolled_users_data": enrolled_users_data,
            "format": format,
            "note": "This report provides enrollment data. For detailed completion, iterate through users with get_user_progress()",
        }

        return report

    # ==================== ADVANCED ENROLLMENT & PROGRESS ====================

    def get_course_enrollments(self, course_id: int) -> dict:
        """
        Get list of all users enrolled in a course.

        Uses LearnDash's native learndash_get_users_for_course() function.

        Args:
            course_id: Course post ID

        Returns:
            Dict with enrolled users list and count

        Raises:
            ValueError: If input validation fails
        """
        course_id = self._validate_positive_int(course_id, "course_id")

        php_code = f'''
$course_id = {course_id};
$users = learndash_get_users_for_course($course_id, array(), false);
$result = array("course_id" => $course_id, "users" => array(), "count" => 0);

if ($users && !empty($users->results)) {{
    $result["count"] = count($users->results);
    foreach($users->results as $user_id) {{
        $user = get_user_by("id", $user_id);
        $result["users"][] = array(
            "user_id" => $user_id,
            "email" => $user->user_email,
            "display_name" => $user->display_name
        );
    }}
}}
echo json_encode($result);
'''
        cmd = f'eval {shlex.quote(php_code)}'
        result = self.cli.execute(cmd, format=None)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"course_id": course_id, "users": [], "count": 0, "error": result}

    def migrate_students(
        self,
        from_course_id: int,
        to_course_id: int,
        user_ids: Optional[list[int]] = None,
        remove_from_source: bool = True
    ) -> dict:
        """
        Migrate students from one course to another.

        Args:
            from_course_id: Source course ID
            to_course_id: Destination course ID
            user_ids: Specific user IDs to migrate (None = all enrolled users)
            remove_from_source: Whether to unenroll from source course

        Returns:
            Dict with migration results

        Raises:
            ValueError: If input validation fails
        """
        from_course_id = self._validate_positive_int(from_course_id, "from_course_id")
        to_course_id = self._validate_positive_int(to_course_id, "to_course_id")

        user_ids_php = "null"
        if user_ids:
            validated_ids = [self._validate_positive_int(uid, f"user_ids[{i}]")
                           for i, uid in enumerate(user_ids)]
            user_ids_php = "array(" + ",".join(map(str, validated_ids)) + ")"

        remove_php = "true" if remove_from_source else "false"

        php_code = f'''
$from_course = {from_course_id};
$to_course = {to_course_id};
$specific_users = {user_ids_php};
$remove_from_source = {remove_php};

$users = $specific_users;
if ($users === null) {{
    $enrolled = learndash_get_users_for_course($from_course, array(), false);
    $users = ($enrolled && !empty($enrolled->results)) ? $enrolled->results : array();
}}

$result = array(
    "from_course" => $from_course,
    "to_course" => $to_course,
    "migrated" => array(),
    "failed" => array(),
    "count" => 0
);

foreach ($users as $user_id) {{
    $user = get_user_by("id", $user_id);
    if (!$user) {{
        $result["failed"][] = array("user_id" => $user_id, "error" => "User not found");
        continue;
    }}

    // Enroll in new course
    ld_update_course_access($user_id, $to_course, false);

    // Remove from old course if requested
    if ($remove_from_source) {{
        ld_update_course_access($user_id, $from_course, true);
    }}

    $result["migrated"][] = array(
        "user_id" => $user_id,
        "email" => $user->user_email
    );
    $result["count"]++;
}}

echo json_encode($result);
'''
        cmd = f'eval {shlex.quote(php_code)}'
        result = self.cli.execute(cmd, format=None)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": result}

    def mark_course_complete(
        self,
        user_id: int,
        course_id: int,
        completion_time: Optional[int] = None
    ) -> dict:
        """
        Mark a course as complete for a user.

        Args:
            user_id: User ID
            course_id: Course post ID
            completion_time: Unix timestamp (None = current time)

        Returns:
            Dict with completion status

        Raises:
            ValueError: If input validation fails
        """
        user_id = self._validate_positive_int(user_id, "user_id")
        course_id = self._validate_positive_int(course_id, "course_id")

        time_php = str(completion_time) if completion_time else "time()"

        php_code = f'''
$user_id = {user_id};
$course_id = {course_id};
$completion_time = {time_php};

global $wpdb;

// Insert course completion activity
$wpdb->insert(
    $wpdb->prefix . "learndash_user_activity",
    array(
        "user_id" => $user_id,
        "post_id" => $course_id,
        "course_id" => $course_id,
        "activity_type" => "course",
        "activity_status" => 1,
        "activity_started" => $completion_time - 86400,
        "activity_completed" => $completion_time,
        "activity_updated" => $completion_time
    )
);

// Set user meta for course completion
update_user_meta($user_id, "course_completed_" . $course_id, $completion_time);

$user = get_user_by("id", $user_id);
echo json_encode(array(
    "success" => true,
    "user_id" => $user_id,
    "user_email" => $user->user_email,
    "course_id" => $course_id,
    "completion_time" => $completion_time,
    "completion_date" => date("Y-m-d H:i:s", $completion_time)
));
'''
        cmd = f'eval {shlex.quote(php_code)}'
        result = self.cli.execute(cmd, format=None)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": False, "error": result}

    def get_student_progress(self, user_id: int, course_id: int) -> dict:
        """
        Get detailed progress for a student in a course.

        Args:
            user_id: User ID
            course_id: Course post ID

        Returns:
            Dict with detailed progress data

        Raises:
            ValueError: If input validation fails
        """
        user_id = self._validate_positive_int(user_id, "user_id")
        course_id = self._validate_positive_int(course_id, "course_id")

        php_code = f'''
$user_id = {user_id};
$course_id = {course_id};

$user = get_user_by("id", $user_id);
$progress = learndash_user_get_course_progress($user_id, $course_id);
$course_progress = learndash_course_progress(array(
    "user_id" => $user_id,
    "course_id" => $course_id,
    "array" => true
));

$completed_timestamp = get_user_meta($user_id, "course_completed_" . $course_id, true);

echo json_encode(array(
    "user_id" => $user_id,
    "user_email" => $user ? $user->user_email : "Unknown",
    "course_id" => $course_id,
    "steps_completed" => isset($progress["completed"]) ? $progress["completed"] : 0,
    "steps_total" => isset($progress["total"]) ? $progress["total"] : 0,
    "percentage" => isset($course_progress["percentage"]) ? $course_progress["percentage"] : 0,
    "is_complete" => !empty($completed_timestamp),
    "completion_timestamp" => $completed_timestamp ? (int)$completed_timestamp : null,
    "completion_date" => $completed_timestamp ? date("Y-m-d H:i:s", $completed_timestamp) : null
));
'''
        cmd = f'eval {shlex.quote(php_code)}'
        result = self.cli.execute(cmd, format=None)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"user_id": user_id, "course_id": course_id, "error": result}

    def duplicate_course(
        self,
        source_course_id: int,
        new_title: str,
        new_slug: Optional[str] = None,
        copy_lessons: bool = True
    ) -> dict:
        """
        Duplicate a course with its structure.

        Args:
            source_course_id: Source course post ID
            new_title: Title for the new course
            new_slug: URL slug (auto-generated if not provided)
            copy_lessons: Whether to copy lesson associations

        Returns:
            Dict with new course details

        Raises:
            ValueError: If input validation fails
        """
        source_course_id = self._validate_positive_int(source_course_id, "source_course_id")
        new_title = self._validate_string(new_title, "new_title", max_length=200)

        # Get source course
        source_course = self.cli.get_post(source_course_id)
        if not source_course:
            raise ValueError(f"Source course {source_course_id} not found")

        # Create new course
        slug_param = f'--post_name={shlex.quote(new_slug)}' if new_slug else ''
        cmd = (
            f'post create --post_type=sfwd-courses '
            f'--post_title={shlex.quote(new_title)} '
            f'--post_status=draft {slug_param} --porcelain'
        )
        result = self.cli.execute(cmd, format=None)
        new_course_id = int(result.strip())

        # Copy content
        source_content = source_course.get('content', {}).get('raw', '')
        if source_content:
            self.cli.execute(
                f'post update {shlex.quote(str(new_course_id))} '
                f'--post_content={shlex.quote(source_content)}'
            )

        # Copy key meta
        meta_keys_to_copy = ['_sfwd-courses', 'course_sections', '_thumbnail_id']
        for meta_key in meta_keys_to_copy:
            try:
                meta_value = self.cli.execute(
                    f'post meta get {shlex.quote(str(source_course_id))} {shlex.quote(meta_key)}',
                    format=None
                )
                if meta_value:
                    self.cli.execute(
                        f'post meta update {shlex.quote(str(new_course_id))} '
                        f'{shlex.quote(meta_key)} {shlex.quote(meta_value)}'
                    )
            except Exception:
                pass

        # Copy course steps if requested
        if copy_lessons:
            try:
                steps_cmd = f'post meta get {shlex.quote(str(source_course_id))} ld_course_steps'
                steps_data = self.cli.execute(steps_cmd, format=None)
                if steps_data:
                    # Update course_id in the steps data
                    steps_data = steps_data.replace(
                        f'"course_id";i:{source_course_id}',
                        f'"course_id";i:{new_course_id}'
                    )
                    self.cli.execute(
                        f'post meta update {shlex.quote(str(new_course_id))} '
                        f'ld_course_steps {shlex.quote(steps_data)}'
                    )
            except Exception as e:
                self.logger.warning(f"Failed to copy course steps: {e}")

        self.logger.info(f"Duplicated course {source_course_id} to {new_course_id}")

        return {
            "source_course_id": source_course_id,
            "new_course_id": new_course_id,
            "new_title": new_title,
            "new_slug": new_slug,
            "status": "draft"
        }

    def set_course_steps(
        self,
        course_id: int,
        lesson_ids: list[int],
        enable_shared_steps: bool = True
    ) -> dict:
        """
        Set the course builder structure with specified lessons.

        Args:
            course_id: Course post ID
            lesson_ids: List of lesson IDs to include in order
            enable_shared_steps: Whether to enable shared steps feature

        Returns:
            Dict with update status

        Raises:
            ValueError: If input validation fails
        """
        course_id = self._validate_positive_int(course_id, "course_id")

        if not isinstance(lesson_ids, list) or len(lesson_ids) == 0:
            raise ValueError("lesson_ids must be a non-empty list")

        validated_lessons = [
            self._validate_positive_int(lid, f"lesson_ids[{i}]")
            for i, lid in enumerate(lesson_ids)
        ]

        lesson_ids_php = "array(" + ",".join(map(str, validated_lessons)) + ")"
        shared_steps_php = "true" if enable_shared_steps else "false"

        php_code = f'''
$course_id = {course_id};
$lesson_ids = {lesson_ids_php};
$enable_shared_steps = {shared_steps_php};

// Build the steps structure
$lessons_array = array();
foreach ($lesson_ids as $lesson_id) {{
    $lessons_array[$lesson_id] = array(
        "sfwd-topic" => array(),
        "sfwd-quiz" => array()
    );
}}

$steps = array(
    "steps" => array(
        "h" => array(
            "sfwd-lessons" => $lessons_array,
            "sfwd-quiz" => array()
        )
    ),
    "course_id" => $course_id,
    "version" => "4.25.6",
    "empty" => false,
    "course_builder_enabled" => true,
    "course_shared_steps_enabled" => $enable_shared_steps,
    "steps_count" => count($lesson_ids)
);

update_post_meta($course_id, "ld_course_steps", $steps);
update_post_meta($course_id, "_ld_course_steps_count", count($lesson_ids));

echo json_encode(array(
    "success" => true,
    "course_id" => $course_id,
    "lesson_count" => count($lesson_ids),
    "shared_steps_enabled" => $enable_shared_steps
));
'''
        cmd = f'eval {shlex.quote(php_code)}'
        result = self.cli.execute(cmd, format=None)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": False, "error": result}
