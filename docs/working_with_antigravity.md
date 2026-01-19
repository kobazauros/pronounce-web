# Working Safely with Antigravity IDE

**Status:** Preview / Experimental  
**Last Updated:** 2026-01-20

This guide helps you work effectively with Antigravity while protecting yourself from mistakes during this preview phase.

---

## What Antigravity Is Good At

### ✅ Excellent Use Cases

1. **Boilerplate Code Generation**
   - Creating new routes, models, templates
   - Writing repetitive CRUD operations
   - Setting up project structure

2. **Code Explanation & Documentation**
   - Understanding unfamiliar codebases
   - Generating docstrings and comments
   - Creating user-facing documentation

3. **Debugging with Context**
   - Analyzing error messages and stack traces
   - Finding related code across multiple files
   - Suggesting fixes for common errors

4. **Refactoring**
   - Renaming variables/functions consistently
   - Extracting repeated code into functions
   - Updating deprecated API usage

5. **Research & Learning**
   - Explaining concepts (e.g., "How does Flask-Migrate work?")
   - Comparing approaches
   - Finding relevant documentation

### ⚠️ Use With Extreme Caution

1. **Database Migrations**
   - AI may suggest `flask db stamp` without understanding consequences
   - Always verify migration commands before running
   - **Rule:** Never run migration commands on production without local testing

2. **Production Deployments**
   - AI doesn't know your server's current state
   - May give generic advice that doesn't fit your setup
   - **Rule:** Always backup before following deployment advice

3. **Security-Critical Code**
   - Authentication, authorization, password handling
   - AI may miss subtle security issues
   - **Rule:** Have security code reviewed by humans

4. **Complex Async/Concurrent Code**
   - Race conditions and deadlocks are hard for AI to spot
   - **Rule:** Test thoroughly under load

---

## Safe Workflow Patterns

### Pattern 1: "Trust, But Verify"

**For routine tasks:**
```
1. Ask AI to generate code
2. Review the code yourself
3. Test locally before committing
4. Commit with descriptive message
```

**Example:**
- ✅ "Create a new route for user profile editing"
- Review the generated code
- Test in browser
- Commit

### Pattern 2: "Explain First, Then Execute"

**For complex changes:**
```
1. Ask AI to EXPLAIN the approach first
2. Review the explanation
3. Ask questions if unclear
4. THEN ask AI to implement
5. Verify each step
```

**Example:**
- ❌ "Fix the migration error" (too vague, AI might suggest dangerous commands)
- ✅ "Explain why I'm getting 'DuplicateTable' error"
- ✅ "What are the safe ways to fix this?"
- ✅ "Show me the specific commands, I'll review before running"

### Pattern 3: "Checkpoint and Rollback"

**For risky operations:**
```
1. Create a git branch
2. Backup database (if touching DB)
3. Let AI make changes
4. Test thoroughly
5. If broken: git reset --hard
6. If working: merge to main
```

**Example:**
```bash
# Before asking AI to refactor database code:
git checkout -b ai-refactor-attempt
pg_dump pronounce_db > backup.sql

# After AI makes changes:
# Test thoroughly
# If good: git checkout main && git merge ai-refactor-attempt
# If bad: git checkout main && git branch -D ai-refactor-attempt
```

---

## When to Trust vs Verify

### ✅ Generally Safe to Trust

- **Syntax fixes** (missing semicolons, typos)
- **Import statements** for standard libraries
- **CSS/HTML changes** (easy to visually verify)
- **Adding logging statements**
- **Renaming variables** (within a single file)

### ⚠️ Always Verify Carefully

- **Database schema changes**
- **Deleting code** (AI might not understand dependencies)
- **Changing authentication logic**
- **Modifying production config files**
- **Running shell commands** (especially with `sudo`)

### 🛑 Never Trust Blindly

