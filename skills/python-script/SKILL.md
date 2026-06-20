---
id: skill.python-script
name: Normalize Task Records (Python Script)
execution_mode: python-script
version: 0.1.0
---

# Normalize Task Records (Python Script)

## When to use

Use this Skill when you need to normalize a list of task records and a reusable Python
script is the preferred execution path. The implementation lives in a separate `.py` file;
you run it rather than re-deriving the logic.

## Inputs

- A JSON array of task records on **stdin**.
- Each record may have inconsistent casing, surrounding whitespace, mixed status labels,
  and optional extra fields.

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

Run the bundled script, piping the input JSON to stdin and capturing stdout:

```bash
python skills/python-script/scripts/transform.py < input.json > output.json
```

Or with a heredoc / pipe:

```bash
echo '[{"id":" 2 ","title":" Fix Login ","status":"In Progress"}]' \
  | python skills/python-script/scripts/transform.py
```

Do not reimplement the normalization inline — invoke the script so behavior stays
consistent and testable.

## Validation

- [ ] Output parses as JSON and is an array.
- [ ] Every `status` is one of the mapped canonical values (or an intentionally unmapped label).
- [ ] Records are ordered by `id`.
- [ ] Invalid input (non-array, malformed JSON) causes a non-zero exit code.
