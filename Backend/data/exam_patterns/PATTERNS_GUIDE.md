# Exam Patterns Guide - Mentor AI Platform

Complete guide to exam pattern JSON files for diagnostic test generation.

## 📋 Overview

This directory contains standardized exam pattern definitions for:
- **JEE Main** - Joint Entrance Examination Main
- **JEE Advanced** - Joint Entrance Examination Advanced  
- **NEET** - National Eligibility cum Entrance Test

All patterns are scaled to **200 questions** for comprehensive diagnostic testing.

## 📁 Files

1. `jee_main_pattern.json` - JEE Main exam pattern
2. `jee_advanced_pattern.json` - JEE Advanced exam pattern
3. `neet_pattern.json` - NEET exam pattern

## 🎯 Pattern Structure

### Common Fields

All pattern files include:

```json
{
  "exam_name": "string",
  "exam_code": "string",
  "description": "string",
  "total_questions": 200,
  "duration_minutes": 180,
  "max_marks": number,
  "subjects": [...],
  "question_types": [...],
  "marking_scheme": {...},
  "difficulty_distribution": {...},
  "sections": [...],
  "general_instructions": [...],
  "metadata": {...}
}
```

## 📊 Exam Comparisons

### Question Distribution

| Exam | Total | Physics | Chemistry | Mathematics | Biology |
|------|-------|---------|-----------|-------------|---------|
| **JEE Main** | 200 | 60 (30%) | 60 (30%) | 80 (40%) | - |
| **JEE Advanced** | 200 | 66 (33%) | 67 (33%) | 67 (34%) | - |
| **NEET** | 200 | 40 (20%) | 40 (20%) | - | 120 (60%) |

### Question Types

#### JEE Main
- **Single Correct MCQ** (70%): 4 marks, -1 for incorrect
- **Numerical** (30%): 4 marks, no negative marking

#### JEE Advanced
- **Single Correct MCQ** (40%): 3 marks, -1 for incorrect
- **Multiple Correct MCQ** (30%): 4 marks, -2 for incorrect, partial marks
- **Numerical** (20%): 4 marks, no negative marking
- **Matrix Match** (10%): 3 marks, partial marking

#### NEET
- **Single Correct MCQ** (100%): 4 marks, -1 for incorrect

### Difficulty Distribution

| Exam | Easy | Medium | Hard |
|------|------|--------|------|
| **JEE Main** | 30% | 50% | 20% |
| **JEE Advanced** | 20% | 50% | 30% |
| **NEET** | 35% | 45% | 20% |

## 📝 Detailed Specifications

### JEE Main Pattern

**File**: `jee_main_pattern.json`

**Key Features**:
- 200 questions total
- 180 minutes duration
- 800 maximum marks
- Two question types: MCQ and Numerical
- No negative marking for numerical questions

**Subject Breakdown**:
```
Physics:      60 questions (240 marks)
  - MCQ:      42 questions (70%)
  - Numerical: 18 questions (30%)

Chemistry:    60 questions (240 marks)
  - MCQ:      42 questions (70%)
  - Numerical: 18 questions (30%)

Mathematics:  80 questions (320 marks)
  - MCQ:      56 questions (70%)
  - Numerical: 24 questions (30%)
```

**Marking Scheme**:
- MCQ: +4 correct, -1 incorrect, 0 unattempted
- Numerical: +4 correct, 0 incorrect, 0 unattempted

### JEE Advanced Pattern

**File**: `jee_advanced_pattern.json`

**Key Features**:
- 200 questions total
- 180 minutes duration
- 720 maximum marks
- Four question types with varying marks
- Partial marking for multiple correct questions

**Subject Breakdown**:
```
Physics:      66 questions (240 marks)
  - Single MCQ:    26 questions (40%)
  - Multiple MCQ:  20 questions (30%)
  - Numerical:     13 questions (20%)
  - Matrix Match:   7 questions (10%)

Chemistry:    67 questions (240 marks)
  - Single MCQ:    27 questions (40%)
  - Multiple MCQ:  20 questions (30%)
  - Numerical:     13 questions (20%)
  - Matrix Match:   7 questions (10%)

Mathematics:  67 questions (240 marks)
  - Single MCQ:    27 questions (40%)
  - Multiple MCQ:  20 questions (30%)
  - Numerical:     13 questions (20%)
  - Matrix Match:   7 questions (10%)
```

