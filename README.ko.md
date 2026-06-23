# skill-execution-bench (한국어)

LLM 코딩 에이전트가 Skill을 사용할 때, **실행 로직을 어떤 형태로 포장하느냐**에 따라
신뢰성과 효율이 어떻게 달라지는지 비교하는 로컬 우선(local-first) 벤치마크입니다.

작업(task)은 고정하고(작업 레코드 정규화), 포장 방식만 4가지로 바꿉니다.

| 모드 | 로직 위치 | 실행 방식 |
|------|-----------|-----------|
| `doc-only` | 자연어 지침만 | 에이전트가 손으로 추론·수행 |
| `inline-code` | `SKILL.md` 안의 코드 블록 | 내장 코드를 복사·실행 |
| `python-script` | 별도 `transform.py` | 스크립트 실행(stdin/stdout) |
| `go-binary` | 컴파일된 Go 바이너리 | 바이너리 실행(stdin/stdout) |

이 프로젝트가 답하려는 질문:

> LLM 에이전트가 Skill을 사용할 때, 문서만 / 인라인 코드 / Python 스크립트 /
> 컴파일된 Go 바이너리 중 무엇이 가장 신뢰성 있고 효율적인가?

전체 명세는 [`AGENTS.md`](./AGENTS.md), 실험 결과는 [`REPORT.ko.md`](./REPORT.ko.md)
(영문 [`REPORT.md`](./REPORT.md))를 참고하세요.

## 작업: 작업 레코드 정규화

각 러너는 JSON 배열(케이싱·공백·status 라벨이 제각각인 레코드)을 받아 정규화합니다.
계약(contract):

1. 모든 문자열 값 trim.
2. `id` → trim된 문자열.
3. `status` → trim·소문자화 후 매핑:
   - `todo, to do, pending` → `todo`
   - `doing, in progress, wip` → `doing`
   - `done, complete, completed` → `done`
   - 매핑에 없으면 소문자·trim 형태 유지.
4. 그 외 필드 → trim.
5. 없는 선택 필드는 추가하지 않음.
6. 객체 키 순서: `id`, `title`, `status`, 그다음 나머지 키 알파벳순.
7. 배열은 `id` 기준 정렬(모두 정수면 수치 정렬, 아니면 사전식).

4개 모드 모두 이 동일한 계약을 구현하므로 바이트 단위로 같은 compact JSON을 만듭니다.

## 디렉터리 구조

```
skills/        doc-only | inline-code | python-script | go-binary  (각각 SKILL.md)
datasets/      tasks.jsonl   (결정적 케이스 5개)
harness/       러너, 평가기, 벤치 드라이버, 참조 정규화기, 에이전트 채점기
outputs/       traces/       (JSONL 벤치마크 트레이스)
tests/         단위 테스트 (pytest)
```

## 명령어

```bash
make setup       # pytest 설치(best effort)
make build-go    # skills/go-binary/bin/skill-runner 빌드
make test        # 단위 테스트 실행(Go 미설치 시 go 테스트는 skip)
make bench       # 4개 모드를 전 케이스에 대해 기계적으로 실행(트레이스 기록)
make clean       # Go 바이너리와 생성된 트레이스 제거
```

### 빠른 스모크 테스트

```bash
echo '[{"id":" 2 ","title":" Fix Login ","status":"In Progress"}]' \
  | python3 skills/python-script/scripts/transform.py
# -> [{"id":"2","title":"Fix Login","status":"doing"}]
```

## 실제 LLM 에이전트 벤치마크

`make bench`(기계적 시뮬레이션, 항상 통과)와 달리, 실제 서브에이전트가 각 SKILL.md만
보고 작업을 수행하게 한 뒤 그 출력을 채점합니다.

```bash
# 모드/trial별로 서브에이전트를 디스패치해 outputs/agent_runs[_haiku]/ 에 저장한 뒤:
python -m harness.agent_eval --runs-dir outputs/agent_runs            # Opus
python -m harness.agent_eval --runs-dir outputs/agent_runs_haiku \    # Haiku
  --trace outputs/traces/agent-bench-haiku.jsonl
```

채점기는 모드별 **정확성(신뢰성)** 과 함께 **속도·토큰·도구 호출 수**를 출력합니다.

## 주요 결과 (요약, 10-trial)

2개 동작 × 2모델 × 4모드 × **10 trial** × 6케이스 = **160 디스패치 / 960 케이스** 채점 결과.

**코드 3모드(inline·python·go)는 4개 셀 전부, 모든 trial에서 100% — 960/960. 무너지는 것은
언제나 doc-only뿐입니다.**

| 동작 | 모델 | doc-only | inline / python / go |
|------|------|:--------:|:--------------------:|
| 정규화-하드 | Haiku | **71.7%** | 100% |
| 정규화-하드 | Opus | **100%** | 100% |
| 위상정렬 | Haiku | **95.0%** | 100% |
| 위상정렬 | Opus | **88.3%** | 100% |

**두 직교 변별 축이 드러납니다:**

- **입력 난이도** 함정(정규화-하드)은 *약한 모델만* 무너뜨립니다 — Haiku 71.7% vs Opus 100%.
  실패는 hard-006(빈 title·중복 id·내부 이중공백) **0/10**, hard-004(optional trim) **3/10**에 집중.
- **동작 깊이** 함정(위상정렬)은 *강한 모델조차* 무너뜨립니다 — Opus doc-only **88.3%**, 12노드
  그래프(topo-005)에서 **50%(5/10)**까지 추락. 모델 강도로도 못 구합니다.

즉 변별의 가장 강력한 축은 입력 난이도가 아니라 **동작의 알고리즘적 깊이**입니다. 동작이 단순
매핑/정렬을 넘어 다단계 알고리즘에 이르면 스크립트·바이너리 포장은 선택이 아니라 필수입니다.

**효율 (10-trial 평균):** `doc-only`가 항상 도구 호출 최소(1회)로 가장 경제적 — 단, 정확성이
보장될 때만. **공정 비교(바이너리 사전 빌드, 빌드 측정 제외)에서 go-binary가 코드 모드 중 가장
빠릅니다** — 위상 Opus에서 go 27s(도구 2회) vs python 39s(도구 4회), 위상 Haiku에서 go 31s로 최速.
`python-script`는 케이스마다 stdin 왕복으로 도구 6~10회로 가장 무겁습니다.

자세한 표·해석은 [`REPORT.ko.md`](./REPORT.ko.md)에 있습니다.

## 요구 사항

- Python 3.11+
- Go 1.22+ (go-binary 모드용)
- GNU Make

Docker·데이터베이스·네트워크 접근 없음.
