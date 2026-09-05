# Nirnay Pay Dashboard

Build the complete frontend for a premium fintech SaaS product called “Nirnay Pay”.

IMPORTANT:

This is FRONTEND ONLY.

Do NOT build:

- Backend

- Database

- API server

- AI/LLM implementation

- Agents

- Payment processing

- Authentication backend

- Business-rule logic

The existing backend APIs already exist. Your job is only to build the frontend and connect it to those APIs.

Strictly follow this : Design direction: Refined Minimalist Enterprise SaaS

Principles: clarity, information density, restrained branding, consistent spacing, strong typography, minimal decoration, purposeful motion, accessible contrast, responsive layouts, and complete interaction states.

--------------------------------------------------

1. TECH STACK

--------------------------------------------------

Use:

- Next.js 15

- React

- TypeScript

- Tailwind CSS

- shadcn/ui

- Radix UI

- Lucide React icons

- TanStack Query

- Recharts

- Zod where validation is required

Use a clean component architecture.

Do NOT use Streamlit or Python.

--------------------------------------------------

2. DESIGN DIRECTION

--------------------------------------------------

The product is built for Razorpay-style merchants and must feel like a premium Indian fintech/B2B SaaS product.

Take inspiration from Razorpay's UX principles:

- Strong fintech visual hierarchy

- Professional typography

- Structured layouts

- Clear navigation

- Metric-first presentation

- Progressive disclosure

- Product-like UI instead of a generic dashboard template

- Strong trust/compliance presentation

- Consistent primary and secondary actions

- Clean cards and data visualization

- Subtle motion only where useful

DO NOT copy Razorpay's exact branding, logo, illustrations, colors, text, or website.

Create an original Nirnay Pay identity.

The UI must NOT look:

- AI-generated

- Futuristic for no reason

- Neon

- Over-animated

- Cyberpunk

- Generic SaaS template

- Excessively rounded

- Cluttered

It should feel like a serious production fintech product.

--------------------------------------------------

3. APPLICATION STRUCTURE

--------------------------------------------------

Create these main sections:

1. Overview

2. Recovery Cases

3. Analytics

4. Audit

Use a professional application shell:

- Left navigation/sidebar

- Top header

- Merchant context

- Main content area

- Consistent page header

- Breadcrumbs where useful

Keep navigation simple. Do not create a Razorpay-style marketing mega-menu because this is an authenticated product dashboard, not a marketing website.

--------------------------------------------------

4. OVERVIEW / DASHBOARD

--------------------------------------------------

Create a premium executive dashboard.

Top section:

Title:

“Revenue Recovery Overview”

Subtitle:

“Monitor revenue at risk and see how Nirnay Pay recovers it.”

Display KPI cards:

- Revenue At Risk

- Revenue Recovered

- Recovery Rate

- Active Recovery Cases

- Compliance Blocks

Use INR formatting.

Example:

₹25.0L

₹17.5L

70%

32

4

Below the KPIs, show:

### Recovery Performance

Chart comparing:

- Revenue At Risk

- Revenue Recovered

### Recovery Breakdown

Show the four supported recovery scenarios:

- Payment Failure

- Checkout Abandonment

- Subscription Failure

- Overdue Receivable

### Recent Recovery Cases

Show a professional data table with:

- Case ID

- Customer

- Scenario

- Amount At Risk

- Recovery Score

- Action

- Status

- Created At

Clicking a case opens its Case Detail page.

--------------------------------------------------

5. RECOVERY CASES

--------------------------------------------------

Create a dedicated Recovery Cases page.

Include filters:

- Scenario

- Status

- Customer segment

- Date

- Search

Only support these scenarios:

- Payment Failure

- Checkout Abandonment

- Subscription Failure

- Overdue Receivable

Case table columns:

- Case ID

- Customer

- Scenario

- Amount At Risk

- RecoveryScore

- Recommended Action

- Status

- Created At

Use pagination.

Do not invent additional case types.

--------------------------------------------------

6. CASE DETAIL — MOST IMPORTANT SCREEN

