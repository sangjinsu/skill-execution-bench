---
id: skill.go-binary
name: Normalize Task Records (Go Binary)
execution_mode: go-binary
version: 0.1.0
---

# Normalize Task Records (Go Binary)

## When to use

Use this Skill when you need to normalize a list of task records via a compiled,
standalone binary. The reusable implementation is written in Go and must be built
before execution. Prefer this when you want a fast, dependency-free executable that
behaves identically across machines.

## Inputs

- A JSON array of task records on **stdin**.
- Records may have inconsistent casing, whitespace, mixed status labels, and optional fields.

## Expected output

- A normalized JSON array on **stdout** (compact, no spaces), following the shared contract:
  - All string values trimmed.
  - `id` is a trimmed string.
  - `status` is trimmed, lowercased, then mapped:
    `todo|to do|pending → todo`, `doing|in progress|wip → doing`,
    `done|complete|completed → done`; unknown values keep their lowercased/trimmed form.
  - Missing optional fields are not added.
  - Key order per object: `id`, `title`, `status`, then remaining keys alphabetically.
  - Array sorted by `id` (numeric when all ids are integers, else lexicographic).
- Exit code `0` on success, non-zero on invalid input.

## Procedure

1. **If the binary already exists at `skills/go-binary/bin/skill-runner`, skip the
   build and run it directly.** Build only when it is missing (standard library only,
   no modules to download):

   ```bash
   go build -o skills/go-binary/bin/skill-runner ./skills/go-binary/cmd/skill-runner
   ```

   (or `make build-go`)

2. Run it, piping input JSON to stdin:

   ```bash
   skills/go-binary/bin/skill-runner < input.json > output.json
   ```

   ```bash
   echo '[{"id":" 2 ","title":" Fix Login ","status":"In Progress"}]' \
     | skills/go-binary/bin/skill-runner
   ```

Build first, then invoke the binary. Do not reimplement the logic by hand.

## Validation

- [ ] `skills/go-binary/bin/skill-runner` exists (binary was built).
- [ ] Output parses as JSON and is an array.
- [ ] Output matches the Python-script output byte-for-byte for the same input.
- [ ] Records are ordered by `id`.
- [ ] Invalid input (non-array, malformed JSON) causes a non-zero exit code.
