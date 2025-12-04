# LearnDash Testing Guide for PSOLOMON

Complete testing guide for the enhanced LearnDash functionality on staging.sst.nyc

## Prerequisites

Before testing, ensure:
- ✅ Staging server is running (staging.sst.nyc)
- ✅ LearnDash plugin is active
- ✅ PSOLOMON MCP server is connected
- ✅ You have admin access to WordPress
- ✅ At least one test course exists

---

## Testing Phases

### Phase 1: Basic CRUD Operations (Foundation)

These tests verify the fundamental create, read, update, delete operations work correctly.

#### 1.1 Course Management

**Create Course:**
```
"Create a test course called 'PSOLOMON Test Course' with description 'This is for testing'"
```

**Verify:** Course appears in LearnDash → Courses

**Update Course:**
```
"Update the PSOLOMON Test Course title to 'Updated Test Course'"
```

**Verify:** Course title changed in WordPress admin

**List Courses:**
```
"List all LearnDash courses"
```

**Verify:** Your test course appears in the list

#### 1.2 Lesson Management

**Create Lessons:**
```
"Create 3 lessons for course [ID]:
- Lesson 1: Introduction to Safety
- Lesson 2: PPE Requirements
- Lesson 3: Fall Prevention"
```

**Verify:** All 3 lessons appear under the course

**Update Lesson:**
```
"Update lesson [ID] to change the title to 'Introduction to Workplace Safety'"
```

**Verify:** Lesson title updated in course builder

#### 1.3 Topic Management (NEW)

**Create Topics:**
```
"Create 2 topics for lesson [ID]:
- Topic 1: Safety Overview
- Topic 2: OSHA Regulations"
```

**Verify:** Topics appear under the lesson

**Update Topic:**
```
"Update topic [ID] with new content about recent OSHA changes"
```

**Verify:** Topic content updated

#### 1.4 Quiz Management

**Create Quiz:**
```
"Create a quiz called 'Safety Knowledge Check' for course [ID] with 80% passing score"
```

**Verify:** Quiz appears in course structure

**Update Quiz:**
```
"Update quiz [ID] to have 3 attempts and 90% passing score"
```

**Verify:** Quiz settings updated in WordPress admin

**Add Questions:**
```
"Add a multiple choice question to quiz [ID]: 'What is the primary purpose of PPE?' with answers:
- Protect workers from hazards (correct)
- Look professional (incorrect)
- Company requirement (incorrect)"
```

**Verify:** Question appears in quiz

---

### Phase 2: Content Modification (NEW Features)

These tests verify the new content modification methods work correctly.

#### 2.1 Reordering Lessons

**Setup:** Create course with 3 lessons (A, B, C)

**Test 1 - Basic Reorder:**
```
"Reorder the lessons in course [ID] so lesson C is first, then A, then B"
```

**Expected:** Lessons appear in order C, A, B in course builder
**Verify:** Check `menu_order` in database (0, 1, 2)

**Test 2 - Ownership Validation (CRITICAL):**

Create lesson D in a different course, then try:
```
"Reorder lessons in course [ID] with order: [C, A, D, B]"
```

**Expected:** Error message: `"Lesson [D_ID] belongs to course [OTHER], not course [ID]"`
**Verify:** Original order unchanged, clear error shown

**Test 3 - Duplicate Detection:**
```
"Reorder lessons in course [ID]: [A, B, A]"
```

**Expected:** Error message: `"lesson_order contains duplicate IDs"`
**Verify:** Order unchanged

**Test 4 - Empty List:**
```
"Reorder lessons in course [ID] with empty list"
```

**Expected:** Error about empty list
**Verify:** Order unchanged

#### 2.2 Reordering Topics

**Setup:** Create lesson with 4 topics (T1, T2, T3, T4)

**Test 1 - Basic Reorder:**
```
"Reorder topics in lesson [ID] to: T4, T2, T1, T3"
```

**Expected:** Topics appear in specified order
**Verify:** `menu_order` in database reflects new order

**Test 2 - Ownership Validation:**

Create topic T5 in different lesson, then:
```
"Reorder topics in lesson [ID]: [T1, T5, T2]"
```

**Expected:** Error: `"Topic [T5_ID] belongs to lesson [OTHER]"`
**Verify:** Order unchanged

#### 2.3 Moving Lessons Between Courses

**Setup:** Course A and Course B, Lesson L1 in Course A

**Test 1 - Basic Move:**
```
"Move lesson [L1_ID] from course [A_ID] to course [B_ID]"
```

