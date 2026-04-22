# POC Flow Documentation

This document explains the full flow of the POC in a detailed but simple way.
It follows the real sequence of the application:

1. User authentication
2. LinkedIn scraping and profile building
3. Resume upload and resume analysis
4. Chatbot interview and data extraction
5. About Me generation and profile enrichment
6. Profile normalization and Pinecone reindexing
7. Founder project creation and candidate matching

The goal of the system is to build a richer user profile from multiple sources,
then use that profile to find good startup co-founder matches.

---

## 1. High-Level Architecture

The POC has two main layers:

- **Frontend**: React UI
- **Backend**: Flask API

The frontend is responsible for:

- showing forms and pages
- collecting user input
- sending requests to the backend
- showing returned data to the user

The backend is responsible for:

- authentication
- scraping LinkedIn through Apify
- parsing resumes
- running chatbot interviews
- extracting structured fields with AI
- generating About Me and summary fields
- saving all state in MongoDB
- building normalized profiles
- creating embeddings for Pinecone
- running matching logic for founders

The important design pattern is:

- the frontend does not decide the business logic
- the backend does the real work
- the backend saves state after every meaningful step
- the frontend refreshes from saved state

This is why the app can survive reloads, continue interviews later, and reuse the same profile data for matching.

---

## 2. User Authentication Flow

The flow starts with signup or login.

### Signup

When a user signs up:

- the app stores the user in MongoDB
- the password is hashed
- the name is split into `firstName` and `lastName`
- basic fields are initialized

This is useful because the chatbot and profile builder already have some identity data from the start.

### Login

When the user logs in:

- the backend verifies the credentials
- the user receives an auth token
- the token is used for all future protected requests

After login, the user can access:

- profile editing
- resume upload
- chatbot interview
- project creation
- matching pages

---

## 3. LinkedIn Profile Building Flow

This is the first major enrichment step.

The user pastes a LinkedIn profile URL into the profile page.

### Step 1: Validate the URL

The backend checks that a LinkedIn URL exists and that Apify is configured.
If the URL or Apify token is missing, the request fails early.

### Step 2: Run Apify scraping

The backend runs two scraping jobs:

- a **profile scraper** to fetch the main LinkedIn profile data
- a **posts scraper** to fetch recent post content

The profile scraper is the required one.
The posts scraper is best-effort.

If the posts scraper fails:

- the profile scrape still continues
- the main flow still works

### Step 3: Parse raw profile data directly

The backend first tries to parse the raw Apify response without relying on AI.

It extracts structured fields such as:

- `firstName`
- `lastName`
- `headline`
- `currentPosition`
- `currentCompany`
- `location`
- `city`
- `state`
- `country`
- `skills`
- `tools`
- `experience`
- `education`
- `certifications`
- `languages`
- `followers`
- `connections`
- `totalYearsExperience`

This direct parsing matters because it gives the system a deterministic baseline.

### Step 4: Analyze posts

The posts are processed separately.

The backend looks for:

- hashtags
- repeated themes
- technical topics
- product or startup interests
- community involvement
- project mentions
- achievement signals

From this, the system builds extra signals like:

- `interests`
- `coreDomains`
- `thoughtLeadershipTopics`
- `communityInvolvement`
- `projectsMentioned`
- `achievementSignals`
- `content_style`
- `expertise_level`

This makes the profile richer than just the visible LinkedIn fields.

### Step 5: Send the profile to the LLM

Once raw parsing is done, the backend sends the data to the LLM.

The LLM is asked to:

- clean the profile
- normalize field names
- infer reasonable values from evidence
- merge profile and post signals
- return a structured JSON profile

The LLM is not allowed to invent arbitrary facts.
It should only work from evidence in the scraped content.

### Step 6: Keep LinkedIn about text separate

The system intentionally does **not** copy the LinkedIn summary into the final About Me field.

Instead:

- the raw LinkedIn about text is stored separately
- the final `About Me` is saved later by the chatbot enrichment step

