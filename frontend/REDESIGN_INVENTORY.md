# Frontend Redesign Inventory

This document serves as the discovery and inventory of all existing frontend routes, pages, sections, form fields, and states for the "Founding Mindset Portal". Per the redesign requirements, every item listed here must be preserved exactly in functionality and presence.

## 1. Login (`/login`)
- **Route Path:** `/login`
- **Page Title / Heading:** Founder Employee Matching Platform / Find Exceptional Talent / Secure Access / Sign In
- **Sections:**
  - Hero / Marketing section (left split)
  - Authentication Form (right split)
- **Form Fields:**
  - Email (`email`, email, required)
  - Password (`password`, password, required)
- **Buttons / Actions:**
  - Sign In (submit button)
  - Show/Hide Password toggle icon
  - "Create one" link (to `/signup`)
- **Data Rendered:** None (input only).
- **State Variants:** Loading ('Signing in...'), Error (error banner with message), Caps Lock On warning.
- **Navigation:** To `/dashboard` on success, to `/signup`.

## 2. Signup (`/signup`)
- **Route Path:** `/signup`
- **Page Title / Heading:** Onboarding / Join the Founder Network
- **Sections:** Form container layout.
- **Form Fields:**
  - Full Name (`name`, text, required)
  - Email (`email`, email, required)
  - Password (`password`, password, required, min 6 chars)
  - Confirm Password (`confirmPassword`, password, required, min 6 chars)
- **Buttons / Actions:**
  - Create Account (submit button)
  - Show/Hide Password toggle icon
  - Show/Hide Confirm Password toggle icon
  - "Sign in" link (to `/login`)
- **Data Rendered:** None.
- **State Variants:** Loading ('Creating Account...'), Error (banner), Password Mismatch, Caps Lock On warnings.
- **Navigation:** To `/dashboard` on success, to `/login`.

## 3. Founder Dashboard (`/dashboard` for Founders)
- **Route Path:** `/dashboard` (role='founder')
- **Page Title / Heading:** Founder command center / Founder Dashboard
- **Sections:**
  - Header / Hero row
  - Metrics Grid
  - Projects List
  - Team View (Sub-component rendered when switching view state)
- **Form Fields:** None.
- **Buttons / Actions:**
  - New Project CTA (navigates to `/submit-idea`)
  - View Matches (per live project)
  - View Team (per live project)
  - Team Chat (per live project)
  - Read more / Show less toggle (for long descriptions)
- **Data Rendered:**
  - Projects Metric Tile
  - Matches Metric Tile
  - Requests Metric Tile
  - Project entries (Title, LIVE / PENDING badge, Description)
- **State Variants:** Loading ('Calibrating...'), Empty Projects ('No Projects Yet', 'Submit First Project'), Under Review (disabled state).
- **Navigation:** Mentions standard Navbar (`/requests`, `/profile/edit`, etc.).

## 4. User Dashboard (`/dashboard` for Candidates)
- **Route Path:** `/dashboard` (role!='founder')
- **Page Title / Heading:** Candidate workspace / Welcome {name}
- **Sections:**
  - Hero (Welcome message)
  - My Teams (Active memberships)
  - Founder Mode CTA
  - Platform capabilities
  - Profile Snapshot
- **Form Fields:** None.
- **Buttons / Actions:**
  - Team Chat (per project)
  - View Team (per project)
  - Leave (per project, triggers confirm)
  - Submit Your Idea (CTA)
  - View Collaboration Requests (if empty teams)
- **Data Rendered:**
  - My Teams entries: Project title, founder name, join date, description preview
  - Platform capabilities list (AI-Powered Matching, Instant Results, Team Formation)
  - Profile Snapshot elements: Email, Title, Location, Experience, Bio, Skills tags, LinkedIn link
- **State Variants:** Loading Projects, Empty Teams, Confirm leave popup.
- **Navigation:** Integrates with Navbar.

## 5. Idea Submission (`/submit-idea`)
- **Route Path:** `/submit-idea`
- **Page Title / Heading:** Founder Submission / Submit Your Startup Vision
- **Sections:**
  - Title/Intro
  - Form
- **Form Fields:**
  - Project Title (`title`, text, required)
  - Project Description (`description`, textarea, min 500 chars)
  - Required Skills (`required_skills`, text)
- **Buttons / Actions:**
  - Voice recording toggle (Stop / Voice)
  - TTS Listen button (Play / Listen)
  - AI Rewrite toggle + Style option chips (Professional, Shorten, Formal, Casual, Expand, Story, Technical)
  - Cancel
  - Submit for Review
- **Data Rendered:** Character count hint.
- **State Variants:** Recording active, Playing Audio active, Rewriting (loading anim), Submitting ('Reviewing your vision...'), Error banner.
- **Navigation:** Returns to `/dashboard` on cancel, forwards to `/matches/:projectId` on success.