--------------------------------------------------

Create a highly polished case investigation page.

The page must clearly answer:

“What happened, why did Nirnay Pay choose this recovery action, and what happened afterward?”

Header:

- Case ID

- Customer

- Scenario

- Amount At Risk

- Current Status

--------------------------------------------------

7. DIAGNOSIS SECTION

--------------------------------------------------

Show:

- Root Cause

- Confidence

- Mode

- Rationale

Example:

Root Cause

Temporary Payment Failure

Confidence

91%

Mode

AI

Rationale

Customer recently replaced their card.

Make this visually clear but not overly decorative.

--------------------------------------------------

8. RECOVERY RIGHTS — BUSINESS DIFFERENTIATOR

--------------------------------------------------

Give this section strong visual importance.

Display:

Customer Segment

LOYAL

Recommended Treatment

GRACE PERIOD

Business Reason

Protect long-term customer value instead of aggressively pursuing a single failed payment.

Make it obvious that Recovery Rights is a business treatment decision.

Do NOT implement the Recovery Rights logic in the frontend.

Only display the backend result.

--------------------------------------------------

9. COMPLIANCE

--------------------------------------------------

Display:

- Compliance Status

- Allowed Actions

- Blocked Actions

- Blocking Reason

- Attempt information when available

States:

APPROVED

BLOCKED

For blocked cases, clearly communicate:

“No automatic recovery action executed.”

Do not calculate compliance on the frontend.

--------------------------------------------------

10. RECOVERYSCORE

--------------------------------------------------

Create a professional score visualization.

Display:

- RecoveryScore

- Expected Recovery Probability

- Amount At Risk

- Channel Cost

- Compliance Penalty

The RecoveryScore must come from the API.

NEVER calculate the authoritative score on the frontend.

--------------------------------------------------

11. DECISION

--------------------------------------------------

Show:

Selected Action

Decision Mode

Rationale

Confidence when available

Possible actions only:

- Retry

- Wait

- Reminder

- Escalate

- Human Review

- Stop

Clearly distinguish:

AI

RULE

FALLBACK

Do not implement decision logic in React.

--------------------------------------------------

12. RECOVERY TIMELINE

--------------------------------------------------

Create a professional chronological timeline:

Detected

↓

Diagnosed

↓

Compliance Checked

↓

Recovery Rights Applied

↓

Score Calculated

↓

Decision Made

↓

Action Executed

↓

Outcome

Each event should show:

- Event

- Actor

- Timestamp

- Short description

Use audit API data.

--------------------------------------------------

13. ACTION RESULT

--------------------------------------------------

Show:

- Action

- Status

- Recovered Amount

- Outcome Reason

Possible states:

SUCCESS

FAILED

BLOCKED

STOPPED

Never display money as recovered unless the backend reports successful recovery.

--------------------------------------------------

14. EXECUTE ACTION

--------------------------------------------------

If an action is executable according to the backend:

Show a clear primary action button.

Example:

“Execute Recovery”

Before execution, show a concise confirmation dialog.

After execution:

- Show loading state

- Call backend API

- Show success/failure result

- Refresh case data

- Refresh audit timeline

- Refresh dashboard metrics

Never execute business logic locally.

Never bypass backend validation.

--------------------------------------------------

15. ANALYTICS

--------------------------------------------------

Create an Analytics page specifically for the hackathon measurement requirement.

Show:

BASELINE vs NIRNAY PAY

Metrics:

- Recovery Rate

- Revenue Recovered

- Revenue At Risk

- Compliance Blocks

- Stopped Cases

- Total Cases

Use clean charts and comparison cards.

Clearly label:

“Synthetic / Simulated Data”

Do not invent real-world performance claims.

--------------------------------------------------

16. AUDIT

--------------------------------------------------

Create an Audit page.

Show:

- Case ID

- Event Type

- Actor

- Timestamp

- Event Details

Allow filtering by:

- Case

- Event

- Actor

Opening a case should show its complete audit timeline.

