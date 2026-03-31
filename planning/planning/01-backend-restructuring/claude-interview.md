# Interview Transcript: Split 01 — Backend Task Model & API Restructuring

## Q1: Database State for Migration
**Q:** For the RecurringTaskTemplate → AgentGlobalTask migration: are there existing recurring task templates with real data in production that need to be preserved, or is the database relatively fresh/development-only?

**A:** Fresh/dev database — little or no real recurring template data. Migration can be straightforward.

## Q2: JIT Recurring Task Behavior
**Q:** When a recurring task is completed and JIT generates the next instance, should the next instance always be auto-created silently, or should the agent have a choice?

**A:** Always auto-create — next instance is always generated. Agent can delete it if unwanted.

## Q3: Approval Workflow Scope
**Q:** For the admin approval workflow (in_review status): can any agent move any task to in_review, or only tasks tagged with specific categories/clients?

**A:** Required for certain categories — some categories (set by admin) require review before marking done. The TaskCategory model needs a `requires_review` flag.

## Q4: API Transition Strategy
**Q:** Should the old recurring task API endpoints still function during transition, or be removed immediately?

**A:** Remove immediately — clean break. Frontend gets updated in same deploy, no backward compatibility needed.

## Q5: Category Visibility by Department
**Q:** Should agents only see categories matching their department, or see all categories?

**A:** Department-filtered only — marketing agents see only marketing+both categories, dev agents see only developer+both.

## Q6: Review Status Trigger Mechanism
**Q:** When an agent completes a task in a review-required category, should the status automatically jump to 'in_review' or should the agent explicitly submit?

**A:** Auto-set on completion — when agent marks task 'done' in a review-required category, status becomes 'in_review' instead of 'done'. Backend enforces this.

## Q7: ScheduledTaskLink Pattern
**Q:** With the unified model, should we keep GenericForeignKey or simplify to a direct FK?

**A:** Simplify to direct FK — replace GenericForeignKey with a direct FK to AgentGlobalTask since we're unifying the task model.

## Q8: Seed Category Strategy
**Q:** Should default categories be created automatically in migration or via management command?

**A:** Auto-seed in migration — data migration creates default categories, guaranteed to exist after migrate.

## Q9: Celery Periodic Task Generator
**Q:** With JIT generation, should the periodic task generator be removed entirely or kept as safety net?

**A:** Remove periodic generator — JIT is the sole mechanism. Clean break, simpler system.
