---
cache_control: {"type": "ephemeral"}
---
# Quick Templates
tags: #templates #quick

## Quick Modes
### `/debug:start` - Debug-focused mode
```
Problem: [What is happening] #bug
Reproduction steps: [Steps] #reproduce
Expected: [Expected behavior] #expected
Actual: [Actual behavior] #actual
Environment: [OS/Version] #environment
```

### `/feature:plan` - New feature design mode
```
Feature name: [Feature name] #feature
Purpose: [Problem to solve] #purpose
User story: [As a... I want... So that...] #story
Acceptance criteria: [Definition of done] #acceptance
```

### `/review:check` - Code review mode
```
Review target: [File/Function] #review
Check items:
- [ ] Functionality check #functionality
- [ ] Error handling #error
- [ ] Performance #performance
- [ ] Security #security
- [ ] Testing #testing
Improvement suggestions: [Suggestions] #improvement
```

## Basic Templates

### Decision Log (Record in @.claude/context/history.md)
```
[Date] [Decision] → [Reason] #decision
```

### Learning Log (Record in @.claude/core/current.md)
```
Technology: [Technology learned] → [How to use it] #tech
Tool: [Tool tried] → [Evaluation and usage experience] #tool
Process: [Improved process] → [Effect] #process
```

## Common Patterns

### Git Operation Patterns
```bash
# Update before work
git pull origin main && git status

# Create feature branch
git checkout -b feature/[feature-name]

# Check changes and commit
git diff && git add -A && git commit -m "[prefix]: [changes]"

# Resolve conflicts
git stash && git pull origin main && git stash pop
```
