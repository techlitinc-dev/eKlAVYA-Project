# Gamification Router API Documentation

## Overview

The Gamification Router provides endpoints for gamification features including achievements, daily challenges, streaks, points, and leaderboards. It implements game mechanics to increase student engagement and motivation.

## Base URL
```
/api/gamification
```

## Endpoints

### 1. Get Achievements

**Endpoint:** `GET /api/gamification/achievements`

**Description:** Get all achievements for a student with unlock status and progress information.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/gamification/achievements?student_id=student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "total_points": 850,
  "unlocked_count": 8,
  "total_count": 25,
  "achievements": [
    {
      "achievement_id": "ach_7day_streak",
      "name": "Week Warrior",
      "description": "Study for 7 consecutive days",
      "icon": "🔥",
      "category": "streak",
      "points": 100,
      "rarity": "rare",
      "requirement": "7-day study streak",
      "unlocked": true,
      "progress": 100.0,
      "earned_date": "2024-01-12T00:00:00Z",
      "last_progress_update": "2024-01-12T00:00:00Z"
    },
    {
      "achievement_id": "ach_100_questions",
      "name": "Century",
      "description": "Solve 100 questions",
      "icon": "💯",
      "category": "questions",
      "points": 150,
      "rarity": "epic",
      "requirement": "100 questions solved",
      "unlocked": false,
      "progress": 75.0,
      "current_count": 75,
      "target_count": 100,
      "last_progress_update": "2024-01-15T14:30:00Z"
    },
    {
      "achievement_id": "ach_first_perfect_score",
      "name": "Perfectionist",
      "description": "Get 100% in any test",
      "icon": "⭐",
      "category": "performance",
      "points": 200,
      "rarity": "legendary",
      "requirement": "100% score in a test",
      "unlocked": false,
      "progress": 50.0,
      "attempts": 1,
      "successful_attempts": 1,
      "last_progress_update": "2024-01-10T16:45:00Z"
    }
  ],
  "recent_unlocks": [
    {
      "achievement_id": "ach_5day_streak",
      "name": "Dedicated Learner",
      "earned_date": "2024-01-10T00:00:00Z",
      "points": 50
    }
  ],
  "next_achievements": [
    {
      "achievement_id": "ach_30day_streak",
      "name": "Month Master",
      "points": 300,
      "progress_percentage": 23.3
    }
  ]
}
```

#### Achievement Categories
- **Streak**: Consecutive study days
- **Questions**: Question-solving milestones
- **Performance**: Test performance achievements
- **Time**: Study time milestones
- **Special**: Event-based achievements

#### Rarity Levels
- **Common**: Easy to achieve, low points
- **Uncommon**: Moderate difficulty, medium points
- **Rare**: Difficult to achieve, high points
- **Epic**: Very difficult, very high points
- **Legendary**: Extremely difficult, maximum points

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve achievements

---

### 2. Claim Achievement

**Endpoint:** `POST /api/gamification/achievements/claim/{achievement_id}`

**Description:** Claim an unlocked achievement. Awards points and updates achievement status.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/gamification/achievements/claim/ach_100_questions?student_id=student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `achievement_id`: Achievement identifier (required)
- `student_id`: Student identifier (required)

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Achievement claimed: ach_100_questions",
  "points_earned": 150,
  "new_total_points": 1000,
  "achievement_details": {
    "achievement_id": "ach_100_questions",
    "name": "Century",
    "description": "Solve 100 questions",
    "icon": "💯",
    "points": 150,
    "rarity": "epic",
    "unlocked": true,
    "progress": 100.0,
    "claimed_date": "2024-01-15T15:30:00Z"
  },
  "streak_bonus": {
    "current_streak": 8,
    "bonus_points": 40,
    "reason": "8-day consecutive study streak"
  }
}
```

#### Claim Process
1. Verify achievement is unlocked
2. Award achievement points
3. Update achievement status
4. Check for streak bonuses
5. Update total points balance

#### Error Scenarios
- **400 Bad Request:** Achievement not unlocked or invalid ID
- **401 Unauthorized:** Authentication required
- **404 Not Found:** Achievement doesn't exist
- **500 Internal Server Error:** Failed to claim achievement

---

### 3. Get Daily Challenge

