# Implementation Tasks

**Bead:** [bead-id]
**Spec:** [link to spec]
**Date:** [YYYY-MM-DD]

---

## Task Metadata

Each task can have these optional fields in YAML frontmatter:

```yaml
---
id: "1.1" # Task identifier
depends_on: [] # Task IDs that must complete first
parallel: true # Can run concurrently with other parallel tasks
conflicts_with: [] # Task IDs that modify same files (cannot parallelize)
files: [] # Files this task will modify
estimated_minutes: 30 # Time estimate for planning
---
```

---

## 1. Setup

### 1.1 [Prerequisite task]

```yaml
depends_on: []
parallel: false
files: ["package.json", "tsconfig.json"]
```

- [ ] [Task description]

### 1.2 [Environment or config task]

```yaml
depends_on: ["1.1"]
parallel: false
files: [".env.example"]
```

- [ ] [Task description]

---

## 2. Core Implementation

### 2.1 [Primary implementation task]

```yaml
depends_on: ["1.1", "1.2"]
parallel: true
conflicts_with: []
files: ["src/feature/index.ts"]
```

- [ ] [Task description]

### 2.2 [Secondary implementation task]

```yaml
depends_on: ["1.1", "1.2"]
parallel: true
conflicts_with: []
files: ["src/feature/utils.ts"]
```

- [ ] [Task description]

### 2.3 [Integration task]

```yaml
depends_on: ["2.1", "2.2"]
parallel: false
conflicts_with: []
files: ["src/feature/index.ts", "src/feature/utils.ts"]
```

- [ ] [Task description]

---

## 3. Testing

### 3.1 [Unit test task]

```yaml
depends_on: ["2.1"]
parallel: true
files: ["tests/feature.test.ts"]
```

- [ ] [Task description]

### 3.2 [Integration test task]

```yaml
depends_on: ["2.3"]
parallel: true
files: ["tests/integration/feature.test.ts"]
```

- [ ] [Task description]

### 3.3 [Edge case verification]

```yaml
depends_on: ["3.1", "3.2"]
parallel: false
files: []
```

- [ ] [Task description]

---

## 4. Documentation

### 4.1 [Code comments / JSDoc]

```yaml
depends_on: ["2.3"]
parallel: true
files: ["src/feature/*.ts"]
```

- [ ] [Task description]

### 4.2 [README updates]

```yaml
depends_on: ["2.3"]
parallel: true
files: ["README.md"]
```

- [ ] [Task description]

---

## 5. Verification

### 5.1 All tests pass

```yaml
depends_on: ["3.1", "3.2", "3.3"]
parallel: false
```

- [ ] `[test command]`

### 5.2 Lint clean

```yaml
depends_on: ["2.3", "4.1"]
parallel: true
```

- [ ] `[lint command]`

### 5.3 Build succeeds

```yaml
depends_on: ["5.1", "5.2"]
parallel: false
```

- [ ] `[build command]`

---

## Dependency Graph

Visualize task flow (auto-generated from above):

```
1.1 ──┬──> 2.1 ──┬──> 2.3 ──┬──> 3.2 ──┬──> 5.1 ──> 5.3
     │         │         │         │
1.2 ──┘   2.2 ──┘    3.1 ──┘    5.2 ──┘
                      │
                 4.1 ──┘
                 4.2
```

**Legend:**

- `──>` = depends_on (sequential)
- Tasks at same level with `parallel: true` = can run concurrently

---

## Notes

<!-- Implementation notes, gotchas, or decisions made during task creation -->