## 6. MatchList (`/matches/:projectId`)
- **Route Path:** `/matches/:projectId`
- **Page Title / Heading:** Match Intelligence  
- **Sections:**
  - Header / Project Brief
  - Match Cards List
- **Form Fields:** None.
- **Buttons / Actions:**
  - Back to Dashboard
  - Send Request
  - View Details / Hide Details toggle
  - Helpful (submit feedback)
  - Not Helpful (submit feedback)
- **Data Rendered:**
  - Match count (`{count} / {total} matches found`)
  - Project Brief: Title, Description
  - Card Metrics: Match Percentage, Match Rank (#1 match, etc.)
  - Card Profile: Name, Professional Title, Experience Years, Skills tags, Reasoning block, Subscores grid (hard skills, domain, etc.).
  - Expanded Details: Bio, Strengths list, Considerations list, LinkedIn link, Resume link, 'Founder - not available' label, 'Request Sent' label.
- **State Variants:** Loading ('Scanning the talent pool...'), Error ('System Alert'), Empty ('No Matches Found'), Expansion visibility states.
- **Navigation:** Back to Dashboard.

## 7. Profile Edit (`/profile/edit`)
- **Route Path:** `/profile/edit`
- **Page Title / Heading:** Edit Profile
- **Sections:**
  - LinkedIn Scrape (Import)
  - Basic Info
  - Auto-Filled from LinkedIn & AI
  - Discovered from LinkedIn
  - Typeform Chatbot Overlay (Floating component)
- **Form Fields:**
  - LinkedIn URL Input (`linkedinUrlInput`, text)
  - Basic Info: First Name, Last Name, Professional Headline, About Me (textarea + AI rewrite), Email, LinkedIn URL
  - Auto-Filled: About (textarea), Current Role, Company, Skills (textarea), Tools, Core Domains, Interests, Years of Experience, Work Style
  - Discovered Fields (Dynamic Field Cards via AI analysis)
  - File Upload for Resume (.pdf, .docx)
  - Chat input inside Typeform chatbot
- **Buttons / Actions:**
  - Scrape & Auto-fill
  - Clear URL
  - Upload Resume, Download Resume, Delete Resume
  - Wait/Listen/AI enhancements
  - Save Profile
  - Open Chatbot (FAB trigger)
  - Chat Send
- **Data Rendered:** Scrape stats, profile validation state (X missing), extracted skills from resume.
- **State Variants:** Unsaved changes banner, Indexing Vector DB states, Success banner, Error banners, Chatbot Loading / Minimised, Scrape Rate Limit cooldown.

## 8. Collaboration Requests (`/requests`)
- **Route Path:** `/requests`
- **Page Title / Heading:** Collaboration Requests (implied)
- **Sections:**
  - Request list
- **Form Fields:** None.
- **Buttons / Actions:**
  - Accept & Join Team
  - Decline
- **Data Rendered:**
  - Project Title and Full Description
  - Founder Name, Title, and Full Bio
  - Personal Message block
- **State Variants:** Loading spinner, Empty state ('No pending collaboration requests').
- **Navigation:** Implicitly via Navbar.

## 9. Team Page (`/team/:projectId`)
- **Route Path:** `/team/:projectId`
- **Page Title / Heading:** Team / {Project Title}
- **Sections:**
  - Header with Member Count
  - Cards for Founder & Members
- **Form Fields:** None.
- **Buttons / Actions:**
  - Back to Dashboard
  - Open Team Chat
- **Data Rendered:** 
  - Project Title, total members
  - Founder Card (FOUNDER badge, name, title, bio, skills, email)
  - Member Cards (name, YOU badge if applicable, title, bio, skills, email)
- **State Variants:** Loading ('Loading team...'), Error, Empty state ('No other team members yet').

## 10. Live Chat (`/chat/:projectId`)
- **Route Path:** `/chat/:projectId`
- **Page Title / Heading:** #{Project Title} / DM
- **Sections:**
  - Left Sidebar / Nav (Channels, Direct Messages, Team Members, Actions)
  - Main Chat View
  - Input Area
- **Form Fields:**
  - New Message string input
- **Buttons / Actions:**
  - Group Chat toggle
  - DM channel toggle (per member)
  - Remove member (X icon - founders only, triggers confirm)
  - Leave Project (triggers confirm)
  - Back to Dashboard
  - Load older messages
  - Send message
- **Data Rendered:**
  - Project info, Member counts, Unread badges.
  - Chat Message items: Sender Name, Time, Text bubble.
  - Optimistic indicator.
- **State Variants:** Loading ('Loading chat...'), Confirm Leave Modal, Confirm Remove Modal, Empty Chat log, Sending.

*(End of Inventory)*
