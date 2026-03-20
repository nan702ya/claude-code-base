# Execute Skill

계획에 따라 구현을 수행하고 진행 상태를 추적한다.

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
전체 완료 시 이슈 코멘트 추가
    ↓
review(issue_id)로 이동
```