This is important because the final About Me is supposed to combine:

- LinkedIn
- resume
- chatbot answers
- post signals

### Step 7: Save the result

The cleaned profile is saved to MongoDB immediately.

The save includes:

- ordinary profile fields
- `extraFields`
- `dynamicFieldLabels`
- `linkedinFieldKeys`
- `postInsights`
- `linkedin_about_raw`
- `normalized_profile`

### Step 8: Refresh the UI

The frontend reloads the saved data and uses it to auto-fill the profile page.

So the LinkedIn scrape is not just data collection.
It is the first stage of profile construction.

---

## 4. Resume Upload Flow

The user can upload a resume after the profile is created.

### Supported file types

The system supports:

- PDF
- DOCX
- DOC

### Step 1: Read the file

The backend reads the uploaded file.

Depending on file type, it uses:

- PDF parsing
- DOCX parsing

### Step 2: Extract raw text

The parser converts the file into plain text.

This extracted text is stored and used later for:

- AI analysis
- matching
- profile enrichment

### Step 3: Extract contact info

The backend also uses regex to detect:

- email addresses
- phone numbers

### Step 4: Run resume AI analysis

The resume text is sent to an AI analysis step.

This analysis tries to extract:

- skills
- experience level
- strengths
- roles
- certifications
- education
- achievements
- recommended roles
- professional summary

### Step 5: Save resume data

The backend stores:

- the uploaded file reference
- the parsed resume text
- the extracted analysis

### Step 6: Reuse resume later

The resume text is not only for the upload screen.

It is reused later when:

- generating About Me
- building normalized profile data
- creating embeddings for Pinecone
- scoring candidates during matching

So the resume becomes a permanent part of the profile intelligence.

---

## 5. Chatbot Interview Flow

This is the core interview system.

It is a guided profiling chatbot.
It does not behave like a general chat assistant.

It has one job:

- ask the right missing question
- capture the answer
- save structured profile data
- move to the next missing field

### The 5 interview buckets

The chatbot covers these five areas:

1. Identity
2. Professional background
3. Topic depth
4. Market fit
5. Founder fit

Each bucket contains a list of fields that matter for that category.

### Identity bucket

This bucket collects basic identity:

- first name
- last name
- headline
- location

### Professional background bucket

This bucket collects work history:

- current position
- current company
- skills
- tools
- total years of experience
- core domains

### Topic depth bucket

This bucket tries to understand how deeply the person actually works:

- project highlights
- domain depth
- learning goals
- strengths
- collaboration style
- work style

### Market fit bucket

This bucket asks what kind of startup direction the person wants:

- preferred industry
- preferred role
- industry inclination
- interests
- career goals

### Founder fit bucket

This bucket asks the startup reality questions:

- hours per week
- equity expectations
- compensation expectations
- risk tolerance
- financial runway
- urgency to start
- previous startup experience
- cofounder role needed
- ideal cofounder
- deal breakers

---

## 6. How the Chatbot Chooses the Next Question

The chatbot is driven by the backend, not the UI.

Before each reply, the backend looks at:

- the current user profile
- `extraFields`
- `postInsights`
- `chatHistory`
- `askedFields`
- `lastAskedField`
- `emptyExtractionStreak`

The backend then decides:

- what is already known
- what has already been asked
- what is still missing
- what should be asked next

The main design principle is:

- one question per field
- no pointless repetition
- no drifting to unrelated topics
- no asking the same bucket forever

The router is responsible for keeping the interview moving in a structured way.

---

## 7. What Happens in One Chat Turn

Each turn has two major AI steps and one persistence step.

### Step 1: Generate the assistant message

The backend asks the LLM to write a short conversational response.

The assistant should:

- acknowledge the user briefly
- ask one question
- stay within the current bucket
- avoid repeating earlier questions
- not invent facts

### Step 2: Extract structured fields from the user reply

The backend then separately asks the LLM to extract data from the latest user answer.

This extraction is conservative:

- it should only save real user-provided information
- it should not guess
- it should not hallucinate