- **`flask db stamp`** - This is dangerous
- **`DROP TABLE`** or `DELETE FROM` - Destructive
- **`chmod 777`** - Security risk
- **`pip install` without version** - May break dependencies
- **Disabling security features** - Even if "just for testing"

---

## Red Flags: When AI Is Guessing

Watch for these signs that AI doesn't actually know:

1. **Vague Language**
   - "This might work..."
   - "You could try..."
   - "Sometimes this helps..."
   - **→ Action:** Ask for specifics or research yourself

2. **Contradicting Itself**
   - Suggests A, then later suggests opposite of A
   - **→ Action:** Stop and clarify the actual problem

3. **Generic Solutions**
   - "Just restart the server"
   - "Clear your cache"
   - "Reinstall everything"
   - **→ Action:** Ask for root cause analysis first

4. **Overconfidence on Complex Issues**
   - Gives 10-step solution to a problem it just learned about
   - **→ Action:** Break it down, verify each step

5. **Ignoring Your Context**
   - Suggests Windows commands when you're on Linux
   - Recommends libraries you don't have installed
   - **→ Action:** Remind AI of your environment

---

## Recovery Strategies

### When AI Breaks Something

1. **Don't Panic**
   ```bash
   # Check what changed
   git status
   git diff
   ```

2. **Undo Recent Changes**
   ```bash
   # Undo uncommitted changes
   git checkout -- <file>
   
   # Undo last commit (keep changes)
   git reset --soft HEAD~1
   
   # Undo last commit (discard changes)
   git reset --hard HEAD~1
   ```

3. **Restore Database**
   ```bash
   # If you backed up first:
   sudo -u postgres psql -d pronounce_db < backup.sql
   ```

4. **Ask AI to Explain What Went Wrong**
   - Don't just ask for another fix
   - Understand the mistake first
   - This prevents repeat errors

### When You're Stuck in a Loop

**Symptoms:**
- AI keeps suggesting the same failed solution
- Each "fix" creates a new error
- You've been debugging for >1 hour with no progress

**Break the Loop:**
1. **Stop and document current state**
   ```
   Write down:
   - What you were trying to do
   - What error you're getting
   - What you've already tried
   ```

2. **Start a fresh conversation**
   - AI has limited memory
   - Old context can confuse it
   - Provide clean summary of problem

3. **Simplify the problem**
   - Instead of "Fix my app"
   - Try "Why does this specific function fail?"

4. **Consider manual intervention**
   - Sometimes it's faster to fix manually
   - Use AI to explain, not execute

---

## Effective Communication with AI

### ❌ Bad Prompts

