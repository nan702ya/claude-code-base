# Create Issue Skill

**모든 작업 사이클의 첫 단계**. 작업 시작 시 이슈를 생성하고, 이후 단계에서 이슈를 참조/업데이트한다.

## 목적

- 작업 시작 시점에 이슈 생성 → 전체 작업 추적
- 이슈번호를 후속 단계에 전달 → 실시간 진행 기록
- 작업 완료/중단 시 최종 상태 업데이트

## 핵심 원칙

> **모든 작업은 이슈로 시작하고 이슈로 끝난다**
> - 작업 시작 → 이슈 생성 (status: `in_progress`)
> - 각 단계 완료 → 이슈 코멘트 추가
> - 작업 완료 → 이슈 상태 업데이트 (status: `done`)

## 수행 흐름

```
사용자 요청
    │
    ▼
┌─────────────────────────────────┐
│  1. 작업 크기 판단              │
│  2. 이슈 생성 (Linear)          │
│  3. 이슈번호 반환 (예: SKT-42)  │
└─────────────────────────────────┘
    │
    ▼
이슈번호를 후속 단계에 전달
    │
    ▼
explore(SKT-42) → plan(SKT-42) → execute(SKT-42) → ...
```

## 이슈 생성 템플릿

```markdown
## 제목
[크기] [카테고리] [작업 요약]

예: [Medium] [Data] OTT 이탈 위험 세그먼트 분석

## 본문

### 작업 정보
- **크기**: [Small/Medium/Large]
- **사이클**: [예정된 단계들]
- **담당 에이전트**: [orchestrator → 서브에이전트들]
- **시작 시간**: [timestamp]

### 요청 내용
[사용자 요청 요약]

### 예상 산출물
- [ ] [산출물 1]
- [ ] [산출물 2]

### 진행 로그
> 각 단계 완료 시 자동 업데이트

---
*이 이슈는 워크플로 시작 시 자동 생성되었습니다.*
```

## 팀 선택 기준

| 조건 | 팀 |
|------|-----|
| SK텔레콤 agent 기능 개발 (skt-agents, offline-crm 등) | `Skt-ai-adoption` |
| 그 외 개인 토이 프로젝트 | `Razalea` |

## 이슈 속성

| 속성 | 값 |
|------|-----|
| **Status** | `in_progress` (시작 시) |
| **Priority** | 작업 긴급도에 따라 |
| **Labels** | 카테고리별 라벨 (아래 참조) |
| **Assignee** | orchestrator 또는 담당 에이전트 |

## 카테고리별 라벨

| 카테고리 | 라벨 | 담당 에이전트 |
|----------|------|---------------|
| 데이터 분석 | `data-analysis` | data-analyst |
| 규제/법률 | `compliance` | government-liaison |
| 요금제 설계 | `plan-design` | plan-designer |
| 손익 분석 | `pnl` | pnl-owner |
| 단말 조달 | `device` | device-procurement |
| 보조금 정책 | `subsidy` | market-ops |
| 시각화 | `visualization` | visualizer |
| 보고서 | `report` | reporter |

## 작업 크기별 사이클

| 크기 | 기준 | 사이클 |
|------|------|--------|
| **Small** | 1-2개 파일, 30분 이내, 기존 패턴 내 | create-issue → execute → review |
| **Medium** | 3-5개 파일, 반나절, 일부 설계 필요 | create-issue → explore → plan → execute → review → peer-review |
| **Large** | 5개+ 파일, 1일+, 신규 설계 필요 | create-issue → explore → plan → execute → review → peer-review → document |

### Small Cycle

```yaml
workflow_context:
  issue_id: "SKT-42"
  size: "Small"
  cycle: ["create-issue", "execute", "review"]
  current_step: "execute"
```

### Medium Cycle

```yaml
workflow_context:
  issue_id: "SKT-42"
  size: "Medium"
  cycle: ["create-issue", "explore", "execute", "review", "document"]
  current_step: "explore"
```

### Large Cycle

```yaml
workflow_context:
  issue_id: "SKT-42"
  size: "Large"
  cycle: ["create-issue", "explore", "plan", "execute", "review", "peer-review", "document"]
  current_step: "explore"
```

## 이슈 업데이트 (각 단계에서)

각 단계 완료 시 이슈에 코멘트 추가:

```markdown
### ✅ [단계명] 완료 - [timestamp]

**소요 시간**: [duration]
**결과 요약**: [1-2줄]
**산출물**: [있으면]

다음 단계: [다음 단계명]
```

## 이슈 최종 업데이트 (작업 완료 시)

```markdown
### 🎉 작업 완료 - [timestamp]

**총 소요 시간**: [duration]
**수행 단계**: [실제 수행된 단계들 나열]
**최종 산출물**:
- `path/to/file1`
- `path/to/file2`

**스킵된 단계**: [있으면 + 사유]

---
Status: `in_progress` → `done`
```

## MCP 연동

```yaml
mcpServers:
  linear: {}  # Linear MCP 서버 필요
```

## Orchestrator 활용

```
사용자 요청 수신
    │
    ▼
Orchestrator: create-issue skill 호출
    │
    ▼
이슈 생성 → 이슈번호 획득 (SKT-42)
    │
    ▼
workflow_context에 이슈번호 저장
    │
    ▼
후속 단계 호출 시 이슈번호 전달
    │
    ├─ explore(issue_id: "SKT-42")
    ├─ plan(issue_id: "SKT-42")
    ├─ execute(issue_id: "SKT-42")
    └─ ...
```

## 작업 중단/실패 시

```markdown
### ⚠️ 작업 중단 - [timestamp]

**중단 단계**: [단계명]
**사유**: [중단 사유]
**완료된 단계**: [완료 단계들]
**재개 방법**: [있으면]

---
Status: `in_progress` → `blocked` 또는 `cancelled`
```