It can extract both normal fields and custom founder-fit fields.

### Step 3: Save the result

After extraction, the backend stores:

- the new chat messages
- any newly discovered fields
- updated labels
- the asked field tracker
- the confidence score
- the bucket score snapshot

So every turn becomes part of the permanent profile record.

---

## 8. How the Chatbot Handles Weak or Plain Answers

This is one of the most important behavior rules.

Users often answer in short or vague ways.

For example:

- “no”
- “not sure”
- “somewhere around 20 hours”
- “I work in fintech”
- “I don’t have startup experience”

The system is designed to still treat these as useful answers.

If extraction cannot cleanly parse a value:

- the backend may still save the raw answer under the field that was asked
- this prevents the bot from re-asking the same thing again
- the interview keeps moving forward

This is what makes the chatbot practical for real users.

It does not demand perfect responses.

---

## 9. Chatbot Stop Logic

The interview does not stop just because the score is high.

The current logic is driven mainly by:

- whether every required field has been asked once
- whether the hard turn cap has been reached
- whether the user manually finishes the interview

The key values in the engine are:

- `MIN_TURNS = 6`
- `HARD_MAX_TURNS = 35`
- `STOP_THRESHOLD = 0.80`
- `STUCK_EMPTY_TURNS = 3`
- `BUCKET_ROTATE_EMPTY_TURNS = 4`

### What these mean

- `MIN_TURNS` is a minimum conversational size reference
- `HARD_MAX_TURNS` is the absolute safety cap
- `STOP_THRESHOLD` is a target confidence level
- `STUCK_EMPTY_TURNS` helps identify dead loops
- `BUCKET_ROTATE_EMPTY_TURNS` helps force movement if extraction keeps failing

The actual practical rule is:

- once the bot has asked everything it needs, it wraps up
- if the hard cap is reached, it also wraps up

So the interview is designed to complete by coverage, not by score alone.

---

## 10. What Gets Saved During Chat

The chatbot writes a lot of state into MongoDB.

This includes:

- `chatHistory`
- `extraFields`
- `dynamicFieldLabels`
- `chatbotFieldKeys`
- `askedFields`
- `lastAskedField`
- `emptyExtractionStreak`
- `profileConfidenceScore`
- `dimensionScores`
- `interviewComplete`
- `interviewCompletedAt`

This persistence is what makes the interview durable.

If the user refreshes the page:

- the transcript comes back
- the current state comes back
- the chat can be reopened
- the interview can continue from the saved state

---

## 11. About Me Generation

When the chatbot interview ends, the backend runs the enrichment step.

This step combines:

- LinkedIn profile data
- chatbot answers
- raw chatbot transcript
- post signals
- resume text

Then it produces:

- `aboutMe`
- `about`
- `headline`
- `strengths`
- `workStyle`
- `careerGoals`
- `preferredRole`
- `preferredIndustry`

### What About Me is supposed to be

It is a short first-person summary that reads like a real profile narrative.

It should describe:

- who the person is
- what they do now
- what they want next
- how they like to work
- what founder-fit signals they gave

This is not a static template.
It is a synthesized AI summary from all the collected evidence.

---

## 12. Manual Profile Editing

The user can still edit fields manually in the UI.

This is separate from chatbot saving.

The manual Save Profile button is for:

- correcting form fields
- editing About Me
- adjusting headline
- changing skills or tools
- fixing any manually edited profile values

The chatbot already auto-saves its own answers, so manual save is mostly for the visible profile form.

---

## 13. Normalized Profile Flow

After profile data changes, the app builds a normalized profile.

This is the profile used for cleaner matching.

### What normalization does

Normalization merges data from:

- LinkedIn
- resume
- questionnaire
- chatbot fields

It produces a canonical profile object.

### Important normalized fields

- `canonical_skills`
- `core_domains`
- `primary_role`
- `unified_profile_summary`
- `total_experience_years`
- `startup_compatibility_flags`

### Why this exists