**Expected:** Lesson now appears under Course B
**Verify:**
- `course_id` meta = B_ID
- `ld_course_{B_ID}` meta exists
- `ld_course_{A_ID}` meta deleted

**Test 2 - Wrong Source Course (Warning):**
```
"Move lesson [L1_ID] from course [WRONG_ID] to course [B_ID]"
```

**Expected:** Warning logged but move completes
**Verify:** Lesson moved to Course B

**Test 3 - Move to Same Course:**
```
"Move lesson [L1_ID] from course [A_ID] to course [A_ID]"
```

**Expected:** Works but unnecessary
**Verify:** No errors, lesson stays in Course A

#### 2.4 Duplicating Lessons

**Setup:** Lesson with title "Original Lesson" and 3 topics

**Test 1 - Duplicate with Topics:**
```
"Duplicate lesson [ID] including all topics"
```

**Expected:**
- New lesson created with title "Copy of Original Lesson"
- New lesson is draft status
- 3 new topics created
- All topics also drafts

**Verify:**
- Count lessons (should be +1)
- Count topics (should be +3)
- Check titles have "Copy of" prefix
- Check all are drafts

**Test 2 - Duplicate without Topics:**
```
"Duplicate lesson [ID] but don't include topics"
```

**Expected:**
- New lesson created
- Zero topics created

**Verify:** Lesson exists, no topics

**Test 3 - Custom Title:**
```
"Duplicate lesson [ID] with title 'Advanced Safety Module'"
```

**Expected:** New lesson has specified title
**Verify:** No "Copy of" prefix

**Test 4 - Lesson with Zero Topics:**
```
"Duplicate lesson [EMPTY_ID] including topics"
```

**Expected:** New lesson, empty topics list
**Verify:** `duplicated_topics: []` in response

#### 2.5 Batch Updating Lessons

**Setup:** Create 5 lessons (L1-L5)

**Test 1 - Successful Batch:**
```
"Batch update these lessons:
- Lesson [L1_ID]: Change title to 'Updated L1'
- Lesson [L2_ID]: Change content to 'New content for L2'
- Lesson [L3_ID]: Change order to 10"
```

**Expected:** All 3 updates succeed
**Verify:**
- `successful: 3, failed: 0`
- All lessons updated correctly

**Test 2 - Mixed Success/Failure:**
```
"Batch update:
- Lesson [L1_ID]: title to 'Good'
- Lesson [999999]: title to 'Bad ID'
- Lesson [L2_ID]: title to 'Good 2'"
```

**Expected:** 2 succeed, 1 fails
**Verify:**
- `successful: 2, failed: 1`
- Error details include bad ID message

**Test 3 - Circuit Breaker (CRITICAL):**

Create batch with 10 invalid IDs in a row:
```
"Batch update lessons: [999991, 999992, 999993, 999994, 999995, 999996, L1_ID, L2_ID]"
```

**Expected:**
- Aborts after 5th failure
- Remaining items (999996, L1_ID, L2_ID) marked `"not_attempted"`
- `aborted: true` in response

**Verify:** Only 5 attempts made, circuit breaker activated

**Test 4 - Empty List:**
```
"Batch update with empty list"
```

**Expected:** Error about empty updates list
**Verify:** No operations attempted

#### 2.6 Setting Prerequisites

**Setup:** 3 lessons (L1, L2, L3) in a course

**Test 1 - Single Prerequisite:**
```
"Make lesson [L2_ID] require completion of lesson [L1_ID] first"
```

**Expected:** L2 locked until L1 completed
**Verify:**
- `lesson_prerequisite` meta set on L2
- LearnDash shows lock icon on L2

**Test 2 - Multiple Prerequisites:**
```
"Make lesson [L3_ID] require lessons [L1_ID] and [L2_ID]"
```

**Expected:** L3 locked until both L1 and L2 completed
**Verify:**
- `lesson_prerequisites` meta set (comma-separated)
- ⚠️ **CRITICAL:** Test if LearnDash actually enforces this
- Try to access L3 without completing L1 and L2

**Test 3 - Clear Prerequisites:**
```
"Remove all prerequisites from lesson [L3_ID]"
```

**Expected:** L3 accessible immediately
**Verify:** Both meta keys deleted

**Test 4 - Self-Reference Prevention (CRITICAL):**
```
"Make lesson [L1_ID] require lesson [L1_ID]"
```

**Expected:** Error: `"Circular dependency detected"`
**Verify:** No meta set, clear error message

**Test 5 - Indirect Circular (KNOWN LIMITATION):**

Setup: L1 → L2 → L3, then try:
```
"Make lesson [L1_ID] require lesson [L3_ID]"
```

