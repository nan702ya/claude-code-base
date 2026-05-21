---
name: close-issue
description: 이슈 완료 처리 — Linear done 전환 + 작업 브랜치를 main에 병합하고 삭제한다.
---

## 입력

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `issue_id` | ✅ | 닫을 이슈번호 (예: SKT-42) |

## 전제 조건

이 스킬을 실행하기 전에 다음이 완료된 상태여야 한다:

- [ ] `review` 또는 `peer-review` 통과 (Critical 이슈 없음)
- [ ] 모든 수정 commit 완료

전제 조건이 충족되지 않은 경우 실행하지 않는다.

## 실행 절차

### 1. 작업 브랜치 탐지

`execute` 스킬이 issue_id 기반으로 브랜치를 생성하므로(`feature/SKT-42`, `bug/SKT-42` 등), 로컬 브랜치에서 issue_id를 포함하는 브랜치를 찾는다.

```bash
git branch | grep [issue_id]
# 예: feature/SKT-42, improvement/SKT-42 등
```

브랜치가 2개 이상 감지되면 사용자에게 선택을 요청한다.
브랜치가 없으면 현재 브랜치가 작업 브랜치인지 확인 후 사용자에게 확인한다.

### 2. Linear 이슈 Done 처리

```
mcp__linear__save_issue(id: issue_id, state: "done")
```

### 3. main 최신화 + 브랜치 병합

```bash
git checkout main
git pull origin main
git merge [branch] --no-ff -m "merge: [branch] → main ([issue_id])"
```

### 4. 원격 push (원격이 있는 경우)

```bash
git push origin main
```

### 5. 작업 브랜치 삭제

```bash
# 로컬 삭제
git branch -d [branch]

# 원격에 push한 적 있으면 원격도 삭제
git push origin --delete [branch]
```

원격 브랜치가 없는 경우 원격 삭제 단계는 생략한다.

## 완료 출력

```
✅ [issue_id] 닫힘
- Linear: Done
- 병합: [branch] → main
- 브랜치 삭제: 로컬 완료 (원격: 있음/없음)
```

## 주의

- 병합 충돌 발생 시 자동 진행하지 않는다. 사용자에게 충돌 내용을 보고하고 해결 후 재실행을 요청한다.
- `--no-ff`로 병합하여 브랜치 이력을 보존한다.