**Endpoint:** `GET /api/gamification/challenge/daily`

**Description:** Get today's daily challenge question. Challenges reset daily and offer bonus points for completion.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/gamification/challenge/daily" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "challenge_id": "challenge_2024-01-15",
  "date": "2024-01-15",
  "question": {
    "question_id": "q_daily_123",
    "question_text": "What is the derivative of sin(2x)?",
    "options": {
      "A": "cos(2x)",
      "B": "2cos(2x)",
      "C": "-2sin(2x)",
      "D": "2sin(2x)"
    },
    "correct_answer": "B",
    "explanation": "Using the chain rule: d/dx[sin(2x)] = cos(2x) × 2 = 2cos(2x)",
    "difficulty": "medium",
    "subject": "Mathematics",
    "topic": "Calculus",
    "hints_available": 2,
    "time_bonus": 30
  },
  "difficulty": "medium",
  "points": 50,
  "bonus_points": 10,
  "time_limit": 180,
  "subject": "Mathematics",
  "topic": "Calculus",
  "attempts_today": 0,
  "best_time_today": null,
  "completion_rate": 0.0
}
```

#### Challenge Features
- Daily reset at midnight UTC
- Difficulty varies by student level
- Bonus points for speed completion
- Hint system with point penalties
- Streak multipliers for consecutive days

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve daily challenge

---

### 4. Submit Daily Challenge

**Endpoint:** `POST /api/gamification/challenge/daily/submit`

**Description:** Submit answer for today's daily challenge. Awards points based on correctness and speed.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/gamification/challenge/daily/submit" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "challenge_2024-01-15",
    "answer": "B",
    "time_taken": 95
  }'
```

#### Request Body
- `challenge_id`: Daily challenge identifier (required)
- `answer`: Student's answer (required)
- `time_taken`: Time taken in seconds (optional)

#### Expected Response (200 OK)
```json
{
  "challenge_id": "challenge_2024-01-15",
  "correct": true,
  "points_earned": 60,
  "correct_answer": "B",
  "explanation": "Using the chain rule: d/dx[sin(2x)] = cos(2x) × 2 = 2cos(2x)",
  "rank": 42,
  "total_participants": 150,
  "time_bonus": false,
  "streak_bonus": {
    "consecutive_days": 5,
    "bonus_multiplier": 1.2,
    "bonus_points": 12
  },
  "performance_metrics": {
    "accuracy": 85.7,
    "average_time": 112.5,
    "improvement": "+5.2%"
  }
}
```

#### Scoring System
- **Base Points**: 50 for correct answer
- **Time Bonus**: Extra points for quick completion
- **Streak Multiplier**: Bonus multiplier for consecutive days
- **Rank Points**: Additional points based on daily ranking

#### Error Scenarios
- **400 Bad Request:** Invalid challenge ID or already submitted
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to submit challenge

---

### 5. Get Challenge Leaderboard

**Endpoint:** `GET /api/gamification/challenge/leaderboard`

**Description:** Get daily challenge leaderboard. Shows top performers for today's challenge.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/gamification/challenge/leaderboard?challenge_date=2024-01-15" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `challenge_date`: Challenge date (defaults to today) (optional)

#### Expected Response (200 OK)
```json
{
  "date": "2024-01-15",
  "entries": [
    {
      "rank": 1,
      "student_name": "Student A",
      "points": 60,
      "time": 95,
      "streak": 7,
      "badge": "🥇"
    },
    {
      "rank": 2,
      "student_name": "Student B",
      "points": 60,
      "time": 102,
      "streak": 5,
      "badge": "🥈"
    },
    {
      "rank": 3,
      "student_name": "Student C",
      "points": 50,
      "time": 85,
      "streak": 3,
      "badge": "🥉"
    }
  ],
  "student_rank": 42,
  "total_participants": 150,
  "top_percentage": 2.0,
  "awards": [
    {
      "type": "speed_demon",
      "recipient": "Student A",
      "reason": "Fastest correct answer under 60 seconds"
    },
    {
      "type": "early_bird",
      "recipients": ["Student A", "Student B"],
      "reason": "Completed within first hour of challenge release"
    }
  ]
}
```

