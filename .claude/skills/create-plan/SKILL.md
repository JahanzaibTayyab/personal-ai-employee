---
name: create-plan
description: Generate Plan.md files for multi-step task breakdowns using Claude's reasoning loop. Use when user has a complex task requiring multiple steps, wants to plan a workflow, needs to break down a project into actionable steps, or asks to create a plan for any multi-step operation.
---

# Create Plan

Generate a Plan.md file that breaks down complex tasks into numbered steps with dependencies and approval requirements.

## Usage

```
/create-plan <task_description>
```

## Arguments

- `task_description` (required): Natural language description of the task to plan

## Examples

```
/create-plan "Send weekly newsletter to all subscribers"
/create-plan "Onboard new client: setup account, send welcome email, schedule intro call"
/create-plan "Prepare quarterly business report with sales data and projections"
/create-plan "Launch new product feature with announcement email and social posts"
```

## Workflow

1. Analyze task description for complexity
2. If simple (single action): execute directly without plan
3. If complex (multi-step):
   - Break into numbered steps
   - Identify dependencies between steps
   - Mark steps requiring approval
   - Define success criteria
4. Create Plan.md in `/Plans/`
5. Return plan summary with step count

## Plan.md Structure

```markdown
---
id: plan_<timestamp>_<hash>
objective: "Task description"
status: pending
created_at: <ISO datetime>
---

# Plan: <Objective>

## Objective
<What this plan accomplishes>

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Steps

### Step 1: <Description>
- **Status**: pending
- **Requires Approval**: No/Yes
- **Dependencies**: None

<Step details>

### Step 2: <Description>
- **Status**: pending
- **Requires Approval**: No
- **Dependencies**: Step 1

<Step details>
```

## Step Status Values

- `pending` - Not started
- `in_progress` - Currently executing
- `completed` - Successfully finished
- `failed` - Execution failed
- `awaiting_approval` - Paused for human approval

## Approval Integration

Steps marked with `Requires Approval: Yes` will:
1. Pause plan execution when reached
2. Create approval request in `/Pending_Approval/`
3. Resume automatically when approved
4. Skip step if rejected

## Output

- **Plan file**: `/Plans/plan_<timestamp>.md`
- **Dashboard update**: Active plans section updated
