"""LearnDash LMS management for course creation and editing."""

from typing import Optional, Literal
from .config import WordPressConfig
from .wp_cli import WPCLIClient


class LearnDashManager:
    """Manage LearnDash courses, lessons, quizzes, and enrollments."""

    def __init__(self, config: WordPressConfig, wp_cli: WPCLIClient):
        self.config = config
        self.cli = wp_cli

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
        """
        # Create course post
        cmd = f'post create --post_type=sfwd-courses --post_title="{title}" --post_status={status}'

        if content:
            cmd += f' --post_content="{content}"'

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
        """
        updates = []

        if title:
            updates.append(f'--post_title="{title}"')
        if content:
            updates.append(f'--post_content="{content}"')
        if status:
            updates.append(f'--post_status={status}')

        if updates:
            cmd = f'post update {course_id} {" ".join(updates)}'
            self.cli.execute(cmd)

        if price is not None:
            self.cli.execute(
                f'post meta update {course_id} _sfwd-courses "_sfwd-courses[sfwd-courses_course_price]" {price}'
            )

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
        """
        cmd = f'post delete {course_id}'
        if force:
            cmd += ' --force'

        self.cli.execute(cmd)
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
        """
        cmd = f'post create --post_type=sfwd-lessons --post_title="{title}" --post_status={status}'

        if content:
            cmd += f' --post_content="{content}"'

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
        """Update lesson details."""
        updates = []

        if title:
            updates.append(f'--post_title="{title}"')
        if content:
            updates.append(f'--post_content="{content}"')

        if updates:
            cmd = f'post update {lesson_id} {" ".join(updates)}'
            self.cli.execute(cmd)

        if order is not None:
            self.cli.execute(f'post meta update {lesson_id} lesson_order {order}')

        return {"id": lesson_id, "updated": True}

    def list_course_lessons(self, course_id: int) -> list[dict]:
        """Get all lessons for a course."""
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
        """
        cmd = f'post create --post_type=sfwd-quiz --post_title="{title}" --post_status=publish'

        if description:
            cmd += f' --post_content="{description}"'

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

        Example answers:
            [
                {"text": "Answer 1", "correct": True},
                {"text": "Answer 2", "correct": False},
            ]
        """
        cmd = f'post create --post_type=sfwd-question --post_title="{question_text}" --post_status=publish'

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
        """
        # LearnDash stores enrollments in user meta
        self.cli.execute(
            f'user meta add {user_id} course_enrolled_{course_id} {course_id}'
        )

        # Also update course user list
        cmd = f'post meta add {course_id} learndash_course_users {user_id}'
        self.cli.execute(cmd)

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
        """
        self.cli.execute(
            f'user meta delete {user_id} course_enrolled_{course_id}'
        )
        self.cli.execute(
            f'post meta delete {course_id} learndash_course_users {user_id}'
        )

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
        """
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
        """
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
        """
        cmd = f'post create --post_type=groups --post_title="{title}" --post_status=publish'

        if description:
            cmd += f' --post_content="{description}"'

        result = self.cli.execute(cmd, format="json")
        group_id = result if isinstance(result, int) else int(result)

        # Associate courses
        if course_ids:
            for course_id in course_ids:
                self.cli.execute(
                    f'post meta add {group_id} learndash_group_enrolled_{course_id} {course_id}'
                )

        return {
            "id": group_id,
            "title": title,
            "course_ids": course_ids or [],
            "type": "group",
        }

    def add_user_to_group(self, user_id: int, group_id: int) -> dict:
        """Add user to a LearnDash group."""
        self.cli.execute(
            f'user meta add {user_id} learndash_group_users_{group_id} {group_id}'
        )
        self.cli.execute(
            f'post meta add {group_id} learndash_group_users {user_id}'
        )

        return {"user_id": user_id, "group_id": group_id, "added": True}
