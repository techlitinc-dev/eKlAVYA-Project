# Implementation Plan

- [ ] 1. Create data models for study center features
  - Create Pydantic models in `models/study_center_models.py` for all request/response types
  - Define Topic, LearningMaterials, MindMap, TeachingContent, LearningSession, ProgressSummary, LearningJourney, and ParentInsights models
  - Add field validation and example schemas for API documentation
  - _Requirements: 1.1, 1.2, 2.1, 3.1, 4.1, 5.1_

- [ ] 2. Implement learning material service with AI generation
  - [ ] 2.1 Create `services/learning_material_service.py` with core generation methods
    - Implement `generate_notes()` method using Gemini AI with proper prompt engineering
    - Implement `generate_mind_map()` method to create structured mind maps in JSON format
    - Implement `generate_teaching_content()` method with introduction, concepts, examples, and summary
    - Add `parse_mind_map_response()` to convert Gemini response to structured MindMap object
    - Add `validate_material_quality()` to ensure generated content matches the topic
    - _Requirements: 1.4, 2.2, 2.3, 5.1, 5.2, 5.3, 6.1, 6.2_

  - [ ] 2.2 Create AI prompt templates for content generation
    - Create `utils/study_center_prompts.py` with prompt building functions
    - Implement `build_notes_prompt()` with exam-specific context and syllabus information
    - Implement `build_mindmap_prompt()` to generate structured JSON mind maps
    - Implement `build_teaching_prompt()` with difficulty adaptation
    - Include exam type (JEE/NEET) context in all prompts for accuracy
    - _Requirements: 5.3, 6.1, 6.3_

  - [ ] 2.3 Implement material caching in Firestore
    - Add methods to check `learning_materials` collection for cached content
    - Implement cache storage with 30-day expiration timestamp
    - Add cache retrieval with expiration checking
    - Track access count and last accessed timestamp for analytics
    - _Requirements: 1.2, 1.3, 7.1, 7.2, 7.3_

- [ ] 3. Implement progress tracking service
  - [ ] 3.1 Create `services/progress_tracker_service.py` with session management
    - Implement `start_learning_session()` to create new session in Firestore
    - Implement `end_learning_session()` to calculate and store duration
    - Implement `mark_topic_complete()` to update completion status to 100%
    - Add session timestamp tracking for streak calculations
    - _Requirements: 3.1, 3.2, 3.5_

  - [ ] 3.2 Implement progress calculation methods
    - Implement `get_topic_progress()` to retrieve completion percentage for a topic
    - Implement `get_all_progress()` to aggregate progress across all topics
    - Implement `calculate_study_streaks()` to count consecutive study days
    - Calculate total time spent per topic across all sessions
    - _Requirements: 3.3, 3.4, 4.2, 4.3_

  - [ ] 3.3 Implement parent insights generation
    - Implement `get_parent_insights()` to generate comprehensive progress report
    - Calculate daily and weekly study time averages
    - Identify top 3 most studied and least studied topics
    - Generate actionable recommendations for parents
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Create study center orchestration service
  - [ ] 4.1 Create `services/study_center_service.py` with topic management
    - Implement `get_topics_for_student()` to fetch syllabus topics based on exam type
    - Load topics from existing syllabus JSON files in `data/syllabus/` directory
    - Filter topics by subject if specified
    - Enrich topics with progress data from Firestore
    - _Requirements: 1.1, 8.1_

  - [ ] 4.2 Implement material orchestration methods
    - Implement `get_learning_materials()` to check cache first, then generate if needed
    - Implement `check_material_cache()` to query Firestore for existing materials
    - Coordinate between cache service and generation service
    - Handle cache expiration and regeneration logic
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 7.1, 7.2_

  - [ ] 4.3 Implement learning journey sequencing
    - Implement `get_learning_journey()` to create recommended topic sequence
    - Identify prerequisite topics that should be completed first
    - Highlight next recommended topic based on current progress
    - Generate motivational messages based on progress and streaks
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.5_

