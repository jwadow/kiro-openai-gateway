---
name: skill-creator
description: Guide for creating effective skills. Use when creating a new skill or updating an existing skill that extends an agent's capabilities with specialized knowledge, workflows, or tool integrations.
---

# Skill Creator

Guide for creating effective skills that extend agent capabilities.

> **CRITICAL: YAML FRONTMATTER REQUIRED**
> Every SKILL.md **MUST** begin with YAML frontmatter on line 1.
>
> ```yaml
> ---
> name: skill-name
> description: One-line description of what this skill does
> ---
> ```

## What Skills Provide

1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex tasks

## Skill Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation loaded as needed
    └── assets/           - Files used in output (templates, icons)
```

## Requirements

- `SKILL.md` should be **less than 200 lines**
- Use `references/` for detailed documentation
- Each script or reference file also **less than 200 lines**
- Descriptions must be specific about WHEN to use the skill

## SKILL.md Format

**REQUIRED - DO NOT SKIP**

```yaml
---
name: skill-name
description: What this skill does and when to use it. Use third-person.
---
```

**Required fields:**

- `name` — hyphen-case identifier matching directory name
- `description` — activation trigger; be specific about WHEN to use

**Optional fields:**

```yaml
---
name: skill-name
description: What this skill does and when to use it.
references:
  - references/guide.md
  - references/api.md
license: Apache-2.0
---
```

**INVALID - Do NOT use:**

- XML-style tags (`<purpose>`, `<references>`)
- Missing `---` delimiters
- Frontmatter that doesn't start at line 1

## Bundled Resources

### Scripts (`scripts/`)

- When the same code is being rewritten repeatedly
- When deterministic reliability is needed
- Prefer Node.js or Python over Bash (Windows support)

### References (`references/`)

- Documentation that agent should reference while working
- Database schemas, API docs, domain knowledge
- If files are large (>10k words), include grep patterns in SKILL.md

### Assets (`assets/`)

- Files used in the final output (not loaded into context)
- Templates, images, icons, boilerplate code

## Progressive Disclosure

Skills use three-level loading:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by agent (Unlimited)

## Skill Creation Process

### Step 1: Understand with Examples

- "What functionality should the skill support?"
- "Can you give examples of how this would be used?"
- "What would a user say that should trigger this skill?"

### Step 2: Plan Reusable Contents

For each example, identify:

- What scripts would be helpful to store?
- What references/documentation needed?
- What assets/templates needed?

### Step 3: Create the Skill

```bash
mkdir -p .opencode/skill/my-skill
touch .opencode/skill/my-skill/SKILL.md
```

### Step 4: Edit SKILL.md

Answer these questions:

1. What is the purpose of the skill?
2. When should it be used?
3. How should the agent use it?

### Step 5: Iterate

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Update SKILL.md or bundled resources
4. Test again

## Pre-Submission Checklist

- [ ] **SKILL.md starts with `---`** (YAML frontmatter, line 1)
- [ ] **`name:` field present** and matches directory name
- [ ] **`description:` field present** with specific activation triggers
- [ ] **Closing `---`** after frontmatter
- [ ] **No XML-style tags**
- [ ] **SKILL.md under 200 lines**
- [ ] **All referenced files exist**
