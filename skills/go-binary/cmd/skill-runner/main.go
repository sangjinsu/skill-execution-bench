// Command skill-runner normalizes task records.
//
// It reads a JSON array from stdin and writes a normalized, compact JSON array
// to stdout. It exits non-zero on invalid input. Standard library only; no
// network access; fully deterministic.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"
)

var statusMap = map[string]string{
	"todo":        "todo",
	"to do":       "todo",
	"pending":     "todo",
	"doing":       "doing",
	"in progress": "doing",
	"wip":         "doing",
	"done":        "done",
	"complete":    "done",
	"completed":   "done",
}

// keyPriority gives id/title/status a fixed leading order; other keys sort after.
var keyPriority = map[string]int{"id": 0, "title": 1, "status": 2}

func priority(key string) int {
	if p, ok := keyPriority[key]; ok {
		return p
	}
	return 3
}

func normalizeStatus(v interface{}) interface{} {
	s, ok := v.(string)
	if !ok {
		return v
	}
	key := strings.ToLower(strings.TrimSpace(s))
	if mapped, ok := statusMap[key]; ok {
		return mapped
	}
	return key
}

func orderedKeys(record map[string]interface{}) []string {
	keys := make([]string, 0, len(record))
	for k := range record {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		pi, pj := priority(keys[i]), priority(keys[j])
		if pi != pj {
			return pi < pj
		}
		return keys[i] < keys[j]
	})
	return keys
}

func isInt(v interface{}) bool {
	_, err := strconv.Atoi(strings.TrimSpace(idString(v)))
	return err == nil
}

// idString renders an id value as a string. JSON numbers arrive as float64.
func idString(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case float64:
		// ids in this benchmark are integer-valued; format without trailing zeros.
		if t == float64(int64(t)) {
			return strconv.FormatInt(int64(t), 10)
		}
		return strconv.FormatFloat(t, 'g', -1, 64)
	case nil:
		return ""
	default:
		return fmt.Sprintf("%v", t)
	}
}

// orderedRecord is one normalized record with its key order preserved.
type orderedRecord struct {
	keys   []string
	values map[string]interface{}
	id     string
}

func normalize(records []interface{}) ([]orderedRecord, error) {
	out := make([]orderedRecord, 0, len(records))
	for _, r := range records {
		record, ok := r.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("each record must be a JSON object")
		}
		keys := orderedKeys(record)
		values := make(map[string]interface{}, len(keys))
		for _, k := range keys {
			value := record[k]
			switch k {
			case "status":
				values[k] = normalizeStatus(value)
			case "id":
				values[k] = strings.TrimSpace(idString(value))
			default:
				if s, ok := value.(string); ok {
					values[k] = strings.TrimSpace(s)
				} else {
					values[k] = value
				}
			}
		}
		out = append(out, orderedRecord{
			keys:   keys,
			values: values,
			id:     strings.TrimSpace(idString(record["id"])),
		})
	}

	allInt := len(out) > 0
	for _, rec := range out {
		if !isInt(rec.id) {
			allInt = false
			break
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		if allInt {
			a, _ := strconv.Atoi(out[i].id)
			b, _ := strconv.Atoi(out[j].id)
			return a < b
		}
		return out[i].id < out[j].id
	})
	return out, nil
}

// marshal emits the records as a compact JSON array preserving key order, so
// output matches the Python implementation byte-for-byte.
func marshal(records []orderedRecord) ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('[')
	for i, rec := range records {
		if i > 0 {
			buf.WriteByte(',')
		}
		buf.WriteByte('{')
		for j, k := range rec.keys {
			if j > 0 {
				buf.WriteByte(',')
			}
			keyJSON, err := json.Marshal(k)
			if err != nil {
				return nil, err
			}
			buf.Write(keyJSON)
			buf.WriteByte(':')
			valJSON, err := json.Marshal(rec.values[k])
			if err != nil {
				return nil, err
			}
			buf.Write(valJSON)
		}
		buf.WriteByte('}')
	}
	buf.WriteByte(']')
	return buf.Bytes(), nil
}

func run() error {
	raw, err := io.ReadAll(os.Stdin)
	if err != nil {
		return fmt.Errorf("reading stdin: %w", err)
	}
	var payload interface{}
	if err := json.Unmarshal(raw, &payload); err != nil {
		return fmt.Errorf("invalid JSON on stdin: %w", err)
	}
	records, ok := payload.([]interface{})
	if !ok {
		return fmt.Errorf("input must be a JSON array")
	}
	normalized, err := normalize(records)
	if err != nil {
		return err
	}
	encoded, err := marshal(normalized)
	if err != nil {
		return err
	}
	_, err = os.Stdout.Write(encoded)
	return err
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