Audit data is read-only.

--------------------------------------------------

17. API INTEGRATION

--------------------------------------------------

Create a centralized API layer.

Use TanStack Query for server state.

Connect only to these existing APIs:

GET /health

GET /merchants/{merchant_id}

GET /recovery-cases

GET /recovery-cases/{case_id}

POST /detect

POST /recovery-cases/{case_id}/diagnose

POST /recovery-cases/{case_id}/compliance-check

POST /recovery-cases/{case_id}/recovery-rights

POST /recovery-cases/{case_id}/score

POST /recovery-cases/{case_id}/decide

POST /recovery-cases/{case_id}/execute

GET /recovery-cases/{case_id}/audit

GET /dashboard/summary

GET /dashboard/cases

POST /batch-runs

Do NOT invent new APIs.

Do NOT create mock business logic if the API already provides the data.

--------------------------------------------------

18. FRONTEND ARCHITECTURE

--------------------------------------------------

Use a clean structure similar to:

src/

  app/

  components/

  features/

    dashboard/

    recovery-cases/

    case-detail/

    analytics/

    audit/

  lib/

    api/

    utils/

  hooks/

  types/

Keep reusable UI components separate from feature-specific components.

--------------------------------------------------

19. UI STATES

--------------------------------------------------

Every API-backed screen must support:

- Loading

- Success

- Empty

- Error

- Retry

Buttons must support:

- Idle

- Loading

- Success

- Failed

- Disabled

Never show raw backend stack traces.

--------------------------------------------------

20. VISUAL SYSTEM

--------------------------------------------------

Create a consistent design system.

Use:

- Professional typography

- Strong spacing system

- Restrained border radius

- Subtle shadows

- Clean data tables

- Consistent iconography

- Clear status badges

- Professional charts

- Excellent whitespace

Use animation sparingly.

No unnecessary gradients.

No glowing effects.

No excessive glassmorphism.

No decorative AI imagery.

The interface should look like something a real fintech operations team could use daily.

--------------------------------------------------

21. RESPONSIVENESS

--------------------------------------------------

Support:

- Desktop

- Laptop

- Tablet

Desktop is the primary target because this is a merchant operations platform.

--------------------------------------------------

22. IMPORTANT BUSINESS BOUNDARY

--------------------------------------------------

The frontend must NEVER implement:

- Compliance rules

- Recovery Rights rules

- RecoveryScore calculation

- Decision-making logic

- AI reasoning

- Payment processing

- Recovery simulation

- Database operations

The backend is the source of truth.

The frontend only:

FETCHES → DISPLAYS → REQUESTS ACTION → REFRESHES

--------------------------------------------------

23. FINAL USER JOURNEY

--------------------------------------------------

The complete working journey must be:

Dashboard

→ Recovery Cases

→ Select Case

→ Case Detail

→ Diagnosis

→ Compliance

→ Recovery Rights

→ RecoveryScore

→ Decision

→ Execute Recovery

→ Outcome

→ Audit Timeline

→ Analytics

Every step must be implemented and connected to the API.

--------------------------------------------------

24. DEFINITION OF DONE

--------------------------------------------------

Do not consider the frontend complete until:

- All four recovery scenarios are represented.

- Dashboard is fully functional.

- Case listing works.

- Case filtering works.

- Case detail works.

- Diagnosis is displayed.

- Recovery Rights is displayed.

- Compliance is displayed.

- RecoveryScore is displayed.

- Decision is displayed.

- Recovery execution works through the API.

- Outcome is displayed.

- Audit timeline works.

- Analytics works.

- Baseline vs Nirnay Pay comparison works.

- Loading/error/empty states work.

- Responsive layout works.

- No placeholder screens remain.

- No fake buttons remain.

- No frontend business logic duplicates the backend.

- No extra features outside this specification are added.

Before finishing, test the entire frontend using the existing API and verify the complete user journey from Dashboard → Case → Decision → Execution → Audit → Analytics.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/04787b0e-436c-40fb-96c7-dae3ed47206f).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
