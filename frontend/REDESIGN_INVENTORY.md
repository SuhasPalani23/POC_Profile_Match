# Founding Mindset Portal – Frontend Phase 0 Inventory

This document acts as a strict contract for the visual redesign of the application. It lists every existing component, route, state, and data field that **must be retained** in the new cinematic aesthetic. Modifying backend structure or removing fields is strictly prohibited.

## 1. Authentication (`/src/components/Auth`)
### `Login.jsx`
- **Fields**: Email, Password.
- **Actions**: "Sign In" button, "Don't have an account? Sign Up" link.
- **States**: Error banners, Loading state (submitting).

### `Signup.jsx`
- **Fields**: 
  - Role selection (Founder, Candidate)
  - Full Name, Email, Password, Confirm Password
  - Contextual step fields: Idea Description (Founder), Top Skills (Candidate, comma-separated)
- **Actions**: "Create Account" button, "Already have an account? Log In" link.
- **States**: Field errors, General errors, Loading state.

## 2. Dashboard (`/src/components/Dashboard`)
### `FounderDashboard.jsx`
- **Metrics**: Projects count, Matches count, Requests count (Pending invites).
- **Actions**: "New Project" (Submit Idea), "Show less / Read more" (Description toggler).
- **Project List**: 
  - Status badge (LIVE or PENDING REVIEW)
  - Title, Description snippet
  - Actions: "View Matches", "View Team", "Team Chat".
- **States**: Loading loader.

### `UserDashboard.jsx` (Candidate Workspace)
- **Sections**: 
  - Welcome Banner (with user name)
  - "My Teams" (Active Memberships): Project title, Founder name, Joined date, Description preview.
    - Actions: "Team Chat", "View Team", "Leave"
  - "Founder mode" CTA: "Ready to launch your own startup brief?" -> "Submit Your Idea"
  - Platform capabilities cards
  - Profile Snapshot: Email, Title, Location, Experience (years), Bio, Skills (tags), LinkedIn link.
- **States**: Loading states, Empty states (No projects joined), Toast notifications.

## 3. Project (`/src/components/Project`)
### `IdeaSubmission.jsx`
- **Fields**: Project Title, Project Description (min 500 chars), Required Skills (comma-separated).
- **Toolbar/AI**: 
  - Voice recording ("Voice" -> "Stop")
  - Listen (TTS)
  - AI Rewrite with styles: Professional, Shorten, Elevator Pitch, Formal, Casual, Expand, Story, Technical.
- **Actions**: "Cancel", "Submit for Review".
- **States**: Voice recording states, Rewriting loading state, Submitting animation (10sec calibration).

## 4. Matching (`/src/components/Matching`)
### `MatchList.jsx`
- **Route Options**: Project brief header, Navigation to Dashboard.
- **Match Item/Card**:
  - Score (% with "match" rank label)
  - Name, Title/Role, Experience Years
  - Skills Tags (filtered by priority/noisy sets)
  - Match Reasoning (text explanation)
  - Subscores (radar/stats)
  - Expanded Details: Bio, Strengths, Considerations (Concerns), LinkedIn link, Resume link (API endpoint).
  - Actions: "View/Hide Details", Feedback ("Helpful", "Not Helpful"), "Send Request".
- **States**: Progress counter for search, Loading scanner animation, Expanded/Collapsed cards.

## 5. Profile (`/src/components/Profile`)
### `ProfileEdit.jsx`
- **Sections/Tools**:
  - LinkedIn Scrape: URL Input, "Scrape & Auto-fill" button, "Clear URL".
  - Basic Info: First Name, Last Name, Professional Headline, About Me, Email, LinkedIn URL.
  - Resume Management: Upload (PDF/DOCX), Download, Delete, extracted skills hint.
  - Auto-Filled / Scraped Panel: About, Current Role, Company, Skills, Tools, Core Domains, Interests, Years of Experience, Work Style.
  - Discovered Insights: Dynamic extra fields from advanced scraping.
- **Chatbot (Typeform-style Overlay)**: 
  - Q&A floating dialogue.
  - Input field for answering.
  - Minimize / Close actions.
- **Actions**: "Save Profile".
- **States**: Unsaved changes warning, Scraping cooldown, Loading, Uploading, Error banners.

## 6. Collaboration & Chat (`/src/components/Collaboration`, `/src/components/Chat`)
### `CollaborationRequests.jsx`
- **List Items**: 
  - Project Title & Full Description.
  - Founder Info: Name, Title, Bio.
  - Custom Message text.
- **Actions**: "Accept & Join Team", "Decline".

### `TeamPage.jsx`
- **Information**: Project Title, Member count string.
- **Cards**:
  - Member details: Name, Role tags ("FOUNDER", "YOU"), Professional Title, Bio, Skills (tags), Email.
- **Actions**: "Back to Dashboard", "Open Team Chat".

### `LiveChat.jsx`
- **Views**: 
  - Sidebar: Channel list ("# Group Chat"), Direct Messages list (per member).
  - Team Members list: Removal action (if founder).
  - Main Panel: Messages stream.
- **Message Item**: Sender name, Text, Timestamp.
- **Actions**: 
  - DM channel selecting.
  - Message Text Input, "Send" button.
  - "Load older messages".
  - "Leave Project" (with confirm).
  - "Remove" member (with confirm mask).
- **States**: WebSocket optimistic updates, Unread counts per thread, Loading, Confirm dialogs.

## UI Components & Primitives
- **Button.jsx**: Primary, Secondary, Outline variants; loading state; fullWidth.
- **FormField.jsx / input styles**: Consistent bordering, focus rings, hints.
- **Loaders**: `LoadingAnimation.jsx`, Cinematic CSS loaders (`pulse-ring`, `cinematic-loader`).
- **Typography/Layout**: `MetricTile.jsx`, Hero text components (`word-rise`, `gradient-text`).
- **Toast Events**: `window.dispatchEvent(new CustomEvent('app-toast'))`.

## Non-Negotiable Contract
1. Every input, button, and state presented above must visually exist and be interactively reachable in the redesign.
2. The exact prop structures flowing into these components from context or the API are untouched.
3. No forms or processes can be "simplified" if it risks dropping any currently collected field (e.g., keeping specific AI rewriting toolbars).