**Marking Scheme**:
- Single MCQ: +3 correct, -1 incorrect
- Multiple MCQ: +4 all correct, +1 partial, -2 any incorrect
- Numerical: +4 correct, 0 incorrect
- Matrix Match: +3 correct, +1 partial, 0 incorrect

### NEET Pattern

**File**: `neet_pattern.json`

**Key Features**:
- 200 questions total
- 180 minutes duration
- 800 maximum marks
- All Multiple Choice Questions (MCQ)
- Biology has highest weightage (60%)

**Subject Breakdown**:
```
Physics:   40 questions (160 marks)
  - All MCQ: 40 questions (100%)

Chemistry: 40 questions (160 marks)
  - All MCQ: 40 questions (100%)

Botany:    60 questions (240 marks)
  - All MCQ: 60 questions (100%)

Zoology:   60 questions (240 marks)
  - All MCQ: 60 questions (100%)
```

**Marking Scheme**:
- MCQ: +4 correct, -1 incorrect, 0 unattempted

## 🔧 Usage

### Loading Patterns

```python
import json

# Load JEE Main pattern
with open('data/exam_patterns/jee_main_pattern.json') as f:
    jee_main = json.load(f)

print(f"Exam: {jee_main['exam_name']}")
print(f"Questions: {jee_main['total_questions']}")
print(f"Duration: {jee_main['duration_minutes']} minutes")
```

### Accessing Subject Information

```python
for subject in jee_main['subjects']:
    print(f"{subject['name']}: {subject['question_count']} questions")
    print(f"  Weightage: {subject['weightage_percentage']}%")
    print(f"  Max Marks: {subject['max_marks']}")
```

### Getting Marking Scheme

```python
for q_type, scheme in jee_main['marking_scheme'].items():
    print(f"{q_type}:")
    print(f"  Correct: +{scheme['correct_marks']}")
    print(f"  Incorrect: {scheme['incorrect_marks']}")
```

## ✅ Validation

All JSON files are validated for:
- ✅ Valid JSON syntax
- ✅ Required fields present
- ✅ Correct data types
- ✅ Logical consistency (totals match)

### Validation Script

```bash
# Validate all patterns
python3 -c "
import json
patterns = ['jee_main_pattern.json', 'jee_advanced_pattern.json', 'neet_pattern.json']
for pattern in patterns:
    data = json.load(open(f'data/exam_patterns/{pattern}'))
    print(f'✓ {data[\"exam_name\"]}: {data[\"total_questions\"]} questions')
"
```

## 📈 Pattern Metadata

Each pattern includes metadata:

```json
{
  "metadata": {
    "version": "2024",
    "last_updated": "2024-01-15",
    "conducting_body": "NTA/IIT",
    "exam_mode": "CBT/Paper-based",
    "language_options": ["English", "Hindi", ...]
  }
}
```

## 🎓 Topic Coverage

### JEE Main Topics

**Physics**: Mechanics, Thermodynamics, Electromagnetism, Optics, Modern Physics, Waves

**Chemistry**: Physical Chemistry, Organic Chemistry, Inorganic Chemistry

**Mathematics**: Algebra, Calculus, Coordinate Geometry, Trigonometry, Vectors, Probability

### JEE Advanced Topics

Similar to JEE Main but with more depth and complexity.

### NEET Topics

**Physics**: Mechanics, Thermodynamics, Electrodynamics, Optics, Modern Physics

**Chemistry**: Physical Chemistry, Organic Chemistry, Inorganic Chemistry

**Biology**: 
- Botany: Plant Physiology, Genetics, Ecology, Diversity, Cell Biology
- Zoology: Human Physiology, Genetics, Ecology, Diversity, Cell Biology

## 🔄 Updates

Patterns are updated annually to reflect:
- Changes in exam structure
- Updated syllabus
- New question types
- Modified marking schemes

**Last Updated**: January 2024

## 📚 Integration

These patterns integrate with:
- Pattern Loader (`utils/pattern_loader.py`)
- Question Distribution Service (`services/question_distribution.py`)
- Test Assembler (`services/test_assembler.py`)
- Test Validator (`services/test_validator.py`)

## 🤝 Contributing

To update patterns:
1. Modify the JSON file
2. Validate JSON syntax
3. Test with pattern loader
4. Update this documentation
5. Update version and last_updated fields

## 📞 Support

For questions about exam patterns:
- Check official NTA/IIT websites
- Refer to latest exam notifications
- Contact Mentor AI support team

---

**Status**: ✅ Production Ready

All patterns validated and tested. Ready for diagnostic test generation.
