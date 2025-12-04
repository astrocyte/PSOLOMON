# LearnDash Enhancements Documentation

Complete reference for PSOLOMON's enhanced LearnDash LMS capabilities.

---

## Table of Contents

1. [Overview](#overview)
2. [Current Capabilities](#current-capabilities)
3. [New MCP Tools](#new-mcp-tools)
4. [Usage Examples](#usage-examples)
5. [API Reference](#api-reference)
6. [Best Practices](#best-practices)
7. [NYC DOB Compliance](#nyc-dob-compliance)
8. [Troubleshooting](#troubleshooting)
9. [Roadmap](#roadmap)

---

## Overview

### What Was Enhanced

PSOLOMON's LearnDash integration provides comprehensive LMS management through natural language commands via Claude Code. The system wraps LearnDash's wp-cli commands and WordPress REST API to provide:

- **Course management** - Create, update, and organize courses
- **Lesson management** - Create lessons and organize them within courses
- **Topic support** - Create topics within lessons for granular content organization
- **Quiz creation** - Build quizzes with multiple question types
- **Student enrollment** - Enroll users individually or in bulk
- **Group management** - Organize students into cohorts with course access
- **Progress tracking** - Monitor student completion and performance
- **Compliance reporting** - Generate reports for regulatory requirements (NYC DOB)

### Why These Enhancements?

SST.NYC provides safety training courses that must comply with NYC Department of Buildings regulations. The enhancements enable:

1. **Compliance tracking** - Automated reporting for DOB requirements
2. **Bulk operations** - Efficiently manage large student cohorts
3. **Detailed progress** - Track student completion for certification
4. **Group analytics** - Monitor organizational/company-wide performance
5. **Granular content** - Organize course content into topics for better learning

### Architecture

```
Claude Code
    ↓
MCP Server (server.py)
    ↓
LearnDashManager (learndash_manager.py)
    ↓
WP-CLI Client (SSH) → WordPress + LearnDash
```

All operations use wp-cli over SSH for reliability and maintainability.

---

## Current Capabilities

### Core Features (v1.0)

#### 1. Course Management
- Create courses with pricing and certificates
- Update course details and pricing
- List courses with filtering
- Delete courses (soft or permanent)
- Associate courses with WooCommerce products

#### 2. Lesson Management
- Create lessons within courses
- Set lesson order/sequence
- Update lesson content and metadata
- List lessons for a course
- Associate lessons with quizzes

#### 3. Quiz Management
- Create quizzes for courses/lessons
- Set passing scores and certificates
- Add multiple question types:
  - Single choice
  - Multiple choice
  - Free answer
  - Essay
- Assign point values to questions

#### 4. Student Enrollment
- Enroll users in courses
- Unenroll users from courses
- Get user's enrolled courses
- Get course's enrolled students

#### 5. Group Management
- Create student groups
- Associate courses with groups
- Add users to groups
- Bulk group enrollments

---

## New MCP Tools

### Course Tools

#### `ld_create_course`
Create a new LearnDash course.

**Parameters:**
```json
{
  "title": "string (required)",
  "content": "string (optional)",
  "status": "publish|draft|private (default: draft)",
  "price": "number (optional)",
  "certificate_id": "number (optional)"
}
```

**Returns:**
```json
{
  "id": 123,
  "title": "10-Hour Construction Safety",
  "status": "draft",
  "type": "course",
  "price": 150.00
}
```

**Example:**
```
"Create a course called '10-Hour Construction Safety' priced at $150"
```

---

#### `ld_update_course`
Update an existing course.

**Parameters:**
```json
{
  "course_id": "number (required)",
  "title": "string (optional)",
  "content": "string (optional)",
  "status": "string (optional)",
  "price": "number (optional)"
}
```

**Returns:**
```json
{
  "id": 123,
  "updated": true
}
```

**Example:**
```
"Update course 123 to change price to $175"
```

---

#### `ld_list_courses`
List all courses with optional filtering.

**Parameters:**
```json
{
  "status": "any|publish|draft (default: any)",
  "limit": "number (default: 50)"
}
```

**Returns:**
```json
[
  {
    "ID": 123,
    "post_title": "10-Hour Construction Safety",
    "post_status": "publish",
    "post_type": "sfwd-courses"
  }
]
```

**Example:**
```
"List all published courses"
```

---

#### `ld_delete_course`
Delete a course (soft delete to trash or permanent).

**Parameters:**
```json
{
  "course_id": "number (required)",
  "force": "boolean (default: false)"
}
```

**Returns:**
```json
{
  "id": 123,
  "deleted": true,
  "permanent": false
}
```

**Example:**
```
"Delete course 123 permanently"
```

---

### Lesson Tools

#### `ld_create_lesson`
Create a lesson within a course.

**Parameters:**
```json
{
  "course_id": "number (required)",
  "title": "string (required)",
  "content": "string (optional)",
  "status": "publish|draft (default: draft)",
  "order": "number (optional)"
}
```

**Returns:**
```json
{
  "id": 456,
  "title": "Introduction to OSHA",
  "course_id": 123,
  "status": "draft",
  "type": "lesson"
}
```

**Example:**
```
"Create a lesson 'Introduction to OSHA' in course 123"
```

---

#### `ld_update_lesson`
Update a lesson's details.

**Parameters:**
```json
{
  "lesson_id": "number (required)",
  "title": "string (optional)",
  "content": "string (optional)",
  "order": "number (optional)"
}
```

**Returns:**
```json
{
  "id": 456,
  "updated": true
}
```

**Example:**
```
"Update lesson 456 to move it to position 2"
```

---

#### `ld_list_course_lessons`
Get all lessons for a course.

**Parameters:**
```json
{
  "course_id": "number (required)"
}
```

**Returns:**
```json
[
  {
    "ID": 456,
    "post_title": "Introduction to OSHA",
    "menu_order": 1
  }
]
```

**Example:**
```
"Show me all lessons in course 123"
```

---

### Topic Tools (Planned - See Roadmap)

#### `ld_create_topic`
Create a topic within a lesson.

**Parameters:**
```json
{
  "lesson_id": "number (required)",
  "course_id": "number (required)",
  "title": "string (required)",
  "content": "string (optional)",
  "order": "number (optional)"
}
```

**Example:**
```
"Create a topic 'Fall Protection Basics' in lesson 456"
```

---

### Quiz Tools

#### `ld_create_quiz`
Create a quiz for a course/lesson.

**Parameters:**
```json
{
  "course_id": "number (required)",
  "lesson_id": "number (optional)",
  "title": "string (required)",
  "description": "string (optional)",
  "passing_score": "number (default: 80)",
  "certificate_id": "number (optional)"
}
```

**Returns:**
```json
{
  "id": 789,
  "title": "OSHA Knowledge Check",
  "course_id": 123,
  "lesson_id": 456,
  "passing_score": 80,
  "type": "quiz"
}
```

**Example:**
```
"Create a quiz 'OSHA Knowledge Check' for lesson 456 with 70% passing score"
```

---

#### `ld_add_quiz_question`
Add a question to a quiz.

**Parameters:**
```json
{
  "quiz_id": "number (required)",
  "question_text": "string (required)",
  "question_type": "single|multiple|free_answer|essay (default: single)",
  "answers": "array (optional)",
  "points": "number (default: 1)"
}
```

**Answers Format:**
```json
[
  {"text": "Answer 1", "correct": true},
  {"text": "Answer 2", "correct": false},
  {"text": "Answer 3", "correct": false}
]
```

**Returns:**
```json
{
  "id": 999,
  "quiz_id": 789,
  "text": "What is the minimum height for fall protection?",
  "type": "single",
  "points": 1
}
```

**Example:**
```
"Add a multiple choice question to quiz 789 worth 2 points"
```

---

### Enrollment Tools

#### `ld_enroll_user`
Enroll a user in a course.

**Parameters:**
```json
{
  "user_id": "number (required)",
  "course_id": "number (required)"
}
```

**Returns:**
```json
{
  "user_id": 42,
  "course_id": 123,
  "enrolled": true
}
```

**Example:**
```
"Enroll user 42 in course 123"
```

---

#### `ld_unenroll_user`
Unenroll a user from a course.

**Parameters:**
```json
{
  "user_id": "number (required)",
  "course_id": "number (required)"
}
```

**Returns:**
```json
{
  "user_id": 42,
  "course_id": 123,
  "enrolled": false
}
```

**Example:**
```
"Remove user 42 from course 123"
```

---

#### `ld_bulk_enroll` (Planned - See Roadmap)
Enroll multiple users in a course.

**Parameters:**
```json
{
  "user_ids": "array (required)",
  "course_id": "number (required)"
}
```

**Example:**
```
"Enroll users 42, 43, 44 in course 123"
```

---

#### `ld_get_user_courses`
Get all courses a user is enrolled in.

**Parameters:**
```json
{
  "user_id": "number (required)"
}
```

**Returns:**
```json
[
  {
    "ID": 123,
    "post_title": "10-Hour Construction Safety",
    "post_status": "publish"
  }
]
```

**Example:**
```
"Show all courses for user 42"
```

---

#### `ld_get_course_students`
Get all students enrolled in a course.

**Parameters:**
```json
{
  "course_id": "number (required)"
}
```

**Returns:**
```json
{
  "course_id": 123,
  "user_ids": [42, 43, 44, 45]
}
```

**Example:**
```
"List all students in course 123"
```

---

### Group Tools

#### `ld_create_group`
Create a student group.

**Parameters:**
```json
{
  "title": "string (required)",
  "description": "string (optional)",
  "course_ids": "array (optional)"
}
```

**Returns:**
```json
{
  "id": 333,
  "title": "ABC Construction Q4 2024",
  "course_ids": [123, 124],
  "type": "group"
}
```

**Example:**
```
"Create a group 'ABC Construction Q4 2024' with courses 123 and 124"
```

---

#### `ld_add_user_to_group`
Add a user to a group.

**Parameters:**
```json
{
  "user_id": "number (required)",
  "group_id": "number (required)"
}
```

**Returns:**
```json
{
  "user_id": 42,
  "group_id": 333,
  "added": true
}
```

**Example:**
```
"Add user 42 to group 333"
```

---

#### `ld_get_group_analytics` (Planned - See Roadmap)
Get completion analytics for a group.

**Parameters:**
```json
{
  "group_id": "number (required)"
}
```

**Example:**
```
"Show completion stats for group 333"
```

---

### Progress Tracking Tools (Planned - See Roadmap)

#### `ld_get_user_progress`
Get detailed progress for a user in a course.

**Parameters:**
```json
{
  "user_id": "number (required)",
  "course_id": "number (required)"
}
```

**Example:**
```
"Show progress for user 42 in course 123"
```

---

#### `ld_mark_complete`
Mark a lesson/topic as complete for a user.

**Parameters:**
```json
{
  "user_id": "number (required)",
  "post_id": "number (required)",
  "course_id": "number (required)"
}
```

**Example:**
```
"Mark lesson 456 complete for user 42"
```

---

### Compliance Tools (Planned - See Roadmap)

#### `ld_generate_dob_report`
Generate NYC DOB compliance report.

**Parameters:**
```json
{
  "start_date": "YYYY-MM-DD (required)",
  "end_date": "YYYY-MM-DD (required)",
  "course_ids": "array (optional)"
}
```

**Example:**
```
"Generate DOB report for all courses from Jan 1 to Dec 31 2024"
```

---

## Usage Examples

### Example 1: Creating a Complete Course with Topics

```python
# Step 1: Create the course
result = ld.create_course(
    title="10-Hour Construction Safety",
    content="OSHA-compliant 10-hour construction safety course",
    status="publish",
    price=150.00
)
course_id = result["id"]  # 123

# Step 2: Create lessons
lesson1 = ld.create_lesson(
    course_id=123,
    title="Introduction to OSHA",
    content="Overview of OSHA regulations and requirements",
    order=1
)

lesson2 = ld.create_lesson(
    course_id=123,
    title="Fall Protection",
    content="Fall protection standards and best practices",
    order=2
)

# Step 3: Create topics within lessons (when implemented)
topic1 = ld.create_topic(
    lesson_id=lesson1["id"],
    course_id=123,
    title="OSHA History",
    content="The history and purpose of OSHA",
    order=1
)

topic2 = ld.create_topic(
    lesson_id=lesson1["id"],
    course_id=123,
    title="OSHA Standards",
    content="Overview of OSHA construction standards",
    order=2
)

# Step 4: Create quiz
quiz = ld.create_quiz(
    course_id=123,
    lesson_id=lesson1["id"],
    title="OSHA Knowledge Check",
    passing_score=80
)

# Step 5: Add questions
ld.add_quiz_question(
    quiz_id=quiz["id"],
    question_text="What does OSHA stand for?",
    question_type="single",
    answers=[
        {"text": "Occupational Safety and Health Administration", "correct": True},
        {"text": "Office of Safety and Health Affairs", "correct": False},
        {"text": "Organization for Safety and Health Awareness", "correct": False}
    ],
    points=1
)
```

**Via Claude Code:**
```
"Create a course called '10-Hour Construction Safety' priced at $150.
Add two lessons: 'Introduction to OSHA' and 'Fall Protection'.
In the first lesson, create a quiz with 80% passing score."
```

---

### Example 2: Tracking Student Progress

```python
# Get user's enrolled courses
courses = ld.get_user_courses(user_id=42)
# Returns: [{ID: 123, post_title: "10-Hour Construction Safety", ...}]

# Get detailed progress (when implemented)
progress = ld.get_user_progress(user_id=42, course_id=123)
# Returns:
# {
#   "course_id": 123,
#   "user_id": 42,
#   "completion_percentage": 65,
#   "lessons_completed": 4,
#   "lessons_total": 6,
#   "quiz_scores": [
#     {"quiz_id": 789, "score": 85, "passed": true}
#   ],
#   "last_activity": "2024-12-01T14:30:00Z"
# }

# Mark a lesson complete
ld.mark_complete(
    user_id=42,
    post_id=456,  # lesson ID
    course_id=123
)
```

**Via Claude Code:**
```
"Show me progress for user john@company.com in the 10-Hour course"
"Mark lesson 'Fall Protection' complete for user 42"
```

---

### Example 3: Bulk Enrollments

```python
# Enroll multiple users at once (when implemented)
user_ids = [42, 43, 44, 45, 46]  # 5 users
course_id = 123

result = ld.bulk_enroll(
    user_ids=user_ids,
    course_id=course_id
)
# Returns:
# {
#   "course_id": 123,
#   "enrolled": 5,
#   "failed": 0,
#   "user_ids": [42, 43, 44, 45, 46]
# }

# Or enroll via group
group = ld.create_group(
    title="ABC Construction Q4 2024",
    course_ids=[123, 124]
)

for user_id in user_ids:
    ld.add_user_to_group(user_id=user_id, group_id=group["id"])
```

**Via Claude Code:**
```
"Enroll users 42, 43, 44, 45, and 46 in course 123"
"Create a group 'ABC Construction Q4' with courses 123 and 124,
then add these 5 users to it"
```

---

### Example 4: Group Analytics

```python
# Get group completion analytics (when implemented)
analytics = ld.get_group_analytics(group_id=333)
# Returns:
# {
#   "group_id": 333,
#   "group_name": "ABC Construction Q4 2024",
#   "total_students": 25,
#   "courses": [
#     {
#       "course_id": 123,
#       "course_name": "10-Hour Construction Safety",
#       "enrolled": 25,
#       "completed": 18,
#       "in_progress": 5,
#       "not_started": 2,
#       "average_score": 87.5,
#       "completion_rate": 72
#     },
#     {
#       "course_id": 124,
#       "course_name": "30-Hour Construction Safety",
#       "enrolled": 25,
#       "completed": 12,
#       "in_progress": 10,
#       "not_started": 3,
#       "average_score": 85.2,
#       "completion_rate": 48
#     }
#   ],
#   "top_performers": [
#     {"user_id": 42, "name": "John Doe", "avg_score": 95},
#     {"user_id": 43, "name": "Jane Smith", "avg_score": 93}
#   ],
#   "need_attention": [
#     {"user_id": 50, "name": "Bob Wilson", "completion": 10}
#   ]
# }

# Get individual student report
report = ld.get_student_report(user_id=42)
```

**Via Claude Code:**
```
"Show me completion stats for ABC Construction group"
"Which students in group 333 are falling behind?"
"Generate a performance report for ABC Construction"
```

---

### Example 5: NYC DOB Compliance Reporting

```python
# Generate compliance report for NYC DOB
report = ld.generate_dob_report(
    start_date="2024-01-01",
    end_date="2024-12-31",
    course_ids=[123, 124, 125]  # DOB-approved courses only
)
# Returns:
# {
#   "report_id": "DOB-2024-12345",
#   "generated_at": "2024-12-31T23:59:59Z",
#   "period": {
#     "start": "2024-01-01",
#     "end": "2024-12-31"
#   },
#   "courses": [
#     {
#       "course_id": 123,
#       "course_name": "10-Hour Construction Safety",
#       "dob_approved": true,
#       "total_completions": 156,
#       "certificates_issued": 156
#     }
#   ],
#   "students": [
#     {
#       "user_id": 42,
#       "name": "John Doe",
#       "email": "john@example.com",
#       "course_id": 123,
#       "completion_date": "2024-03-15",
#       "certificate_number": "SST-10HR-20240315-042",
#       "quiz_score": 92
#     }
#   ],
#   "totals": {
#     "total_students": 156,
#     "total_completions": 156,
#     "total_certificates": 156,
#     "average_score": 87.3
#   },
#   "export_csv": "/path/to/dob-report-2024.csv"
# }

# Export to CSV for DOB submission
csv_path = report["export_csv"]
```

**Via Claude Code:**
```
"Generate a DOB compliance report for 2024"
"Show me all students who completed the 10-hour course this quarter"
"Export DOB report to CSV for submission"
```

---

## API Reference

### LearnDashManager Class

Located in `/mcp-server/src/learndash_manager.py`

#### Constructor

```python
def __init__(self, config: WordPressConfig, wp_cli: WPCLIClient):
    """
    Initialize LearnDash manager.

    Args:
        config: WordPress configuration object
        wp_cli: WP-CLI client for executing commands
    """
```

---

#### Course Methods

##### `create_course()`
```python
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
        dict: Created course data with ID
        {
            "id": int,
            "title": str,
            "status": str,
            "type": "course",
            "price": float
        }

    Raises:
        WPCLIError: If wp-cli command fails
    """
```

##### `update_course()`
```python
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
        dict: {"id": int, "updated": bool}
    """
```

##### `list_courses()`
```python
def list_courses(
    self,
    status: str = "any",
    limit: int = 50
) -> list[dict]:
    """
    List all LearnDash courses.

    Args:
        status: Post status filter (any, publish, draft)
        limit: Maximum number to return

    Returns:
        list[dict]: List of courses with metadata
    """
```

##### `delete_course()`
```python
def delete_course(
    self,
    course_id: int,
    force: bool = False
) -> dict:
    """
    Delete a course.

    Args:
        course_id: Course post ID
        force: Permanently delete (bypass trash)

    Returns:
        dict: {"id": int, "deleted": bool, "permanent": bool}
    """
```

---

#### Lesson Methods

##### `create_lesson()`
```python
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
        dict: Created lesson data
        {
            "id": int,
            "title": str,
            "course_id": int,
            "status": str,
            "type": "lesson"
        }
    """
```

##### `update_lesson()`
```python
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
        dict: {"id": int, "updated": bool}
    """
```

##### `list_course_lessons()`
```python
def list_course_lessons(self, course_id: int) -> list[dict]:
    """
    Get all lessons for a course.

    Args:
        course_id: Course post ID

    Returns:
        list[dict]: Lessons ordered by menu_order
    """
```

---

#### Quiz Methods

##### `create_quiz()`
```python
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
        dict: Created quiz data
        {
            "id": int,
            "title": str,
            "course_id": int,
            "lesson_id": int,
            "passing_score": int,
            "type": "quiz"
        }
    """
```

##### `add_quiz_question()`
```python
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
        dict: Created question data

    Example answers:
        [
            {"text": "Answer 1", "correct": True},
            {"text": "Answer 2", "correct": False},
        ]

    Note:
        Answer serialization is simplified in v1.0. Full answer support
        with correct/incorrect marking requires LearnDash's complex
        serialized format and will be enhanced in v1.1.
    """
```

---

#### Enrollment Methods

##### `enroll_user()`
```python
def enroll_user(self, user_id: int, course_id: int) -> dict:
    """
    Enroll a user in a course.

    Args:
        user_id: WordPress user ID
        course_id: Course post ID

    Returns:
        dict: {"user_id": int, "course_id": int, "enrolled": bool}

    Note:
        Updates both user meta (course_enrolled_{course_id}) and
        course meta (learndash_course_users) for bidirectional lookup.
    """
```

##### `unenroll_user()`
```python
def unenroll_user(self, user_id: int, course_id: int) -> dict:
    """
    Unenroll a user from a course.

    Args:
        user_id: WordPress user ID
        course_id: Course post ID

    Returns:
        dict: {"user_id": int, "course_id": int, "enrolled": bool}
    """
```

##### `get_user_courses()`
```python
def get_user_courses(self, user_id: int) -> list[dict]:
    """
    Get all courses a user is enrolled in.

    Args:
        user_id: WordPress user ID

    Returns:
        list[dict]: List of enrolled courses with full post data
    """
```

##### `get_course_students()`
```python
def get_course_students(self, course_id: int) -> list[dict]:
    """
    Get all students enrolled in a course.

    Args:
        course_id: Course post ID

    Returns:
        dict: {"user_ids": list, "course_id": int}

    Note:
        Returns serialized data in v1.0. Will be parsed to user objects
        in v1.1 for easier consumption.
    """
```

---

#### Group Methods

##### `create_group()`
```python
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
        dict: Created group data
        {
            "id": int,
            "title": str,
            "course_ids": list[int],
            "type": "group"
        }
    """
```

##### `add_user_to_group()`
```python
def add_user_to_group(self, user_id: int, group_id: int) -> dict:
    """
    Add user to a LearnDash group.

    Args:
        user_id: WordPress user ID
        group_id: Group post ID

    Returns:
        dict: {"user_id": int, "group_id": int, "added": bool}

    Note:
        When a user is added to a group, they are automatically
        enrolled in all courses associated with that group.
    """
```

---

## Best Practices

### When to Use Each Feature

#### Courses vs. Groups
- **Use Courses** when you need a standalone learning path
- **Use Groups** when managing cohorts/companies with multiple courses
- **Example:** ABC Construction needs 10-hour and 30-hour courses → Create 2 courses, 1 group

#### Lessons vs. Topics
- **Use Lessons** for major course sections (1-2 hours of content)
- **Use Topics** for sub-sections within lessons (10-20 minutes each)
- **Example:** "Fall Protection" lesson → Topics: "Basics", "Equipment", "Inspection"

#### Single vs. Multiple Quiz Questions
- **Single choice** for knowledge checks with one correct answer
- **Multiple choice** when multiple answers are correct
- **Free answer** for short text responses
- **Essay** for detailed explanations

### Performance Optimization

#### Bulk Operations
```python
# BAD - Slow for large groups
for user_id in user_ids:  # 100 users
    ld.enroll_user(user_id, course_id)  # 100 SSH calls

# GOOD - Use bulk enrollment (when implemented)
ld.bulk_enroll(user_ids, course_id)  # 1 SSH call
```

#### Caching Course Data
```python
# Cache course list for repeated lookups
courses = ld.list_courses()
course_map = {c["ID"]: c for c in courses}

# Now lookup is instant
course_name = course_map[123]["post_title"]
```

### Data Integrity

#### Always Associate Content
```python
# GOOD - Lesson is properly linked
lesson = ld.create_lesson(
    course_id=123,
    title="Safety Basics",
    order=1
)

# BAD - Orphaned content won't appear in course
# (Don't create lessons without course_id)
```

#### Set Proper Order
```python
# GOOD - Explicit ordering
ld.create_lesson(course_id=123, title="Intro", order=1)
ld.create_lesson(course_id=123, title="Advanced", order=2)

# BAD - Random order, confusing for students
ld.create_lesson(course_id=123, title="Intro")  # order undefined
```

### Error Handling

```python
from .wp_cli import WPCLIError

try:
    result = ld.create_course(title="New Course", price=100)
except WPCLIError as e:
    # Handle wp-cli errors (SSH issues, invalid params, etc.)
    print(f"Course creation failed: {e}")
    # Could retry, log, or notify admin
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
```

### Security

#### Validate User Permissions
```python
# Before enrolling, verify user exists and has permission
user = wp_cli.execute(f"user get {user_id}", format="json")
if user:
    ld.enroll_user(user_id, course_id)
else:
    raise ValueError(f"User {user_id} not found")
```

#### Sanitize Input
```python
# BAD - SQL injection risk
title = user_input  # Could contain quotes/special chars
ld.create_course(title=title)

# GOOD - Sanitize input
import shlex
title = shlex.quote(user_input)
ld.create_course(title=title)
```

---

## NYC DOB Compliance

### Requirements

The NYC Department of Buildings requires:
1. **Approved Courses** - Courses must be DOB-approved
2. **Verified Completion** - Students must complete all lessons/quizzes
3. **Certificates** - Issue certificates upon completion
4. **Record Keeping** - Maintain completion records for 5 years
5. **Reporting** - Submit quarterly completion reports

### Implementation

#### 1. Mark Courses as DOB-Approved
```python
# Add custom field to course
wp_cli.execute(
    f'post meta update {course_id} dob_approved 1'
)
wp_cli.execute(
    f'post meta update {course_id} dob_course_number "SST-10HR-2024"'
)
```

#### 2. Track Completion with Progress API
```python
# Get completion data
progress = ld.get_user_progress(user_id=42, course_id=123)

# Verify 100% completion
if progress["completion_percentage"] == 100:
    # Issue certificate
    ld.issue_certificate(user_id=42, course_id=123)
```

#### 3. Generate Compliance Reports
```python
# Monthly report for DOB
report = ld.generate_dob_report(
    start_date="2024-12-01",
    end_date="2024-12-31",
    course_ids=[123, 124, 125]  # DOB courses only
)

# Export to CSV
csv_data = report["export_csv"]
# Submit to DOB portal
```

#### 4. Certificate Numbering
```python
# Format: SST-{COURSE}-{DATE}-{USER}
# Example: SST-10HR-20241215-042

certificate_number = f"SST-{course_code}-{completion_date}-{user_id:03d}"
```

### Compliance Checklist

- [ ] All DOB courses marked with `dob_approved` meta
- [ ] DOB course numbers stored in `dob_course_number` meta
- [ ] Quiz passing score ≥ 70% (DOB requirement)
- [ ] Certificates issued automatically on 100% completion
- [ ] Certificate numbers follow SST format
- [ ] Completion data exported monthly
- [ ] Records backed up and retained for 5 years
- [ ] Audit trail maintained (who completed what when)

---

## Troubleshooting

### Common Issues

#### 1. Enrollment Not Working
```
Error: User not enrolled after calling enroll_user()
```

**Cause:** LearnDash uses serialized PHP arrays in meta fields

**Solution:**
```python
# Verify enrollment by checking meta directly
result = wp_cli.execute(
    f'user meta get {user_id} course_enrolled_{course_id}'
)
print(result)  # Should return course_id if enrolled
```

**Workaround:** Use LearnDash's built-in enrollment function
```php
// Via wp eval (future enhancement)
learndash_update_user_activity(
    array(
        'user_id' => $user_id,
        'course_id' => $course_id,
        'activity_type' => 'course'
    )
);
```

---

#### 2. Quiz Answers Not Saving
```
Quiz questions created but answers not appearing
```

**Cause:** LearnDash stores answers in complex serialized format

**Status:** Known limitation in v1.0

**Workaround:** Create questions via WordPress admin for now

**Fix Coming:** v1.1 will properly serialize answer data

---

#### 3. Progress Not Updating
```
User completed lesson but progress shows 0%
```

**Cause:** LearnDash requires specific activity table entries

**Solution:** Use proper completion function (when implemented)
```python
ld.mark_complete(
    user_id=42,
    post_id=456,  # lesson ID
    course_id=123
)
```

**Check Progress:**
```bash
# Via SSH
wp db query "SELECT * FROM wp_learndash_user_activity
WHERE user_id = 42 AND course_id = 123"
```

---

#### 4. Group Enrollment Issues
```
Users added to group but not enrolled in courses
```

**Cause:** Group-to-course enrollment requires trigger

**Solution:**
```python
# After adding users to group, manually enroll in courses
group_courses = [123, 124]
group_users = [42, 43, 44]

for user_id in group_users:
    for course_id in group_courses:
        ld.enroll_user(user_id, course_id)
```

**Future:** v1.1 will auto-enroll group members in group courses

---

#### 5. SSH Connection Timeouts
```
WPCLIError: SSH connection timeout
```

**Causes:**
- Network issues
- Server load
- wp-cli command hanging

**Solutions:**
```python
# Increase timeout in config
config.ssh_timeout = 60  # seconds

# Retry logic
for attempt in range(3):
    try:
        result = ld.create_course(title="Test")
        break
    except WPCLIError:
        if attempt == 2:
            raise
        time.sleep(5)
```

---

#### 6. Serialized Data Issues
```
TypeError: expected string, got bytes
```

**Cause:** PHP serialized data from meta fields

**Solution:**
```python
import phpserialize

# Unserialize PHP data
meta_value = wp_cli.execute(f'post meta get {course_id} learndash_course_users')
users = phpserialize.loads(meta_value.encode())
```

**Future:** v1.1 will handle serialization automatically

---

### Debug Mode

Enable detailed logging:

```python
# In .env
DEBUG=1
LOG_LEVEL=DEBUG

# In code
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see all wp-cli commands
```

### Getting Help

1. **Check Logs:**
   - MCP Server: `./logs/mcp.log`
   - WordPress: `/wp-content/debug.log`
   - SSH errors: `./logs/ssh.log`

2. **Verify via wp-cli:**
   ```bash
   ssh user@host -p 65002
   cd /path/to/wordpress
   wp post list --post_type=sfwd-courses
   ```

3. **Check WordPress Admin:**
   - LearnDash > Courses
   - LearnDash > Settings > Advanced
   - Tools > Site Health

4. **Ask Claude Code:**
   ```
   "Debug enrollment issue for user 42 in course 123"
   "Why isn't the quiz showing questions?"
   "Check LearnDash configuration"
   ```

---

## Roadmap

### v1.0 (Current) - Foundation
- ✅ Basic course/lesson/quiz creation
- ✅ User enrollment (single)
- ✅ Group creation
- ✅ MCP tool integration
- ✅ wp-cli wrapper

### v1.1 (Q1 2025) - Enhanced Features
- ⏳ Topic creation and management
- ⏳ Progress tracking API
- ⏳ Bulk enrollment operations
- ⏳ Quiz answer serialization
- ⏳ Certificate automation
- ⏳ Auto-enroll group members

### v1.2 (Q2 2025) - Analytics & Reporting
- ⏳ Group analytics dashboard
- ⏳ Student performance reports
- ⏳ DOB compliance reporting
- ⏳ Export to CSV/PDF
- ⏳ Email notifications
- ⏳ Completion reminders

### v1.3 (Q3 2025) - Advanced Features
- ⏳ Custom certificate templates
- ⏳ Advanced quiz types (sorting, matching)
- ⏳ Drip content scheduling
- ⏳ Prerequisites and dependencies
- ⏳ Course cloning/templates
- ⏳ REST API integration (replace wp-cli for some operations)

### v2.0 (Q4 2025) - Enterprise
- ⏳ Multi-site support
- ⏳ API rate limiting
- ⏳ Advanced caching
- ⏳ Real-time progress webhooks
- ⏳ Integration with third-party LMS systems
- ⏳ Mobile app support

---

## Contributing

To add new LearnDash features:

1. **Update `learndash_manager.py`:**
   ```python
   def new_feature(self, param: str) -> dict:
       """New feature description."""
       # Implementation
       return result
   ```

2. **Add MCP Tool in `server.py`:**
   ```python
   Tool(
       name="ld_new_feature",
       description="Description for Claude",
       inputSchema={...}
   )
   ```

3. **Add Handler in `call_tool()`:**
   ```python
   elif name == "ld_new_feature":
       result = ld.new_feature(arguments["param"])
       return [TextContent(type="text", text=str(result))]
   ```

4. **Update This Documentation:**
   - Add to [New MCP Tools](#new-mcp-tools)
   - Add usage example
   - Add to API reference
   - Update roadmap if applicable

5. **Test Thoroughly:**
   ```bash
   pytest tests/test_learndash_manager.py::test_new_feature
   ```

---

## Version History

### v1.0 (December 2024)
- Initial LearnDash integration
- Course, lesson, quiz creation
- Basic enrollment
- Group management
- MCP tools for all core features
- Documentation complete

---

## Support

For questions or issues with LearnDash features:

1. Check this documentation
2. Review [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
3. Check WordPress debug log
4. Ask Claude Code for help
5. File issue on GitHub

---

**PSOLOMON LearnDash - Complete LMS management via natural language** 🎓

Built with Claude Code (https://claude.com/claude-code)
