# Document Skill

변경사항 문서화 및 Context 전달 문서 작성을 수행한다.

## 입력

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `issue_id` | ✅ | 참조할 이슈번호 (예: SKT-42) |

## 목적

- 변경사항 기록 (CHANGELOG)
- Context 전달 문서 작성/업데이트 (HANDOFF.md)
- 관련 문서 최신화

## 문서화 원칙

1. **코드 검증** - 기존 문서를 신뢰하지 않고 실제 코드 확인
2. **간결함** - 문법보다 명확성 우선
3. **실용성** - 이론보다 예시
4. **정확성** - 가정 없이 검증된 내용만

## 수행 단계

### 1. 변경사항 파악
- git diff 또는 최근 커밋 확인
- 변경된 기능/모듈 식별
- 신규/삭제/변경 파일 목록

### 2. 문서 업데이트

**CHANGELOG.md**
```markdown
## [Unreleased]

### Added
- [신규 기능]

### Changed
- [변경 사항]

### Fixed
- [버그 수정]
```

**HANDOFF.md** (Context 전달)
```markdown
# Handoff: [프로젝트명]

**Last Updated**: [날짜]

## Goal
[목표 1-2문장]

## Current Progress
[완료된 작업]

## What Worked
[성공한 접근법]

## What Didn't Work
[실패한 접근법 - 반복 방지용]

## Next Steps
[다음 작업 목록]

## Key Files
[주요 파일 경로]
```

### 3. 검증
- 문서와 실제 코드 일치 확인
- 불확실한 내용은 사용자에게 질문

## 이슈 상태 업데이트

- **시작 시**: `mcp__linear__save_issue`로 이슈 status → `in_progress`
- **완료 시**: `mcp__linear__save_comment`로 코멘트 추가 후 `mcp__linear__save_issue`로 status → `done`

## 이슈 업데이트

문서화 완료 시 이슈에 코멘트 추가:

```markdown
### ✅ Document 완료 - [timestamp]

**소요 시간**: [duration]

**업데이트된 문서**:
- CHANGELOG.md: [추가된 항목 수]
- HANDOFF.md: [업데이트 여부]
- 기타: [있으면]

**다음 단계**: 워크플로 완료

---
이슈: [issue_id]
```

## 이슈 최종 완료 처리

document가 Large 사이클의 마지막 단계인 경우:

```markdown
### 🎉 워크플로 완료 - [timestamp]

**총 소요 시간**: [duration]
**수행 사이클**: create-issue → explore → plan → execute → review → peer-review → document

**최종 산출물**:
- `path/to/file1`
- `path/to/file2`

**문서 업데이트**:
- CHANGELOG.md
- HANDOFF.md

---
이슈: [issue_id]
Status: in_progress → done
```

## Orchestrator 활용

```
peer-review(issue_id) 완료
    ↓
Orchestrator: document(issue_id) 호출
    ↓
CHANGELOG, HANDOFF 업데이트
    ↓
이슈 코멘트 추가 (문서화 결과)
    ↓
이슈 status → done (워크플로 완료)
```