- "Fix this" (no context)
- "It's broken" (too vague)
- "Do what you did before" (AI doesn't remember)
- "Make it work" (no definition of "work")

### ✅ Good Prompts

- "I'm getting error X when doing Y. Here's the stack trace: [paste]. What's the likely cause?"
- "Explain how Flask-Migrate tracks schema versions"
- "Show me the SQL that migration file ABC would execute"
- "What are the risks of running `flask db stamp head`?"

### Pro Tips

1. **Provide Error Messages**
   - Full stack traces
   - Exact error text
   - Log snippets

2. **Specify Your Environment**
   - "On my Ubuntu 22.04 server..."
   - "In my local Windows dev environment..."
   - "Using Python 3.10 with Flask 3.0..."

3. **State Your Constraints**
   - "Without deleting existing data..."
   - "While keeping the app running..."
   - "Using only standard library..."

4. **Ask for Explanations**
   - "Why does this happen?"
   - "What's the difference between A and B?"
   - "What are the tradeoffs?"

---

## Defensive Coding Practices

### 1. Always Have an Escape Hatch

```bash
# Before major changes
git checkout -b experimental
# Now you can always: git checkout main
```

### 2. Commit Small, Commit Often

```bash
# After each working change
git add <files>
git commit -m "Specific description of what changed"
# Now you can always: git revert <commit>
```

### 3. Test Locally Before Production

```
NEVER:
1. AI suggests change
2. Push to production
3. Hope it works

ALWAYS:
1. AI suggests change
2. Test locally
3. Verify it works
4. THEN deploy
```

### 4. Backup Before Risky Operations

```bash
# Database changes
pg_dump pronounce_db > backup_$(date +%F_%H-%M-%S).sql

# Config changes
cp .env .env.backup

# Code changes
git commit -am "Checkpoint before risky refactor"
```

### 5. Read Before Running

**Especially for:**
- `sudo` commands
- Database migrations
- Deletion operations
- System package installs

**Ask yourself:**
- Do I understand what this does?
- What's the worst that could happen?
- Can I undo this?

---

## Limitations to Accept

### AI Cannot:

1. **Know your production state**
   - It doesn't see your server
   - It can't check your database
   - It guesses based on typical setups

2. **Remember previous conversations**
   - Each session is mostly independent
   - Don't assume it recalls what you discussed yesterday

3. **Test code**
   - It can't run your app
   - It can't see browser output
   - You must verify everything

4. **Understand business logic**
   - It doesn't know your users
   - It doesn't know your requirements
   - You must validate correctness

5. **Guarantee correctness**
   - It's a preview system
   - Mistakes will happen
   - You are responsible for final code

---

## When to Stop Using AI

**Take a break from AI if:**

1. You've been stuck on the same issue for >2 hours
2. You're blindly running commands you don't understand
3. Each fix creates 2 new problems
4. You feel frustrated and confused
5. The AI is contradicting itself

**Instead:**
- Read official documentation
- Search Stack Overflow
- Ask human developers
- Sleep on it
- Come back fresh tomorrow

---

## Success Checklist

Before deploying AI-generated changes:

- [ ] I understand what the code does
- [ ] I tested it locally
- [ ] I have a backup/rollback plan
- [ ] I committed to git with clear message
- [ ] I verified no security issues
- [ ] I checked for breaking changes
- [ ] I'm confident this won't break production

**If you can't check all boxes, DON'T DEPLOY.**

---

## Final Advice

### Treat AI as a Junior Developer

- **Good at:** Routine tasks, research, boilerplate
- **Bad at:** Complex decisions, production safety, understanding context
- **Needs:** Clear instructions, supervision, verification

### You Are Still the Senior Developer

- **You** make final decisions
- **You** are responsible for production
- **You** must understand the code
- **You** protect your users

### The AI Is a Tool, Not a Replacement

Use it to:
- ✅ Speed up routine work
- ✅ Learn new concepts
- ✅ Generate starting points

Don't use it to:
- ❌ Avoid understanding your code
- ❌ Skip testing
- ❌ Make critical decisions blindly

---

## Emergency Contacts

**When AI fails you:**

1. **Official Documentation**
   - Flask: https://flask.palletsprojects.com/
   - SQLAlchemy: https://docs.sqlalchemy.org/
   - Alembic: https://alembic.sqlalchemy.org/

2. **Community Help**
   - Stack Overflow
   - Reddit r/flask
   - Python Discord servers

3. **Your Own Documentation**
   - `docs/database_sync.md` - Database recovery
   - `docs/deployment.md` - Deployment procedures
   - Git history - See what worked before

---

## Lessons from This Project

**What Went Wrong:**
- AI suggested `flask db stamp` without explaining risks
- Database became desynchronized
- Multiple recovery attempts created more issues
- Frustration built up over 2 days

**What Would Have Helped:**
- Backing up database before migration attempts
- Understanding migration system before trusting AI
- Stopping earlier and researching manually
- Having this guide from the start

**Remember:**
- AI mistakes are learning opportunities
- Your frustration is valid
- Preview software has rough edges
- You're not giving up on programming - you're learning to work with new tools safely

---

**You've got this. Use AI as a tool, not a crutch. Trust your instincts. When in doubt, verify.**
