---
sessionId: session-261011-184608-17qr
---

# Requirements

### Overview & Goals
Build a personal learning and study app using Python and Flet that guides users through an onboarding pretest, provides mock tests for licensure and general exams, measures IQ and EQ, delivers personalized lessons, and tracks progress over time.

### User Stories
- As a new user, I want to take a short pretest when I first open the app so I can see my baseline knowledge.
- As a user, I want to create an account so my progress, scores, and preferences are saved.
- As a student, I want to take mock tests for licensure exams or any subject at a chosen difficulty so I can prepare effectively.
- As a learner, I want to take IQ and EQ assessments so I can understand my cognitive and emotional strengths.
- As a struggling student, I want personalized lessons targeting my weakest areas so I can improve efficiently.
- As a user, I want to see my statistics and get recommendations so I can track my growth.

### Scope
**In Scope:**
- Onboarding pretest (general knowledge, ~10 questions)
- User account system (local SQLite)
- Mock test mode (licensure exams + curriculum subjects, configurable difficulty and question count)
- Cognitive IQ assessment (verbal, numerical, logical, spatial reasoning)
- Emotional EQ assessment (scenario-based questions)
- Learning mode (personalized lessons based on weak areas)
- Mini-quizzes / homeworks
- Statistics and progress tracking
- Personalized recommendations

**Out of Scope:**
- Multi-user / cloud sync
- Real-time multiplayer features
- AI-generated content
- Mobile app deployment (desktop Flet app only for now)

# Technical Design

### Current Implementation
The app is built with **Flet** (Python GUI framework). Key existing components:
- `main.py` (480 lines): Single-file Flet app with screens for home, profile, statistics, recommendations, subject menu, and a quiz engine. Cognitive test, EQ, and lessons are stub screens.
- `core/loader.py`: Loads questions from JSON files — `data/curriculum/` (subjects with topics) and `data/cognitive/` (domains × tiers). Cognitive files exist but are empty.
- `core/scoring.py`: Simple `calculate_score()` and `grade_label()` utilities.
- `data/curriculum/subjects.json`: 7 subject categories with topics, each with JSON question files (e.g., `mathematics/algebra.json`). Questions have `id`, `type`, `difficulty`, `question`, `choices`, `answer`, `explanation`.
- `data/cognitive/`: Empty JSON files for verbal, numerical, logical, spatial × beginner/intermediate/advanced.
- `results/`: Empty directory for future result exports.

### Key Decisions
- **Onboarding flow**: Pretest first, then optional account creation — matches the user's description.
- **Persistence**: Local SQLite database (`core/database.py`) for users, test results, and progress. No server needed.
- **Question data**: Continue using JSON files for questions and lessons — consistent with existing pattern.
- **Quiz engine**: Extend the existing `run_quiz()` engine in `main.py` rather than rewriting — it already handles rendering, scoring, and results.
- **IQ scoring**: Weighted scoring across 4 cognitive domains × 3 difficulty tiers, normalized to an IQ-like scale.
- **Learning mode**: Auto-generated from test results — the recommender analyzes weak areas and suggests lessons.

### Proposed Changes

#### 1. Database Layer (`core/database.py`)
- SQLite database with tables: `users`, `test_results`, `progress`, `preferences`.
- Functions: `create_user()`, `get_user()`, `save_test_result()`, `get_user_stats()`, `get_weak_areas()`.

#### 2. Onboarding Flow (`main.py`)
- New `show_onboarding()` screen: welcome message + short pretest.
- New `show_signup()` screen: name, email, password (hashed locally).
- New `show_login()` screen for returning users.
- `show_home()` checks login state; redirects to onboarding if needed.

#### 3. Cognitive IQ Assessment (`main.py` + `data/cognitive/`)
- Populate cognitive JSON files with questions.
- New `show_cognitive_test()` screen: selects domain, runs tiered questions.
- `calculate_iq_score()` in `core/scoring.py`: combines domain scores into an IQ estimate.

#### 4. EQ Assessment (`main.py` + `data/emotional/`)
- New `data/emotional/eq_assessment.json` with scenario-based questions.
- New `show_eq_assessment()` screen.
- `calculate_eq_score()` in `core/scoring.py`.

#### 5. Mock Test Mode (`main.py` + `data/licensure/`)
- New `data/licensure/` directory with exam categories and question banks.
- `load_licensure_exam()` in `core/loader.py`.
- `show_mock_test_menu()`: choose exam type, difficulty, question count, timer.
- Timer integration in quiz engine.

#### 6. Learning Mode (`main.py` + `core/recommender.py` + `data/lessons/`)
- `core/recommender.py`: analyzes test results to find weak topics, generates study plan.
- `data/lessons/`: JSON files with lesson content (explanations, key concepts, practice questions).
- `show_learning_mode()`: personalized study plan view.
- `show_lesson()`: lesson content + embedded practice quiz.
- Mini-quiz / homework feature: 5-question daily quizzes.

#### 7. Statistics & Recommendations (`main.py`)
- `show_statistics()`: score history, subject breakdowns, trends.
- `show_recommendations()`: personalized suggestions from recommender.
- CSV export to `results/` directory.

### Architecture Diagram

``` mermaid
graph LR
    A[main.py UI Layer] --> B[core/loader.py Data Loading]
    A --> C[core/scoring.py Scoring]
    A --> D[core/database.py Persistence]
    A --> E[core/recommender.py Recommendations]
    B --> F[data/curriculum/ Questions]
    B --> G[data/cognitive/ IQ Questions]
    B --> H[data/emotional/ EQ Questions]
    B --> I[data/licensure/ Exam Questions]
    B --> J[data/lessons/ Lesson Content]
    C --> D
    E --> D
    D --> K[results/ Exports]
```