**Expected:** ⚠️ This will NOT be prevented (known limitation)
**Verify:** Creates invalid state, document this limitation

#### 2.7 Course Builder Structure

**Setup:** Course with 6 lessons

**Test 1 - Create Module Structure:**
```
"Update course [ID] with this structure:
- Module 1 'Introduction': Lessons [L1, L2]
- Module 2 'Advanced': Lessons [L3, L4, L5]
- Module 3 'Assessment': Lesson [L6]"
```

**Expected:** Structure saved to `ld_course_builder` meta
**Verify:**
- JSON stored in meta field
- Each lesson `menu_order` updated
- ⚠️ **CRITICAL:** Check if LearnDash course builder UI shows this

**Test 2 - LearnDash Integration (CRITICAL):**

After Test 1, open WordPress admin → Course Builder

**Expected:** ⚠️ MAY NOT INTEGRATE with LearnDash UI
**Verify:** If structure doesn't appear, document as custom implementation

**Test 3 - Invalid Structure:**
```
"Update course structure with invalid JSON"
```

**Expected:** Validation error
**Verify:** No changes made to course

---

### Phase 3: User Enrollment & Progress

#### 3.1 Enrollment

**Enroll User:**
```
"Enroll user john@example.com in course [ID]"
```

**Verify:** User appears in course students list

**Bulk Enroll:**
```
"Enroll these 5 users in course [ID]: [emails...]"
```

**Verify:** All 5 users enrolled, `successful: 5`

#### 3.2 Progress Tracking

**Get User Progress:**
```
"Show me progress for user [ID] in course [ID]"
```

**Verify:** Returns completion percentage, steps completed

**Get Course Completion Rate:**
```
"What's the completion rate for course [ID]?"
```

**Verify:** Returns percentage, student counts

---

### Phase 4: Analytics & Reporting

#### 4.1 Course Analytics

**List Course Students:**
```
"Who is enrolled in course [ID]?"
```

**Verify:** Returns list with names, emails

**Completion Statistics:**
```
"Show me completion stats for course [ID]"
```

**Verify:** Total students, completed, in progress, not started

#### 4.2 Group Management

**Create Group:**
```
"Create a group called 'ACME Construction' with courses [ID1, ID2]"
```

**Verify:** Group created, courses associated

**Bulk Add to Group:**
```
"Add these 10 users to group [ID]"
```

**Verify:** All users added

**Group Progress:**
```
"Show me progress for group [ID]"
```

**Verify:** Returns group-wide completion rate

#### 4.3 Compliance Reporting

**Export Completion Report:**
```
"Generate completion report for course [ID] for Q4 2024"
```

**Verify:** Returns list of completions with timestamps

---

### Phase 5: Security Testing

#### 5.1 Command Injection Prevention

**Test 1 - Malicious Course Title:**
```
"Create course with title: Test\"; rm -rf /tmp/*; echo \""
```

**Expected:** Course created with literal title (shell chars escaped)
**Verify:** No command executed, course exists with full title

**Test 2 - Malicious Lesson Content:**
```
"Create lesson with content: $(whoami) or `id`"
```

**Expected:** Content stored as literal text
**Verify:** No command execution

**Test 3 - SQL Injection Patterns:**
```
"Create course: Test' OR '1'='1"
```

**Expected:** Course created with literal title
**Verify:** No SQL injection

#### 5.2 Input Validation

**Test 1 - Negative IDs:**
```
"Update course with ID -1"
```

**Expected:** ValueError: "course_id must be a positive integer"

**Test 2 - Empty Strings:**
```
"Create course with empty title"
```

**Expected:** ValueError about empty title

**Test 3 - Excessive Lengths:**
```
"Create course with 300 character title"
```

**Expected:** ValueError about max length (200 chars)

**Test 4 - Invalid Enums:**
```
"Create course with status 'invalid'"
```

**Expected:** ValueError about allowed status values

**Test 5 - Out of Range:**
```
"Create quiz with passing score 150"
```

**Expected:** ValueError: score must be 0-100

---

### Phase 6: Edge Cases & Error Handling

#### 6.1 Missing Resources

**Test 1 - Non-existent Course:**
```
"Update course 999999"
```

**Expected:** wp-cli error about missing post

**Test 2 - Non-existent User:**
```
"Enroll user 999999 in course [ID]"
```

**Expected:** Error about invalid user

#### 6.2 Boundary Conditions

**Test 1 - Zero Items:**
```
"Reorder lessons with empty list"
```

**Expected:** ValueError

**Test 2 - Single Item:**
```
"Reorder lessons with single lesson [ID]"
```