#### Leaderboard Features
- Real-time ranking updates
- Multiple ranking criteria (points, time)
- Badge system for top performers
- Special awards for exceptional performance
- Historical leaderboard access

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **404 Not Found:** No leaderboard for specified date
- **500 Internal Server Error:** Failed to retrieve leaderboard

---

### 6. Get Streak Information

**Endpoint:** `GET /api/gamification/streak`

**Description:** Get student's study streak information including current streak, longest streak, and available streak protection.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/gamification/streak?student_id=student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "current_streak": 12,
  "longest_streak": 15,
  "streak_protection_available": true,
  "last_activity_date": "2024-01-15T18:30:00Z",
  "streak_milestones": [7, 10, 14, 21, 30],
  "streak_history": [
    {
      "start_date": "2024-01-03T00:00:00Z",
      "end_date": "2024-01-15T00:00:00Z",
      "duration_days": 12,
      "points_earned": 120,
      "bonus_multiplier": 1.5
    },
    {
      "start_date": "2023-12-20T00:00:00Z",
      "end_date": "2024-01-02T00:00:00Z",
      "duration_days": 15,
      "points_earned": 150,
      "bonus_multiplier": 2.0
    }
  ],
  "next_milestone": {
    "days": 14,
    "bonus_points": 200,
    "special_reward": "Streak Master Badge"
  },
  "protection_info": {
    "available_until": "2024-01-16T23:59:59Z",
    "cost_to_activate": 100,
    "description": "Protects current streak for 24 hours if missed"
  }
}
```

#### Streak Features
- **Current Streak**: Consecutive days of activity
- **Longest Streak**: Personal best record
- **Milestones**: Achievement levels at various day counts
- **Streak Protection**: Shield to preserve streak
- **History**: Past streak performance

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve streak info

---

### 7. Get Points History

**Endpoint:** `GET /api/gamification/points/history`

**Description:** Get points earning history for a student with breakdown by time periods and activities.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/gamification/points/history?student_id=student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "total_points": 2450,
  "points_today": 120,
  "points_this_week": 680,
  "points_this_month": 2450,
  "points_breakdown": {
    "achievements": 850,
    "daily_challenges": 600,
    "study_sessions": 500,
    "streak_bonuses": 300,
    "bonus_activities": 200
  },
  "history": [
    {
      "date": "2024-01-15",
      "activity": "Completed topic",
      "points": 50,
      "description": "Thermodynamics",
      "multiplier": 1.0
    },
    {
      "date": "2024-01-15",
      "activity": "Daily challenge",
      "points": 60,
      "description": "Correct answer - Kinematics",
      "multiplier": 1.2
    },
    {
      "date": "2024-01-14",
      "activity": "Achievement unlocked",
      "points": 100,
      "description": "Week Warrior",
      "multiplier": 1.0
    },
    {
      "date": "2024-01-13",
      "activity": "Streak bonus",
      "points": 40,
      "description": "7-day streak maintained",
      "multiplier": 1.5
    }
  ],
  "trends": {
    "daily_average": 81.7,
    "weekly_growth": 15.2,
    "monthly_total": 2450,
    "projection_next_month": 2680
  }
}
```

#### Points Categories
- **Achievements**: Milestone completions
- **Daily Challenges**: Daily puzzle completions
- **Study Sessions**: Learning activity points
- **Streak Bonuses**: Consecutive day rewards
- **Bonus Activities**: Special event rewards

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve points history

---

## Testing Workflows

### Complete Gamification Workflow

1. **Get Achievements**
   ```bash
   curl -X GET "/api/gamification/achievements?student_id=student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Get Daily Challenge**
   ```bash
   curl -X GET "/api/gamification/challenge/daily" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Submit Challenge**
   ```bash
   curl -X POST "/api/gamification/challenge/daily/submit" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"challenge_id": "challenge_2024-01-15", "answer": "B"}'
   ```

4. **Get Leaderboard**
   ```bash
   curl -X GET "/api/gamification/challenge/leaderboard" \
     -H "Authorization: Bearer TOKEN"
   ```

5. **Check Streak**
   ```bash
   curl -X GET "/api/gamification/streak?student_id=student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

6. **Get Points History**
   ```bash
   curl -X GET "/api/gamification/points/history?student_id=student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