### File Structure
```
core/
  __init__.py
  database.py       (NEW - SQLite persistence)
  loader.py         (MODIFIED - add licensure loader)
  recommender.py    (NEW - weak area analysis)
  scoring.py        (MODIFIED - add IQ/EQ scoring)

data/
  cognitive/        (POPULATE - fill with questions)
  curriculum/       (EXISTING)
  emotional/        (NEW - EQ questions)
    eq_assessment.json
  licensure/        (NEW - licensure exam questions)
  lessons/          (NEW - lesson content)
  onboarding/       (NEW - pretest questions)
    pretest.json

results/            (CSV exports)
main.py             (MODIFIED - all new screens)
```

### Risks
- **Single-file monolith**: `main.py` will grow significantly. Consider refactoring into separate screen modules in a future iteration.
- **Question data quality**: Populating cognitive, EQ, and licensure question banks requires careful curation. Start with sample data and expand iteratively.
- **IQ scoring validity**: The IQ score will be an approximation, not a clinically validated test. Label it clearly as an "estimate".

# Testing

### Validation Approach
Verify each feature by running the Flet app and walking through the complete user flow.

### Key Scenarios
- **First launch**: App shows onboarding pretest → user completes it → sees score → creates account → lands on home.
- **Returning user**: App shows login → user logs in → lands on home with saved data.
- **Cognitive test**: User starts cognitive test → answers questions across domains → sees IQ score with domain breakdown.
- **EQ assessment**: User starts EQ test → answers scenario questions → sees EQ score.
- **Mock test**: User selects exam type and difficulty → takes timed test → sees results saved to database.
- **Learning mode**: User enters learning mode → sees personalized plan based on weak areas → reads lesson → completes practice quiz.
- **Statistics**: User views statistics → sees score history and trends from past tests.
- **Recommendations**: User views recommendations → sees suggestions based on performance.

### Edge Cases
- Empty question banks (no questions for a subject/exam).
- User cancels test mid-way (progress dialog works).
- User takes tests without creating an account (guest mode handles gracefully).
- Database doesn't exist on first run (auto-created).
- User has no test history (statistics shows empty state).

# Delivery Steps

### ✓ Step 1: Onboarding pretest and user account system
Add a pretest-on-first-launch screen and a user account system with local SQLite persistence.
- Create `core/database.py` with SQLite schema for users, test results, and progress tracking.
- Create `data/onboarding/pretest.json` with 10 general knowledge questions for the first-run experience.
- Add `show_onboarding()` and `show_signup()` screens in `main.py` — users take a short pretest, see their score, then optionally create an account.
- Update `show_home()` to check if a user is logged in; redirect to onboarding if not.
- Implement login/logout flow in the profile drawer.

### ✓ Step 2: Cognitive IQ and EQ assessment modules
Implement the full cognitive (IQ) test and EQ assessment modules with dedicated UI screens.
- Populate `data/cognitive/` JSON files (verbal, numerical, logical, spatial × beginner/intermediate/advanced) with questions.
- Create `data/emotional/eq_assessment.json` with scenario-based EQ questions.
- Add `calculate_iq_score()` and `calculate_eq_score()` functions in `core/scoring.py`.
- Implement `show_cognitive_test()` and `show_eq_assessment()` screens in `main.py` that use the existing quiz engine.
- Replace stub screens with working cognitive and EQ assessments.

### ✓ Step 3: Mock test and licensure exam mode
Add mock test mode where users can take timed practice exams for any subject or licensure exam.
- Create `data/licensure/` directory with exam category definitions (e.g., nursing, engineering, teaching) and sample question banks.
- Add `load_licensure_exam()` function in `core/loader.py`.
- Implement `show_mock_test_menu()` in `main.py` with difficulty selection and question count configuration.
- Add timer functionality to the quiz engine for timed mock tests.
- Save mock test results to the SQLite database for progress tracking.

### * Step 4: Learning mode with personalized lessons
Implement learning mode that generates personalized lessons based on user's weakest areas.
- Create `core/recommender.py` with logic to analyze test results and identify weak topics.
- Create `data/lessons/` directory with lesson content JSON files (explanations, key concepts, practice questions) organized by subject and topic.
- Add `show_learning_mode()` screen in `main.py` that shows a personalized study plan.
- Implement `show_lesson()` screen with lesson content and embedded practice quiz.
- Add homework/mini-quiz feature: short 5-question quizzes that users can complete daily.

### ✓ Step 5: Statistics, recommendations, and progress tracking
Make statistics meaningful and recommendations personalized, and wire up the complete navigation flow.
- Implement `show_statistics()` with charts showing score history, subject breakdowns, and trends (using Flet's built-in UI components).
- Implement `show_recommendations()` that uses `core/recommender.py` to suggest subjects, lessons, and practice tests based on performance.
- Update the profile drawer to show real user data from the database.
- Ensure all screens are connected: onboarding → home → features → results → recommendations → learning mode.
- Add CSV export for test results in the `results/` directory.

### ✓ Step 6: Data population and final integration
Add sample question data for all cognitive domains and EQ, polish UI, and ensure the app runs end-to-end.
- Populate remaining empty cognitive JSON files with at least 10 questions per tier.
- Add EQ assessment questions (20+ scenario-based questions).
- Add sample licensure exam questions (10 per category).
- Add lesson content for top 3 subjects (Math, Science, English).
- Polish UI: consistent colors, loading states, and error handling.
- Test the complete flow: first launch → pretest → account creation → mock test → results → learning mode → statistics.