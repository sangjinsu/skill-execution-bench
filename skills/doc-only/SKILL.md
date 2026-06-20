---
id: skill.doc-only
name: Normalize Task Records (Doc Only)
execution_mode: doc-only
version: 0.1.0
---

# Normalize Task Records (Doc Only)

## When to use

Use this Skill when you need to normalize a list of task records and only written
instructions are available. There is no reusable code here — reason through the rules
below and produce the output by hand.

## Inputs

- A JSON array of task records.
- Each record may contain:
  - inconsistent casing (e.g. `"In Progress"`, `"DONE"`),
  - surrounding whitespace (e.g. `" Fix Login "`, `" 2 "`),
  - mixed status labels (e.g. `"wip"`, `"to do"`, `"completed"`),
  - optional extra fields (e.g. `"assignee"`).

## Expected output

A normalized JSON array where every record and the array as a whole follow the contract
in the Procedure section. Output should be compact JSON (no extra spaces).

## Procedure

Apply these rules, in order, to produce the result:

1. **Trim every string value** — remove leading and trailing whitespace.
2. **`id`** — trim it and treat it as a string (e.g. `" 2 "` → `"2"`, number `2` → `"2"`).
3. **`status`** — trim, lowercase, then map to a canonical value:
   - `todo`, `to do`, `pending` → `todo`
   - `doing`, `in progress`, `wip` → `doing`
   - `done`, `complete`, `completed` → `done`
   - any other value: keep it lowercased and trimmed (do not invent a mapping).
4. **Other fields** (e.g. `title`, `assignee`) — trim the string value; keep the field.
5. **Missing optional fields** — do not add them. Only emit keys that were present.
6. **Key order within each object** — `id` first, then `title`, then `status`, then any
   remaining keys in alphabetical order.
7. **Array order** — sort records by `id`. If every `id` is an integer, sort numerically
   (so `2` comes before `10`); otherwise sort lexicographically as strings.

### Worked example

Input:

```json
[{"id":" 2 ","title":" Fix Login ","status":"In Progress"},
 {"id":"1","title":"Write Tests","status":"complete"}]
```

Output:

```json
[{"id":"1","title":"Write Tests","status":"done"},{"id":"2","title":"Fix Login","status":"doing"}]
```

## Validation

- [ ] The result is a JSON array.
- [ ] Each string value has no leading/trailing whitespace.
- [ ] Each `status` is `todo`, `doing`, `done`, or a deliberately unmapped lowercase label.
- [ ] Keys appear in the order `id`, `title`, `status`, then alphabetical.
- [ ] Records are ordered by `id` (numeric when all ids are integers).
- [ ] No optional fields were invented for records that lacked them.