**Expected:** Works, lesson menu_order = 0

**Test 3 - Large Batch (100 items):**
```
"Batch update 100 lessons"
```

**Expected:** All complete (or circuit breaker if failures)
**Verify:** Performance is acceptable

---

## Testing Checklist

Use this checklist to track testing progress:

### Foundation (Phase 1)
- [ ] Create course
- [ ] Update course
- [ ] List courses
- [ ] Delete course
- [ ] Create lessons
- [ ] Update lesson
- [ ] Create topics
- [ ] Update topic
- [ ] Create quiz
- [ ] Update quiz
- [ ] Add quiz questions

### Content Modification (Phase 2) - NEW
- [ ] Reorder lessons (basic)
- [ ] Reorder lessons (ownership validation)
- [ ] Reorder lessons (duplicate detection)
- [ ] Reorder topics (basic)
- [ ] Reorder topics (ownership validation)
- [ ] Move lesson between courses
- [ ] Duplicate lesson with topics
- [ ] Duplicate lesson without topics
- [ ] Batch update (successful)
- [ ] Batch update (circuit breaker)
- [ ] Set single prerequisite
- [ ] Set multiple prerequisites
- [ ] Prerequisites self-reference prevention
- [ ] Course builder structure
- [ ] Course builder LearnDash integration

### User Management (Phase 3)
- [ ] Enroll user
- [ ] Bulk enroll users
- [ ] Get user progress
- [ ] Get course completion rate

### Analytics (Phase 4)
- [ ] List course students
- [ ] Course completion stats
- [ ] Create group
- [ ] Group progress
- [ ] Export completion report

### Security (Phase 5)
- [ ] Command injection prevention
- [ ] SQL injection prevention
- [ ] Input validation (negatives, empty, long)
- [ ] Enum validation
- [ ] Range validation

### Edge Cases (Phase 6)
- [ ] Non-existent resources
- [ ] Boundary conditions
- [ ] Large batch operations

---

## Critical Tests (Must Pass Before Production)

These tests MUST pass before deploying to production:

### 🔴 CRITICAL - Security
1. ✅ Command injection prevention (course/lesson titles)
2. ✅ Input validation (IDs, strings, ranges)

### 🔴 CRITICAL - Data Integrity
3. ⚠️ Ownership validation (reorder lessons from different courses)
4. ⚠️ Ownership validation (reorder topics from different lessons)
5. ⚠️ Circuit breaker (batch operations)

### 🔴 CRITICAL - LearnDash Integration
6. ⚠️ Prerequisites format (comma-separated vs serialized)
7. ⚠️ Course builder structure (custom vs LearnDash native)

### 🟡 IMPORTANT - User Experience
8. ⚠️ Error messages are clear and actionable
9. ⚠️ Duplicate detection prevents user mistakes
10. ⚠️ Progress tracking shows accurate data

---

## Known Limitations

Document these limitations after testing:

1. **Indirect Circular Prerequisites:** System only prevents direct self-reference (L1→L1), not indirect cycles (L1→L2→L3→L1)

2. **Course Builder Integration:** `update_course_builder_structure()` may not integrate with LearnDash's native course builder UI

3. **Prerequisites Format:** Multiple prerequisites use comma-separated format - may need PHP serialization for production

4. **Rollback:** Reorder operations have no rollback - if operation fails mid-way, partial state remains

5. **Performance:** Duplicating lesson with 50+ topics may be slow (each topic creates separately)

---

## Reporting Issues

When you find issues, document:

1. **Test name** and phase
2. **Expected behavior**
3. **Actual behavior**
4. **Error messages** (full text)
5. **Steps to reproduce**
6. **Database state** (course/lesson IDs involved)
7. **WordPress/LearnDash versions**

---

## Post-Testing Actions

After completing all tests:

1. **Document findings** in LEARNDASH_TESTING_RESULTS.md
2. **Update LEARNDASH_ENHANCEMENTS.md** with known limitations
3. **Create GitHub issues** for any bugs found
4. **Update agent prompt** with tested workflows
5. **Plan production rollout** based on test results

---

## Questions for Testing

Answer these during testing:

1. Does LearnDash recognize comma-separated prerequisites?
2. Does course builder structure integrate with LearnDash UI?
3. What happens with indirect circular prerequisites?
4. How long does duplicating 50-topic lesson take?
5. Do reordered lessons appear correctly in student view?
6. Does ownership validation prevent all invalid operations?
7. Does circuit breaker activate at correct threshold?
8. Are error messages helpful for troubleshooting?

---

**Testing on staging.sst.nyc before any production deployment!**
