# Review Skill

구현 완료 후 코드/결과물 검토를 수행한다.

## 입력

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `issue_id` | ✅ | 참조할 이슈번호 (예: SKT-42) |

## 목적

- 품질 기준 충족 여부 확인
- 잠재적 문제 사전 발견
- 개선 사항 도출

## 검토 항목

### 코드 품질
- [ ] 로깅: console.log 대신 적절한 로거 사용
- [ ] 에러 처리: try-catch, 의미 있는 에러 메시지
- [ ] 타입: any 타입 지양, 적절한 인터페이스
- [ ] 프로덕션 준비: 디버그 코드, TODO, 하드코딩 제거

### 아키텍처
- [ ] 기존 패턴 준수
- [ ] 적절한 디렉토리 배치
- [ ] 의존성 방향 올바름

### 보안
- [ ] 인증/인가 확인
- [ ] 입력값 검증
- [ ] 민감 정보 노출 없음

### 성능
- [ ] 불필요한 연산 없음
- [ ] 적절한 캐싱/메모이제이션

## 출력 형식

```markdown
## 검토 결과

### ✅ 양호
- [항목 1]
- [항목 2]

### ⚠️ 발견된 이슈
- **[심각도]** [파일:라인] - [이슈 설명]
  - 수정 방안: [제안]

### 📊 요약
- 검토 파일: X개
- Critical: X개
- Warning: X개
- 통과 여부: ✅/❌
```

## 심각도 기준

| 레벨 | 설명 |
|------|------|
| **CRITICAL** | 보안, 데이터 손실, 크래시 |
| **HIGH** | 버그, 성능 문제, UX 저하 |
| **MEDIUM** | 코드 품질, 유지보수성 |
| **LOW** | 스타일, 사소한 개선 |

## 이슈 상태 업데이트

- **시작 시**: `mcp__linear__save_issue`로 이슈 status → `in_progress`
- **완료 시**: `mcp__linear__save_comment`로 코멘트 추가
- **Small 사이클 마지막 단계인 경우**: 코멘트 추가 후 `mcp__linear__save_issue`로 status → `done`, 이후 **브랜치 병합 및 정리** 수행

## 이슈 업데이트

검토 완료 시 이슈에 코멘트 추가:

```markdown
### ✅ Review 완료 - [timestamp]

**소요 시간**: [duration]

**검토 결과**:
- 검토 파일: [n]개
- Critical: [n]개
- Warning: [n]개
- 통과 여부: ✅/❌

**발견된 이슈** (있으면):
- [심각도] [위치] - [설명]

**다음 단계**: peer-review / execute (수정 필요 시)

---
이슈: [issue_id]
```

## Orchestrator 활용

```
execute(issue_id) 완료
    ↓
Orchestrator: review(issue_id) 호출
    ↓
검토 수행
    ↓
이슈 코멘트 추가 (검토 결과)
    ↓
이슈 있으면 → execute(issue_id)로 복귀
이슈 없으면 → peer-review(issue_id)로 이동
```

## 브랜치 병합 및 정리 (사이클 완료 시)

Small 사이클의 마지막 단계(review)에서 모든 검토가 통과되면, 작업 브랜치를 main에 병합하고 삭제한다.

```bash
# 1. main 최신화
git checkout main
git pull origin main

# 2. 작업 브랜치 병합
git merge [작업브랜치]  # 예: feature/SKT-42

# 3. 원격 push
git push origin main

# 4. 작업 브랜치 삭제 (로컬 + 원격)
git branch -d [작업브랜치]
git push origin --delete [작업브랜치]  # 원격에 push한 경우
```

> **주의**: review에서 이슈가 발견되어 execute로 복귀하는 경우에는 병합하지 않는다.
> 병합은 **모든 검토 통과 + 이슈 done 처리 후**에만 수행한다.
