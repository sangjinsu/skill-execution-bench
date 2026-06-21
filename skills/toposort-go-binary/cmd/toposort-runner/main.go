// Command toposort-runner topologically sorts dependency records.
//
// It reads a JSON array from stdin and writes a JSON array of ids in
// topological order to stdout. When several nodes are ready at once, the
// smallest numeric id is emitted first (deterministic, matching the Python
// reference). It exits non-zero on invalid input or a cycle. Standard library
// only; no network access.
package main

import (
	"container/heap"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

type record struct {
	ID   interface{}   `json:"id"`
	Deps []interface{} `json:"deps"`
}

// intHeap is a min-heap of node ids ordered by their numeric value.
type intHeap [][2]interface{} // each entry: {numericKey int, id string}

func (h intHeap) Len() int            { return len(h) }
func (h intHeap) Less(i, j int) bool  { return h[i][0].(int) < h[j][0].(int) }
func (h intHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *intHeap) Push(x interface{}) { *h = append(*h, x.([2]interface{})) }
func (h *intHeap) Pop() interface{} {
	old := *h
	n := len(old)
	item := old[n-1]
	*h = old[:n-1]
	return item
}

func asString(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case float64:
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

func toposort(records []record) ([]string, error) {
	var ids []string
	depsOf := map[string][]string{}
	for _, r := range records {
		if r.ID == nil {
			return nil, fmt.Errorf("each record must have an 'id'")
		}
		node := strings.TrimSpace(asString(r.ID))
		if _, dup := depsOf[node]; dup {
			return nil, fmt.Errorf("duplicate id: %s", node)
		}
		deps := make([]string, 0, len(r.Deps))
		for _, d := range r.Deps {
			deps = append(deps, strings.TrimSpace(asString(d)))
		}
		ids = append(ids, node)
		depsOf[node] = deps
	}

	nodeSet := map[string]bool{}
	for _, n := range ids {
		nodeSet[n] = true
	}
	indegree := map[string]int{}
	dependents := map[string][]string{}
	for _, n := range ids {
		indegree[n] = indegree[n] + 0
	}
	for _, node := range ids {
		for _, dep := range depsOf[node] {
			if !nodeSet[dep] {
				return nil, fmt.Errorf("unknown dependency '%s' for node '%s'", dep, node)
			}
			indegree[node]++
			dependents[dep] = append(dependents[dep], node)
		}
	}

	key := func(node string) (int, error) {
		return strconv.Atoi(node)
	}

	h := &intHeap{}
	heap.Init(h)
	for _, n := range ids {
		if indegree[n] == 0 {
			k, err := key(n)
			if err != nil {
				return nil, fmt.Errorf("non-integer id '%s'", n)
			}
			heap.Push(h, [2]interface{}{k, n})
		}
	}

	order := make([]string, 0, len(ids))
	for h.Len() > 0 {
		item := heap.Pop(h).([2]interface{})
		node := item[1].(string)
		order = append(order, node)
		for _, child := range dependents[node] {
			indegree[child]--
			if indegree[child] == 0 {
				k, err := key(child)
				if err != nil {
					return nil, fmt.Errorf("non-integer id '%s'", child)
				}
				heap.Push(h, [2]interface{}{k, child})
			}
		}
	}

	if len(order) != len(ids) {
		return nil, fmt.Errorf("input graph has a cycle")
	}
	return order, nil
}

func run() error {
	raw, err := io.ReadAll(os.Stdin)
	if err != nil {
		return fmt.Errorf("reading stdin: %w", err)
	}
	var records []record
	if err := json.Unmarshal(raw, &records); err != nil {
		return fmt.Errorf("invalid JSON on stdin: %w", err)
	}
	order, err := toposort(records)
	if err != nil {
		return err
	}
	encoded, err := json.Marshal(order)
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