The raw profile can be noisy.
Normalization gives the matching engine a clean common format.

### Where it is stored

The normalized result is stored in MongoDB under `normalized_profile`.

---

## 14. Pinecone Reindexing Flow

After the profile changes, the backend reindexes the user in Pinecone.

This happens because the matching system depends on embeddings.

### The text used for embedding can include:

- identity fields
- headline
- job title
- company
- about text
- skills
- tools
- domains
- interests
- experience
- education
- resume text
- chatbot extra fields
- normalized profile data

### Why reindexing matters

Without reindexing, the profile used for matching would be stale.

With reindexing, the latest profile state is always reflected in search results.

---

## 15. Founder Project Flow

The founder side starts when a user creates a project.

### Step 1: Project submission

The founder submits:

- title
- description
- required skills

The description must be long enough, because the matching logic needs enough context.

### Step 2: Background review

After submission, a background task runs.

This task marks the project live after the review delay.

### Step 3: Founder role update

Once the project goes live:

- the user role is updated to `founder`

So the role change is tied to the project flow, not just the initial form submission.

---

## 16. Candidate Matching Flow

Once there is a live founder project, the matching flow starts.

### Step 1: Build project requirements

The backend reads the project title and description.
It converts them into a requirements object.

### Step 2: Search Pinecone

The backend creates a text query from the project requirements.
Then it searches the vector index for similar candidate profiles.

### Step 3: Load candidate user documents

The matching service fetches full user records from MongoDB for the returned vectors.

### Step 4: Score each candidate

The service applies a deterministic scoring model using factors like:

- exact skill overlap
- rare keyword overlap
- critical term overlap
- domain match
- role match
- experience match
- founder fit
- confidence
- AI depth signals
- retrieval similarity

### Step 5: Rank results

The candidates are sorted by score.

The best candidates rise to the top.

### Step 6: Return results to the UI

The frontend displays the ranked candidates as match cards.

The UI also lets the founder send collaboration requests.

---

## 17. Matching Is Hybrid, Not Single-Source

The matching system is not only vector similarity.
It is not only LLM output either.

It is a hybrid system:

- the LLM helps normalize and enrich profiles
- Pinecone retrieves semantically similar profiles
- deterministic scoring ranks the final result

This makes the matching more stable and more explainable.

---

## 18. Data Stored in MongoDB

MongoDB is the main persistence layer.

The user document can contain:

- identity fields
- profile fields
- LinkedIn scrape data
- resume data
- chatbot transcript
- chatbot answers
- dynamic labels
- extra insights
- normalized profile
- interview completion state
- profile confidence state

This means the database is not just storing one snapshot.
It is storing the history and the current enriched profile together.

---

## 19. What Triggers Reindexing

The user vector is reindexed after major changes such as:

- LinkedIn scrape save
- resume upload
- chatbot answer save
- profile update save
- interview completion
- manual finish-interview action

The reason is simple:

- the matching engine should always work with the most recent data

So reindexing is part of keeping the platform accurate.

---

## 20. Final End-to-End Flow

Here is the full POC in one clean sequence:

1. User signs up or logs in.
2. User opens the profile page.
3. User pastes a LinkedIn URL.
4. Backend scrapes LinkedIn profile and posts.
5. Backend parses and normalizes the scraped data.
6. Backend saves the profile to MongoDB.
7. User uploads a resume.
8. Backend parses and analyzes the resume.
9. Resume data is saved to MongoDB.
10. Chatbot starts the founder profiling interview.
11. Chatbot asks missing questions bucket by bucket.
12. Each answer is extracted and saved.
13. The chatbot avoids repeating itself.
14. The transcript and extracted fields are persisted.
15. When the interview ends, About Me is generated.
16. The full profile is normalized again.
17. The vector is reindexed in Pinecone.
18. Founder submits a startup project.
19. The project becomes live after review.
20. The user role becomes founder.
21. Matching runs.
22. Ranked candidate profiles are shown to the founder.

That is the whole POC in real flow order.