7. **Claim Achievement**
   ```bash
   curl -X POST "/api/gamification/achievements/claim/ach_100_questions?student_id=student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## Gamification Mechanics

### Achievement System
- **Progressive Unlocking**: Achievements unlock based on progress
- **Rarity Tiers**: Common to legendary with increasing difficulty
- **Progress Tracking**: Real-time progress updates
- **Milestone Rewards**: Special rewards for key achievements

### Challenge System
- **Daily Challenges**: New puzzle each day
- **Difficulty Scaling**: Adapts to student level
- **Time Bonuses**: Rewards for quick completion
- **Leaderboard Rankings**: Competitive element with badges

### Streak System
- **Consecutive Days**: Tracks daily activity
- **Milestone Rewards**: Bonus points at thresholds
- **Streak Protection**: Shield to preserve streaks
- **Recovery Mechanism**: Ways to maintain motivation

### Points Economy
- **Multiple Sources**: Points from various activities
- **Multipliers**: Bonuses for exceptional performance
- **Balance Tracking**: Real-time point totals
- **Redemption**: Future features for point usage

---

## Common Issues and Solutions

### 1. Achievement Not Unlocking
**Problem:** Achievement progress not updating or unlocking
**Solution:** 
- Verify underlying activity is completed
- Check achievement criteria and thresholds
- Ensure progress tracking is working
- Refresh achievement data if needed

### 2. Streak Reset Incorrectly
**Problem:** Streak resetting when it shouldn't
**Solution:** 
- Check activity detection logic
- Verify timezone handling for daily reset
- Ensure streak protection is working
- Check for missed days and grace periods

### 3. Points Not Awarding
**Problem:** Points not being added after activities
**Solution:** 
- Verify point calculation logic
- Check for duplicate submissions
- Ensure point transactions are atomic
- Review point award triggers

### 4. Leaderboard Not Updating
**Problem:** Leaderboard showing stale data
**Solution:** 
- Check real-time update mechanism
- Verify scoring calculations
- Ensure ranking algorithm is correct
- Check for caching issues

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing Gamification Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Gamification Router implements game mechanics for student engagement
- Achievement system with rarity tiers and progress tracking
- Daily challenges with time bonuses and leaderboards
- Streak system with milestone rewards and protection
- Points economy with multiple earning sources and multipliers
- Real-time rankings and competitive elements

**Question:** Can you help me debug this issue by:
1. Analyzing the gamification logic and state management
2. Checking if achievement/streak/point calculations are correct
3. Identifying common issues with game mechanics
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Student ID: [STUDENT_ID]
- Achievement ID: [ACHIEVEMENT_ID_IF_APPLICABLE]
- Challenge ID: [CHALLENGE_ID_IF_APPLICABLE]
- Current Streak: [CURRENT_STREAK_IF_APPLICABLE]
- Points Balance: [POINTS_BALANCE_IF_APPLICABLE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.gamification_models.Achievement`
- `models.gamification_models.StudentAchievements`
- `models.gamification_models.DailyChallenge`
- `models.gamification_models.DailyChallengeSubmission`
- `models.gamification_models.DailyChallengeResult`
- `models.gamification_models.Leaderboard`
- `models.gamification_models.StreakInfo`
- `models.gamification_models.PointsHistory`

### Services
- `services.gamification_service.GamificationService`
- `services.achievement_service.AchievementService`
- `services.streak_service.StreakService`
- `services.leaderboard_service.LeaderboardService`

---

## Performance Considerations

1. **Real-time Updates**: Leaderboard and streak updates
2. **Caching**: Achievement and points data cached
3. **Database Optimization**: Efficient queries for rankings
4. **Atomic Operations**: Point transactions are atomic
5. **Background Tasks**: Daily challenge generation and reset

---

## Security Notes

1. **Access Control**: Students can only access their own data
2. **Fair Play**: Anti-cheating measures for challenges
3. **Point Security**: Secure point transactions and validation
4. **Privacy Controls**: Leaderboard privacy options available
5. **Audit Logging**: All gamification actions are logged

---

## Testing Best Practices

1. **Achievement Testing**: Test unlock conditions and progress
2. **Streak Testing**: Verify streak logic and edge cases
3. **Points Testing**: Test point calculations and transactions
4. **Leaderboard Testing**: Test ranking accuracy and updates
5. **Integration Testing**: Verify with study and analytics systems