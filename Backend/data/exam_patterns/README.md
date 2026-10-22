# Exam Patterns for Mentor AI

This directory contains JSON files defining exam patterns for diagnostic test generation.

## Supported Exams

- **JEE Main** (`jee_main.json`)
- **JEE Advanced** (`jee_advanced.json`)
- **NEET** (`neet.json`)

## Pattern Structure

Each exam pattern JSON file must include:

```json
{
  "exam_name": "string",
  "total_questions": "integer",
  "subjects": [
    {
      "name": "string",
      "question_count": "integer",
      "weightage": "float (0-100)"
    }
  ],
  "question_types": [
    {
      "type": "string (MCQ, Numerical, Integer, MSQ, Assertion-Reason)",
      "count_per_subject": "integer",
      "marks": "float"
    }
  ],
  "marking_scheme": {
    "correct_marks": "float (positive)",
    "incorrect_marks": "float (negative or zero)",
    "unattempted_marks": "float (default: 0)"
  },
  "duration_minutes": "integer",
  "difficulty_distribution": {
    "easy": "float (0-100)",
    "medium": "float (0-100)",
    "hard": "float (0-100)"
  }
}
```

## Validation Rules

1. **Subject Questions**: Sum of all subject question counts must equal `total_questions`
2. **Subject Weightage**: Sum of all subject weightages must equal 100%
3. **Difficulty Distribution**: Easy + Medium + Hard percentages must equal 100%
4. **Marking Scheme**: `incorrect_marks` must be negative or zero
5. **Positive Values**: All counts, marks, and duration must be positive

## Usage

```python
from utils.pattern_loader import PatternLoader

# Initialize loader
loader = PatternLoader()

# Load a specific pattern
jee_main = loader.load_pattern("JEE_MAIN")
print(f"Total questions: {jee_main.total_questions}")

# Load all patterns
all_patterns = loader.get_all_patterns()

# Access pattern details
for subject in jee_main.subjects:
    print(f"{subject.name}: {subject.question_count} questions")
```

## Adding New Patterns

1. Create a new JSON file in this directory (e.g., `sat.json`)
2. Follow the pattern structure above
3. Add the exam type to `ExamType` enum in `utils/pattern_loader.py`
4. Ensure all validation rules are met

## Pattern Details

### JEE Main
- 90 questions (30 per subject: Physics, Chemistry, Mathematics)
- 180 minutes duration
- MCQ (20) + Numerical (10) per subject
- +4 marks for correct, -1 for incorrect
- Difficulty: 30% Easy, 50% Medium, 20% Hard

### JEE Advanced
- 54 questions (18 per subject: Physics, Chemistry, Mathematics)
- 180 minutes duration
- MCQ (8) + MSQ (6) + Numerical (4) per subject
- +3 marks for correct, -1 for incorrect
- Difficulty: 20% Easy, 50% Medium, 30% Hard

### NEET
- 180 questions (45 per subject: Physics, Chemistry, Botany, Zoology)
- 180 minutes duration
- All MCQ (45 per subject)
- +4 marks for correct, -1 for incorrect
- Difficulty: 35% Easy, 45% Medium, 20% Hard
