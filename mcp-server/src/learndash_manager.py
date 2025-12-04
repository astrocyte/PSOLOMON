"""LearnDash LMS management for course creation and editing."""

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

        # Set course meta
        if price is not None:
            self.cli.execute(
                f'post meta update {course_id} _sfwd-courses "_sfwd-courses[sfwd-courses_course_price]" {price}'
            )

        if certificate_id:
            self.cli.execute(
                f'post meta update {course_id} _sfwd-courses "_sfwd-courses[sfwd-courses_certificate]" {certificate_id}'
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
            cmd = f'post update {course_id} {" ".join(updates)}'
            self.cli.execute(cmd)

        if price is not None:
            self.cli.execute(
                f'post meta update {course_id} _sfwd-courses "_sfwd-courses[sfwd-courses_course_price]" {price}'
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

        cmd = f'post delete {course_id}'
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

        # Associate with course
        self.cli.execute(
            f'post meta update {lesson_id} course_id {course_id}'
        )
        self.cli.execute(
            f'post meta update {lesson_id} ld_course_{course_id} {course_id}'
        )

        # Set order if provided
        if order is not None:
            self.cli.execute(
                f'post meta update {lesson_id} lesson_order {order}'
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
            cmd = f'post update {lesson_id} {" ".join(updates)}'
            self.cli.execute(cmd)

        if order is not None:
            self.cli.execute(f'post meta update {lesson_id} lesson_order {order}')

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

        cmd = f'post list --post_type=sfwd-lessons --meta_key=course_id --meta_value={course_id} --orderby=menu_order --order=ASC'
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

        # Set quiz meta
        self.cli.execute(f'post meta update {quiz_id} course_id {course_id}')

        if lesson_id:
            self.cli.execute(f'post meta update {quiz_id} lesson_id {lesson_id}')

        # Set passing score
        self.cli.execute(
            f'post meta update {quiz_id} _sfwd-quiz "_sfwd-quiz[sfwd-quiz_passingpercentage]" {passing_score}'
        )

        if certificate_id:
            self.cli.execute(
                f'post meta update {quiz_id} _sfwd-quiz "_sfwd-quiz[sfwd-quiz_certificate]" {certificate_id}'
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

        # Associate with quiz
        self.cli.execute(f'post meta update {question_id} quiz_id {quiz_id}')

        # Set question type
        type_map = {
            "single": "single",
            "multiple": "multiple",
            "free_answer": "free_answer",
            "essay": "essay_text",
        }
        self.cli.execute(
            f'post meta update {question_id} question_type {type_map[question_type]}'
        )

        # Set points
        self.cli.execute(f'post meta update {question_id} question_points {points}')

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

        # LearnDash stores enrollments in user meta
        self.cli.execute(
            f'user meta add {user_id} course_enrolled_{course_id} {course_id}'
        )

        # Also update course user list
        cmd = f'post meta add {course_id} learndash_course_users {user_id}'
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
            f'user meta delete {user_id} course_enrolled_{course_id}'
        )
        self.cli.execute(
            f'post meta delete {course_id} learndash_course_users {user_id}'
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
        cmd = f'user meta list {user_id} --fields=meta_key,meta_value'
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

        cmd = f'post meta get {course_id} learndash_course_users'
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

        # Associate courses
        if course_ids:
            for course_id in course_ids:
                self.cli.execute(
                    f'post meta add {group_id} learndash_group_enrolled_{course_id} {course_id}'
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
            f'user meta add {user_id} learndash_group_users_{group_id} {group_id}'
        )
        self.cli.execute(
            f'post meta add {group_id} learndash_group_users {user_id}'
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

        # Add group leader meta
        self.cli.execute(
            f'post meta add {group_id} learndash_group_leaders {user_id}'
        )
        self.cli.execute(
            f'user meta add {user_id} learndash_group_leaders_{group_id} {group_id}'
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

        # Associate with lesson and course
        self.cli.execute(f'post meta update {topic_id} lesson_id {lesson_id}')

        if course_id:
            self.cli.execute(f'post meta update {topic_id} course_id {course_id}')
            self.cli.execute(f'post meta update {topic_id} ld_course_{course_id} {course_id}')

        # Set order if provided
        if order is not None:
            self.cli.execute(f'post meta update {topic_id} topic_order {order}')

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

        cmd = f'post list --post_type=sfwd-topic --meta_key=lesson_id --meta_value={lesson_id} --orderby=menu_order --order=ASC'
        return self.cli.execute(cmd, format="json")

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

        # Get user course progress meta
        cmd = f'user meta get {user_id} course_progress_{course_id}'
        progress_data = self.cli.execute(cmd)

        # Get completed lessons
        cmd = f'user meta list {user_id} --fields=meta_key,meta_value'
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

        # Get all enrolled users
        cmd = f'post meta get {course_id} learndash_course_users'
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

        # Get group users
        cmd = f'post meta get {group_id} learndash_group_users'
        group_users_data = self.cli.execute(cmd)

        # Get associated courses
        cmd = f'post meta list {group_id} --fields=meta_key,meta_value'
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

        # Get quiz meta
        cmd = f'post meta list {quiz_id} --fields=meta_key,meta_value'
        quiz_meta = self.cli.execute(cmd, format="json")

        # Get quiz settings
        passing_score = next(
            (int(m['meta_value']) for m in quiz_meta
             if 'passingpercentage' in m['meta_key']),
            80
        )

        # Get quiz questions count
        questions_cmd = f'post list --post_type=sfwd-question --meta_key=quiz_id --meta_value={quiz_id}'
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

        # Get user meta for certificates
        cmd = f'user meta list {user_id} --fields=meta_key,meta_value'
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

        # Get all enrolled users
        cmd = f'post meta get {course_id} learndash_course_users'
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
