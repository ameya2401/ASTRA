# AI Flow — Full-Stack App Development Playbook

> A sequential, step-by-step workflow for building, securing, and shipping an app with AI coding tools. Follow the phases in order.

---

## Table of Contents

1. [Phase 0 — Project Docs](#phase-0-project-docs)
2. [Phase 1 — Design](#phase-1-design)
3. [Phase 2 — Development](#phase-2-development)
4. [Phase 3 — Security](#phase-3-security)
5. [Phase 4 — Pre-Deployment Checklist](#phase-4-pre-deployment-checklist)
6. [Phase 5 — Domain & Deployment](#phase-5-domain-deployment)
7. [Phase 6 — SEO & Local Marketing](#phase-6-seo-local-marketing)
8. [Phase 7 — Launch Checklist](#phase-7-launch-checklist)
9. [Phase 8 — Reliability Hardening](#phase-8-reliability-hardening)
10. [Appendix — Tools & Skills](#appendix-tools-skills)

---

## Phase 0 — Project Docs

### 0.1 Create these MD files BEFORE writing any code

| File | Purpose |
|------|---------|
| `prd.md` | Product Requirements Document |
| `trd.md` | Tech Spec |
| `appflow.md` | App flow / user journeys |
| `design.md` | Design system & visual rules |
| `schema.md` | Database schema |
| `implementationplan.md` | Build phases |
| `tracker.md` | What the model is currently building |
| `rules.md` | Rules for the AI to follow |

### 0.2 PRD.md — Product Requirements Document

The PRD should contain:
- Which problem to solve
- Target users
- What features you're going to have
- Success criteria
- What "NOT" to build

**Prompt to generate the PRD:**

> You are an expert Product Manager helping me write a PRD (Product Requirements Document) for a new app or software project I want to build using AI coding tools like Cursor, Lovable, Claude Code, or Bolt.
>
> Here is my idea:
>
> [DESCRIBE YOUR APP IDEA IN 2–3 SENTENCES]
>
> **STEP 1 — CLARIFYING QUESTIONS** (do this first, before writing anything)
>
> Before generating the PRD, ask me up to 8 focused clarifying questions to fill in any gaps. Cover these areas only if my idea doesn't already answer them:
> 1. Who exactly is the target user? (role, age, skill level, context)
> 2. What is the core problem or pain point being solved?
> 3. What platform? (web app, mobile, browser extension, desktop)
> 4. What tech stack or AI tools should be used, if any preference?
> 5. What does a successful v1 look like — what's the ONE thing it must do well?
> 6. Are there any competitors or existing tools I'm inspired by or want to be different from?
> 7. What is explicitly out of scope for the first version?
> 8. Any monetization, auth, or third-party integrations needed? (e.g., Stripe, Google login)
>
> Ask only the questions that are genuinely unclear from my idea. Keep each question short and specific. Number them. Wait for my answers before writing the PRD.
>
> **STEP 2 — GENERATE THE PRD** (only after I've answered your questions)
>
> Once I respond, generate a complete PRD with these sections:
> - **Problem Statement** — What problem does this solve? Who experiences it? Why does it matter now?
> - **Target User** — Who is the primary user? (be specific — not just "everyone"). Their goals, frustrations, and behaviors.
> - **Core Features (MVP Only)** — 3–5 must-have features for v1, each described in 1–2 sentences. Mark anything "Nice to Have" that is NOT needed for launch.
> - **Out of Scope** — Explicitly list what we are NOT building in v1 (prevents scope creep).
> - **Success Metrics** — 2–3 measurable KPIs (e.g., DAU, task completion rate, retention).
> - **Technical Assumptions** — Preferred tech stack, platform (Web / Mobile / Both), integrations (Stripe, Google Auth, OpenAI API).
> - **Open Questions** — 3–5 things still to be decided before or during development.

---

## Phase 1 — Design

### 1.1 Generate a DESIGN.md (taste-design skill)

Generate a premium, non-generic `DESIGN.md` using semantic design rules. It serves as the single source of truth for prompting AI to generate screens that align with your design language.

**Structure of DESIGN.md:**

```markdown
# Design System: [Project Title]

## 1. Visual Theme & Atmosphere
(Evocative description of mood, density, variance, motion intensity.)

## 2. Color Palette & Roles
- **Canvas White** (#F9FAFB) - Primary background
- **Pure Surface** (#FFFFFF) - Card/container fill
- **Charcoal Ink** (#18181B) - Primary text
- **Muted Steel** (#71717A) - Secondary text
- **Whisper Border** (rgba(226,232,240,0.5)) - Structural lines
- **[Accent Name]** (#XXXXXX) - Single accent

## 3. Typography Rules
- **Display:** [Font Name] - Track-tight hierarchy
- **Body:** [Font Name] - Relaxed leading, 65ch max-width
- **Mono:** [Font Name] - Code/metadata/high-density numbers
- **Banned:** Inter, generic system fonts in premium contexts

## 4. Component Stylings
- **Buttons:** Flat, tactile active state, no outer glow
- **Cards:** Rounded, soft shadow, hierarchy-driven use
- **Inputs:** Label above, error below, accent focus ring
- **Loaders:** Skeletal shimmer
- **Empty States:** Composed guidance

## 5. Layout Principles
(Grid-first responsive architecture, asymmetric hero structures, max-width containment.)

## 6. Motion & Interaction
(Spring physics, staggered reveal, perpetual micro-loops, transform/opacity-only animation.)

## 7. Anti-Patterns (Banned)
(No emojis, no Inter, no pure black, no neon glows, no generic AI filler conventions.)
```

**Design rule reference — Atmosphere spectrum:**
- Density: "Art Gallery Airy" (1-3) → "Daily App Balanced" (4-7) → "Cockpit Dense" (8-10)
- Variance: "Predictable Symmetric" (1-3) → "Offset Asymmetric" (4-7) → "Artsy Chaotic" (8-10)
- Motion: "Static Restrained" (1-3) → "Fluid CSS" (4-7) → "Cinematic Choreography" (8-10)
- Default baseline: Creativity 9, Variance 8, Motion 6, Density 5.

**Color constraints:**
- Maximum 1 accent color; saturation below 80%.
- No "AI purple/blue neon" aesthetic (no purple glows, no neon gradients).
- Neutral bases (Zinc/Slate) with high-contrast singular accents.
- One palette throughout; avoid warm/cool gray shifts.
- Never pure black (`#000000`); use off-black, Zinc-950, or charcoal.

**Typography constraints:**
- `Inter` banned in premium/creative contexts; prefer `Geist`, `Outfit`, `Cabinet Grotesk`, or `Satoshi`.
- Generic serifs (`Times New Roman`, `Georgia`, `Garamond`, `Palatino`) banned.
- Modern serifs only if needed: `Fraunces`, `Gambarino`, `Editorial New`, `Instrument Serif`.
- Serif always banned in dashboards/software UIs.
- Dashboard pairings: `Geist` + `Geist Mono` or `Satoshi` + `JetBrains Mono`.
- Density > 7: all numbers must use monospace.

**Hero section rules:**
- Creative and striking, never generic.
- Inline image typography between words at type-height; no overlapping text.
- No filler copy ("Scroll to explore", "Swipe down", chevrons, bounce prompts).
- Centered hero banned when variance > 4.
- Max one primary CTA, no secondary "Learn more".

**Anti-patterns (NEVER DO):**
- No emojis, no `Inter`, no generic serif fonts, no pure black.
- No neon/outer glow shadows, no oversaturated accents.
- No heavy gradient text on large headers, no custom mouse cursors.
- No overlapping elements, no 3-column equal card layouts.
- No generic names ("John Doe", "Acme", "Nexus").
- No fabricated numbers, metrics, or performance statistics.
- No fake "system metrics" sections with invented data.
- No `LABEL // YEAR` formatting conventions.
- No AI copywriting cliches ("Elevate", "Seamless", "Unleash", "Next-Gen").
- No broken Unsplash links; use `picsum.photos` or SVG avatars.

### 1.2 Design references

- Get designs of popular apps: https://getdesign.md/
- UI reference: https://www.appkittie.com/#home
- Motion/animations: https://motion-primitives.com/docs
- SVG/blob shapes: https://haikei.app/
- Real-time color palette generator: https://www.realtimecolors.com/?colors=050315-fbfbfe-2f27ce-dedcff-433bff&fonts=Inter-Inter

### 1.3 Install design skills

```bash
npx skills add https://github.com/pbakaus/impeccable --skill impeccable
npx impeccable install
# then use: /impeccable init, shape, craft

npx skills add Leonxlnx/taste-skill
npx skills add emilkowalski/skill
npx skills add nutlope/hallmark
npx skills add alchaincyf/huashu-design
```

---

## Phase 2 — Development

### 2.1 Backend setup for vibe-coding

**Every request follows this path:**
```
Frontend → API Routes → Authentication → Validation → Business Logic → Database → Response
```

**Framework → ORM → Database → Testing stack:**
- **Frameworks:** Next.js • Express • FastAPI • Hono
- **ORM:** Prisma • Drizzle
- **Database:** PostgreSQL • MongoDB • Supabase
- **API Testing:** Postman • Bruno

> Don't expose your backend.

**Auth & validation stack:**
- **Authentication:** Clerk • Better Auth • Auth.js • Firebase Auth
- **Validation:** Zod • Valibot • Joi
- **Security:** JWT • Rate Limiting • CORS • Helmet • CSRF • XSS Protection • SQL Injection Protection
- **Secrets:** `.env` • Doppler • Infisical

**Scale stack (design for 10 users or 10 million):**
- **Database:** Prisma • Drizzle
- **Caching:** Redis • Upstash Redis
- **Background Jobs:** BullMQ • Trigger.dev • Inngest
- **Storage:** Cloudinary • AWS S3 • UploadThing

**Production stack (observable, testable, reliable):**
- **Logging:** Pino • Winston
- **Monitoring:** Sentry • Better Stack • Grafana
- **API Docs:** Swagger • Scalar
- **Testing:** Vitest • Jest • Playwright
- **Deployment:** Docker • GitHub Actions • Railway • Render • Fly.io

### 2.2 Frontend — 10 things to keep in mind

1. **User-perceived speed** — Don't make users stare at blank screens. Show content instantly (skeletons, optimistic UI, fast interactions).
2. **Smaller first load** — Homepage doesn't need 4MB of JavaScript. Ship less stuff upfront.
3. **Critical path first** — Load what users SEE first. Above-the-fold content matters most.
4. **Ship less JavaScript** — Keep bundles lean.
5. **Lazy loading** — Don't load charts, modals, or images users may never open.
6. **Protect the main thread** — One heavy render can freeze the entire app.
7. **Stable layouts (CLS)** — Nothing is more annoying than clicking a button and the layout shifts.
8. **Optimize images** — Huge PNGs are performance killers. Use responsive images and modern formats like WebP.
9. **Third-party scripts** — Analytics, ads, chat widgets can be your biggest bottleneck.
10. **Smart caching** — Cache static assets aggressively. Make repeat visits feel instant.

---

## Phase 3 — Security

### 3.1 Security practices to apply always

- **Give your agent standing security rules** — Agents generate from the context they are given. Persistent project rules (`rules.md`) ensure security requirements are applied consistently, not left to each individual prompt.
- **Define an access control matrix** — Document what each role is allowed to do with each resource. Explicit authorization rules prevent gaps when access decisions are left implicit or assumed.

### 3.2 Six core security prompts (run in order)

**1. Secure Authentication** — Stops attackers from taking over accounts.
> Act as a senior security engineer. Review the authentication system of this project and make it secure. Ensure passwords are securely hashed, sessions expire, email verification is enabled, password reset tokens expire, login attempts are rate limited, and authentication secrets are never exposed to the frontend. Refactor any insecure authentication logic.

**2. Protect User Data Access** — Stops attackers from injecting malicious code.
> Identify every place where user input enters the system including forms, APIs, uploads, and query parameters. Add strict validation and sanitization to prevent SQL injection, command injection, script injection, and unsafe file uploads. Reject invalid data and enforce strict input types.

**3. Protect Secrets & API Keys** — Prevents attackers from stealing your credentials.
> Scan the entire project for secrets and credentials. Ensure API keys, database service keys, and tokens are never exposed in frontend code or committed to the repository. Move all secrets to secure environment variables and ensure they are only used on the server.

**4. Input Validation (IDOR / Access Control)** — Ensures users can only access their own data.
> Review all API endpoints and database queries. Ensure every request verifies the logged-in user owns the data being accessed. Prevent insecure direct object reference (IDOR) vulnerabilities by enforcing ownership checks before reading, modifying, or deleting any resource.

**5. Prevent Abuse & Bot Attacks** — Stops bots from spamming and overloading your app.
> Add abuse protection to the application. Implement rate limiting for login attempts, API endpoints, account creation, and AI generation requests. Prevent bots or automated scripts from repeatedly calling endpoints or scraping data.

**6. Secure Deployment** — Protects data in transit and detects suspicious activity.
> Configure the application for secure deployment. Enforce HTTPS, ensure secrets are stored securely, restrict direct database access from the public internet, and add logging for authentication attempts, API errors, and unusual traffic patterns so suspicious behavior can be detected.

### 3.3 Deep-dive security prompts

**1) Validate and clean user input**
> Add server-side input validation to the login and signup routes of this app. For every auth form field (email, password, username, display name):
> - Validate format and length on the server, regardless of frontend checks
> - Sanitize inputs to strip HTML tags, script tags, and special characters
> - Return a generic error message for invalid inputs (do not expose which field failed specifically)
> - Use [Zod/Joi/Pydantic] for schema validation
> - Log validation failures server-side for monitoring
>
> Do not rely on client-side validation alone. Show me the updated route handlers.

**2) Rate limiting and lockout**
> Add rate limiting and account lockout to the login endpoint of this app. Requirements:
> - Rate limit the /login route to max 10 requests per IP per minute
> - Lock the account for 15 minutes after 5 consecutive failed login attempts
> - Implement a progressive delay: each failed attempt increases wait time
> - Store failed attempt counts in [Redis/Upstash/in-memory cache]
> - After lockout, send the user an email notification with a reset link
> - Never reveal whether the lockout is due to too many attempts vs wrong password
>
> Show me the middleware or route handler implementation.

**3) Use strong password hashing**
> Audit and update the password storage in this app to use secure hashing. Requirements:
> - Replace any plain text or MD5/SHA-1 password storage with bcrypt or Argon2id
> - Use a salt round of at least 12 for bcrypt (or equivalent cost factor)
> - Hash passwords before storing on signup AND re-hash on password change
> - Compare hashes using constant-time comparison (never string equality)
> - Add a migration script to rehash any existing plain-text or weakly hashed passwords on next login
> - Never log passwords at any point in the codebase; scan for any console.log that might expose them
>
> Show me the updated auth service and any migration logic needed.

**4) Fix error messages that leak info**
> Audit all authentication error messages in this app and fix any that leak information. Rules:
> - Login failures (wrong email OR wrong password) must return exactly: "Incorrect email or password"
> - Account lockout must NOT mention it's a lockout — return the same generic message
> - Password reset must say: "If that email is registered, you'll receive a reset link"
> - Registration must NOT confirm whether an email already exists
> - Search the entire codebase for any auth-related error string that mentions: "not found", "doesn't exist", "wrong password", "invalid email", "already registered" and replace them with safe generic versions
>
> Show me a list of every changed message and the file locations.

**5) Use trusted auth providers**
> Replace the custom authentication in this app with [Clerk / Supabase Auth / Firebase Auth]. Requirements:
> - Remove any custom password hashing, session management, or JWT logic
> - Integrate the provider's SDK and set up sign-in, sign-up, and sign-out flows
> - Set up social login (Google, GitHub) via the provider's OAuth settings
> - Protect all private routes using the provider's middleware or auth guards
> - Set up webhooks for user creation and deletion events if available
> - Store only non-sensitive user metadata in our own database (user ID, plan, preferences)
> - Never store passwords or tokens
>
> Show me the installation steps, environment variables needed, and updated auth middleware.

### 3.4 General hardening prompt

> Review this app and harden its security. Add:
> 1. Rate limiting on all public endpoints (IP + user-based, sensible defaults, graceful 429s).
> 2. Strict input validation & sanitization on all user inputs (schema-based, type checks, length limits, reject unexpected fields).
> 3. Secure API key handling (remove hard-coded keys, move to environment variables, rotate keys, ensure no keys are exposed client-side). Follow OWASP best practices, include clear comments, and do not break existing functionality.

### 3.5 Context: IDOR in a QR ordering system

IDOR (Insecure Direct Object Reference) falls under **Broken Access Control** — one of the most critical security risks in the OWASP Top 10.

Security recommendations for a QR ordering system:
1. Add proper user authentication (Mobile number + OTP) like modern food ordering apps.
2. Implement strict server-side authorization checks for tables and outlets.
3. Add contextual protections like QR session expiry and location/restaurant Wi-Fi validation.

Stack guidance: use **JWT** to authenticate users, add **middleware** for role-based access, set **CORS origin** to block third-party ports, hash passwords with **bcrypt**, validate with **Zod**, and add other third-party security libraries.

### 3.6 Backend shipping checklist

- [x] API Framework
- [x] Authentication
- [x] Authorization
- [x] Validation
- [x] Database
- [x] ORM
- [x] Environment Variables
- [x] File Storage
- [x] Caching
- [x] Background Jobs
- [x] Logging
- [x] Monitoring
- [x] Testing
- [x] CI/CD
- [x] Deployment

---

## Phase 4 — Pre-Deployment Checklist

- **Lock users to their own UUIDs** — You don't want users to see each other's data.
- **Expire password reset links** — Kill the tokens after 30 minutes so hackers can't hijack old links.
- **Input validation** — Sanitize every single input field. Validate and escape all data to block SQL injection and XSS attacks completely.
- **CORS configuration** — Restrict your API with CORS. Block unauthorized external domains from making rogue requests to your backend.
- **Rate limiting** — Cap request limits to protect your infrastructure from DDoS attacks and massive unexpected bills.
- **Error handling** — Show generic, custom error screens so malicious users can't map out your system vulnerabilities.
- **Database performance** — Index only high-traffic query fields. Speed up main read queries without slowing down database write performance.
- **Logging & monitoring** — Configure active monitoring so you can fix production crashes before your users even notice.
- **Rollback strategy** — Keep an identical environment ready for instant, zero-downtime rollbacks if the new build crashes.

---

## Phase 5 — Domain & Deployment

### 5.1 Step 1 — Set up a subdomain for your app

```
Marketing pages → yourdomain.com
App             → app.yourdomain.com
```

**Why?** So your design and marketing team can change the homepage without ever touching your codebase. The two stay fully independent. (Large companies like Notion or Stripe do this too.)

**How:**
1. Create a new **CNAME DNS record** wherever you bought the domain → point it to where you host your app (e.g., Vercel).
2. Name it `app` (or whatever you want the subdomain to be).

### 5.2 Step 2 — Split emails onto their own subdomains

- `yourdomain.com` → human-written mails (contact, support, personal)
- `mail.yourdomain.com` → app emails (password resets, billing, etc.)
- `news.yourdomain.com` → marketing emails (newsletter, campaigns)

**Why?** It adds an isolation layer. If your emails get flagged as spam, it doesn't immediately drag your main domain down with it. But it's NOT a failsafe — don't abuse it.

**How:**
1. Go to Resend, add each subdomain: https://resend.com/docs/add-a-domain
2. Configure each one with:
   - **SPF** → Says which servers are allowed to send for you
   - **DKIM** → Signs each email so it can't be forged
   - **DMARC** → Tells inboxes what to do if a check fails

**Important:** Don't run cold outreach from these domains. If you burn a subdomain with too much cold outreach, Google can flag your main domain too. Instead: spin up a separate domain, warm it up before sending anything, then redirect it to your main domain so it still looks legit.

### 5.3 Step 3 — Tell Google to index your site

Once your homepage is live on the main domain, create a `sitemap.xml` of your public pages.

```xml
<!-- https://yourdomain.com/sitemap.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/</loc>
  </url>
  <url>
    <loc>https://yourdomain.com/pricing</loc>
  </url>
  <url>
    <loc>https://yourdomain.com/blog</loc>
  </url>
</urlset>
```

**Why?** Without a sitemap, indexing can take a lot longer since Google has to find every page on its own.

**How to set up:**
1. Have AI create a `sitemap.xml` in the root folder of your app.
2. Go to Google Search Console: https://search.google.com/search-console
3. Add your domain.
4. Click on "Sitemaps".
5. Submit `https://yourapp.com/sitemap.xml`.

---

## Phase 6 — SEO & Local Marketing

1. **Connect Gemini** — Link your Google Business Profile to Gemini. Google's AI reads your profile and writes your posts and replies.
2. **Submit your sitemap** — Add it in Google Search Console. It gives Google every page at once. No sitemap, no rankings.
3. **Add your services** — Fill out your business description. Add every service you offer. You rank for every service, not just your main one.
4. **Track your traffic** — Set up Google Analytics. Not all traffic is equal; know if you're getting the right visitors.
5. **Compress your images** — Shrink every image on your site. Images are the number one thing slowing your site down.
6. **Add a Google Map** — Embed your map on your website. It shows where you are and reinforces your location to Google.
7. **Fix your 404 pages** — Use the free Redirection plugin. Broken pages frustrate visitors and waste Google's crawl.
8. **Add an SSL certificate** — Turn on the padlock (HTTPS). No padlock = Google and visitors stop trusting you.
9. **Add your footer info** — Name, address, and phone on every page. Google sees one consistent location and customers can always reach you.
10. **Chamber of Commerce** — Ask them to list your business. A trusted local link that tells Google you're established.

---

## Phase 7 — Launch Checklist

### 7.1 Legal & Compliance
- [ ] Privacy Policy page
- [ ] Terms & Conditions (Terms of Service)
- [ ] Cookie consent (especially if targeting EU — GDPR)

Legal page templates: https://docs.google.com/document/d/1iMLeBKhGOTBEqujhviLx4gwB1ePUOnV8kHDNTItjVzQ/mobilebasic

### 7.2 Auth & Security
- [ ] Signup / login flow tested
- [ ] Email verification working
- [ ] Password reset flow
- [ ] OAuth (Google, etc.) working if included
- [ ] Rate limiting (prevent brute force)

### 7.3 Payment
- [ ] Payment flow fully tested (success + failure cases)
- [ ] Subscription lifecycle: Upgrade / Downgrade / Cancel

### 7.4 Analytics & Tracking
- [ ] User Event Tracking
- [ ] Page Tracking

### 7.5 Marketing Basics
- [ ] Submit page to Google Search Console
- [ ] Submit on other search engines
- [ ] Check for SEO basics

### 7.6 Feedback Loop
- [ ] Contact / Support Email
- [ ] Bug report option

---

## Phase 8 — Reliability Hardening

*(Prevent your vibe-coded website from being one user away from crashing.)*

- Input sanitization and injection prevention
- Authentication, authorization, roles, and permissions
- Session management and token expiry
- Secrets management
- HTTPS, TLS configuration, and certificate rotation
- Rate limiting and abuse prevention
- Dependency scanning and vulnerability patching
- Multi-tenancy and data isolation
- PII handling, data retention, and deletion policies
- Regulatory compliance (GDPR, HIPAA)
- Audit trails and tamper-evident logging
- Unit, integration, and end-to-end tests
- Regression tests
- Load and stress testing
- Chaos engineering and resilience testing
- Test coverage thresholds enforced in CI
- Code review process and standards
- Error handling and graceful degradation
- Retry logic with backoff and idempotency
- Circuit breakers and fallback behavior
- Concurrency handling and race condition prevention
- Caching strategy (and invalidation)
- RTO and RPO
- Disaster recovery plan
- Accessibility
- Architecture diagrams, ADRs

---

## Appendix — Tools & Skills

### AI coding / project tools
- Project scaffolding: `npx @opengsd/gsd-core@latest` → `/gsd-new-project`
- GSD (GitHub): https://github.com/snarktank/ralph
- Code review bot: https://www.coderabbit.ai/pricing

### Database / backend
- Convex (pricing): https://www.convex.dev/pricing

### Understanding codebases
- https://understand-anything.com/#install

### Free setup guide
- Build a $10K website in Claude Code (free setup guide): https://noocap.notion.site/Build-a-10K-Website-in-Claude-Code-Free-Setup-Guide-356508e99dda816c9d15ea892d4139f9

### More prompts
- https://achieved-cloak-445.notion.site/Prompts-397e13e8b39080b4beebf8da644def5f