- [ ] 5. Create study center API router
  - [ ] 5.1 Create `routers/study_center_router.py` with topic endpoints
    - Implement `GET /api/study-center/topics` to list available topics
    - Implement `GET /api/study-center/topics/{topic_id}` for topic details
    - Add authentication middleware to verify student JWT token
    - Add query parameter support for subject filtering
    - _Requirements: 1.1, 10.1_

  - [ ] 5.2 Implement learning material endpoints
    - Implement `GET /api/study-center/materials/{topic_id}` to get all materials
    - Implement `POST /api/study-center/materials/generate` to force regeneration
    - Implement `GET /api/study-center/mindmap/{topic_id}` for mind map retrieval
    - Implement `GET /api/study-center/teach/{topic_id}` for teaching content
    - Add proper error handling with user-friendly messages
    - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 5.1, 10.2, 10.4_

  - [ ] 5.3 Implement progress tracking endpoints
    - Implement `GET /api/study-center/progress/{student_id}` for progress summary
    - Implement `POST /api/study-center/progress/start` to begin learning session
    - Implement `POST /api/study-center/progress/complete` to mark topic complete
    - Implement `GET /api/study-center/journey/{student_id}` for learning journey
    - Add request validation and error responses
    - _Requirements: 3.1, 3.2, 3.4, 8.1, 10.1_

  - [ ] 5.4 Implement parent dashboard endpoints
    - Implement `GET /api/study-center/parent-progress/{child_id}` for parent insights
    - Verify parent-child relationship before returning data
    - Add authorization checks to ensure parents can only view their own child's data
    - Return comprehensive insights with recommendations
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Implement achievement and motivation system
  - [ ] 6.1 Create achievement tracking in progress service
    - Add achievement badge logic for completing 5, 10, and all topics in a subject
    - Implement streak badge for 7 consecutive study days
    - Store achievements in `learning_progress` document
    - _Requirements: 9.2, 9.3_

  - [ ] 6.2 Implement motivational messaging
    - Add congratulatory messages when topics are completed
    - Generate encouraging messages for students returning after gaps
    - Calculate and display syllabus coverage percentage
    - Include progress statistics in completion messages
    - _Requirements: 9.1, 9.4, 9.5_

- [ ] 7. Add error handling and retry logic
  - [ ] 7.1 Implement Gemini API error handling
    - Add retry logic with exponential backoff (2s, 4s) for API failures
    - Implement 30-second timeout for content generation
    - Return user-friendly error messages on failure
    - Log all errors with full context for debugging
    - _Requirements: 10.3, 10.4, 10.5_

  - [ ] 7.2 Add rate limiting for AI generation
    - Implement rate limiter: 10 AI generation requests per student per hour
    - Return 429 status with retry-after header when limit exceeded
    - Log all AI generation requests with token counts
    - _Requirements: 7.5_

- [ ] 8. Integrate router with main application
  - Register study center router in `main.py` with `/api/study-center` prefix
  - Add router to API documentation with proper tags
  - Verify all endpoints are accessible and documented
  - _Requirements: 10.1_

- [ ] 9. Create database indexes for performance
  - Create Firestore composite index on `topic_id` + `exam_type` for material lookups
  - Create index on `student_id` for progress queries
  - Create composite index on `student_id` + `session_date` for session queries
  - Document index requirements in deployment guide
  - _Requirements: 10.1, 10.2_

- [ ] 10. Test API endpoints with real data
  - [ ] 10.1 Test topic retrieval endpoints
    - Test getting topics for JEE Main student
    - Test getting topics for NEET student
    - Test subject filtering
    - Verify topics match syllabus JSON files
    - _Requirements: 1.1_

  - [ ] 10.2 Test material generation and caching
    - Test notes generation for a Physics topic
    - Test mind map generation for a Chemistry topic
    - Test teaching content generation for a Mathematics topic
    - Verify cache hit on second request for same topic
    - Verify materials are stored in Firestore with correct structure
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 5.1, 7.1, 7.2_

  - [ ] 10.3 Test progress tracking flow
    - Test starting a learning session
    - Test completing a topic
    - Test progress calculation across multiple topics
    - Test streak calculation with multiple sessions
    - Verify session data is stored correctly in Firestore
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 10.4 Test parent insights endpoint
    - Test parent viewing child's progress
    - Verify daily and weekly averages are calculated correctly
    - Verify most/least studied topics are identified correctly
    - Test authorization (parent can only view their own child)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 10.5 Test learning journey sequencing
    - Test recommended sequence generation
    - Test prerequisite identification
    - Test next topic recommendation
    - Verify motivational messages are generated
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.5_

  - [ ] 10.6 Test error handling and edge cases
    - Test invalid topic ID returns 404
    - Test Gemini API failure triggers retry logic
    - Test rate limiting returns 429 after 10 requests
    - Test unauthorized access returns 401
    - Test cache expiration and regeneration
    - _Requirements: 10.3, 10.4, 10.5, 7.5_

- [ ] 11. Performance testing and optimization
  - [ ] 11.1 Test response times
    - Verify cached material responses are under 500ms
    - Verify new generation completes within 30 seconds
    - Test with 50 concurrent requests
    - Identify and optimize slow queries
    - _Requirements: 10.1, 10.2_

  - [ ] 11.2 Monitor token usage
    - Log token consumption for each generation type
    - Calculate cost per topic
    - Verify cache hit rate is above 70%
    - Optimize prompts if token usage is too high
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 12. Documentation and deployment preparation
  - [ ] 12.1 Create API documentation
    - Document all endpoints with request/response examples
    - Add authentication requirements to docs
    - Document rate limits and error codes
    - Create Postman collection for testing
    - _Requirements: 10.1_

  - [ ] 12.2 Create deployment guide
    - Document required Firestore indexes
    - Document environment variables needed
    - Create database initialization script
    - Document monitoring and alerting setup
    - _Requirements: 10.1_
