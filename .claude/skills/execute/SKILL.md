---
name: execute
description: 계획에 따라 구현을 수행하고 진행 상태를 추적한다.
---

## 입력

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `issue_id` | ✅ | 참조할 이슈번호 (예: SKT-42) |

## 목적

- 계획된 단계를 순차적으로 구현
- 진행 상태 실시간 업데이트
- 기존 코드 패턴 및 컨벤션 준수

## 구현 원칙

1. **계획 준수** - 계획에 없는 작업은 수행하지 않음
2. **최소 변경** - 필요한 변경만 수행
3. **문서화** - 코드 내 명확한 주석 (단, 과도하지 않게)
4. **진행 추적** - 각 단계 완료 시 상태 업데이트
5. **Redundancy 차단** - spec / 온톨로지 / 문서 파일에 변경 이력·migration 메모·폐기 잔재를 남기지 않는다. 변경 추적은 Linear issue 가 담당하며, spec 파일은 *현재 상태* 만 보유.

### 5.1 Redundancy 차단 — 금지 패턴

다음은 모두 **spec 파일에 작성 금지**:

- `"이전에는 ~ 였음"`, `"기존 X 컬럼 정리"`, `"~ 대비 변경"` 같은 historical 서술
- 티켓 ID (`SKT-XX`, `(2026-05-04)`) 를 spec 본문·필드 설명·rule 근거에 인용
- 폐기된 테이블·MCP 도구·컬럼 이름을 현재 spec 과 같은 파일에 나란히 노출 (LLM 오호출 유도)
- ADR / migration 문서 포인터 (`"자세한 경위는 ~ 참조"`) — 운영 LLM context 외부에 두지 않으면 redundancy 만 늘어남
- 동일 사실을 `§SSOT 블록 + §1.X + rule 근거 + §참조` 등 여러 위치에 중복 기재 (drift 시한폭탄)

### 5.2 Redundancy 차단 — 적용 규칙

- **단일 출처**: 한 사실은 한 곳 (rule 또는 §1.X) 에만 두고, 다른 위치는 포인터 (`§3 R-XX 참조`) 로만 인용
- **근거 = WHY 만**: rule 의 `**근거**` 라인은 *현재 운영 로직의 이유* 로만 서술. 과거 incident·티켓·"이전 정책" 인용 금지
- **변경 history 위치**: commit 메시지 / PR 본문 / Linear issue. spec 파일 본문 외부.
- **편집 전 sweep**: spec / entity 파일을 수정할 때 `grep -nE "SKT-[0-9]+|폐기|이전|기존 .*컬럼|ADR 참조|대비 변경"` 으로 잔재 확인 → 발견 시 같은 PR 에서 정리

## 실행 흐름

```
단계 시작
    ↓
상태: 🟥 → 🟨 (진행 중)
    ↓
구현 수행
    ↓
상태: 🟨 → 🟩 (완료)
    ↓
진행률 업데이트
    ↓
다음 단계
```

## 상태 업데이트 형식

```markdown
**전체 진행률:** `40%` (2/5 완료)

- [x] 🟩 **단계 1: DB 스키마**
  - [x] 🟩 테이블 생성
  - [x] 🟩 인덱스 추가

- [ ] 🟨 **단계 2: API 엔드포인트**
  - [x] 🟩 라우트 정의
  - [ ] 🟨 컨트롤러 구현 ← 현재

- [ ] 🟥 **단계 3: 프론트엔드**
```

## 서브 에이전트 위임

Orchestrator는 단계별로 적합한 서브 에이전트에 위임:

| 단계 유형 | 담당 에이전트 |
|-----------|---------------|
| 데이터 분석 | data-analyst |
| 수익성 계산 | pnl-owner |
| 시각화 | visualizer |
| 보고서 | reporter |

## 오류 처리

- 실패 시 즉시 중단하고 상태 보고
- 원인 분석 후 plan 수정 또는 사용자 확인 요청
- 이슈에 오류 상황 코멘트 추가

## 브랜치 생성

execute 시작 시 **반드시** 작업 브랜치를 확인하고, 없으면 생성한다.

1. 현재 브랜치가 main인지 확인
2. main이면 → `mcp__linear__get_issue`로 이슈 라벨 확인 후 브랜치 생성:

```bash
git checkout main
git pull origin main
git checkout -b [prefix][issue_id]
# 예: git checkout -b feature/SKT-42
```

| 라벨 | 브랜치 prefix |
|------|--------------|
| `Feature` | `feature/` |
| `Bug` | `bug/` |
| `Improvement` | `improvement/` |
| `Chore` | `chore/` |
| `Hotfix` | `hotfix/` |

3. 이미 작업 브랜치에 있으면 → 그대로 진행

> **라벨이 없는 경우**: 이슈 내용을 분석하여 라벨을 먼저 부여한 후 브랜치를 생성한다.

## 이슈 상태 업데이트

- **시작 시**: `mcp__linear__save_issue`로 이슈 status → `in_progress`
- **완료 시**: `mcp__linear__save_comment`로 코멘트 추가

## 이슈 업데이트

실행 완료 시 이슈에 코멘트 추가:

```markdown
### ✅ Execute 완료 - [timestamp]

**소요 시간**: [duration]

**실행 결과**:
- 완료 단계: [n]/[total]
- 생성된 파일: [n]개
- 수정된 파일: [n]개

**산출물**:
- `path/to/file1`
- `path/to/file2`

**다음 단계**: review

---
이슈: [issue_id]
```

## 완료 후 필수 게이트 (Review Required)

모든 Phase 완료 및 커밋 후 **반드시** 다음 메시지를 출력하고 멈춘다:

```
---
⚠️  구현이 완료됐지만 작업은 아직 끝나지 않았습니다.

커밋: [commit_hash] ([branch])
이슈: [issue_id]

**다음 필수 단계**: `/review [issue_id]`

review 없이 종료하면 코드 품질·정책 준수 검증이 누락됩니다.
진행하시겠습니까? [/review 실행 / 나중에]
---
```

> **[Critical]** execute 스킬은 커밋 후 자동으로 종료하지 않는다.
> 사용자가 명시적으로 `/review`를 실행하거나 "나중에"를 선택할 때까지 대기한다.
> "나중에"를 선택하면 Linear 이슈에 `status=in_progress` 유지 + 다음 단계 안내 코멘트를 남긴다.

### 오류 발생 시

```markdown
### ⚠️ Execute 중단 - [timestamp]

**중단 단계**: [단계명]
**오류 내용**: [오류 설명]
**완료된 단계**: [n]/[total]

**필요 조치**: [plan 수정 / 사용자 확인 / 재시도]

---
이슈: [issue_id]
Status: in_progress → blocked
```

## Orchestrator 활용

```
plan(issue_id) 완료 + 사용자 승인
    ↓
Orchestrator: execute(issue_id) 호출
    ↓
서브 에이전트 위임 실행
    ↓
각 단계 완료 시 진행률 업데이트
    ↓
전체 완료 + 커밋
    ↓
이슈 코멘트 추가
    ↓
⚠️ Review 게이트 출력 (대기) ← 사용자 응답 필요
    ↓
/review [issue_id] 실행 (사용자 명시 실행)
```
