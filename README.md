# claude-code-base

Claude Code + Cursor로 제품을 빌드하기 위한 설정 및 커맨드 베이스입니다.

## 구조

```
.claude/
  CLAUDE.md                      # CTO 역할 정의 및 워크플로우 규칙
  setting.json                   # 권한, 언어, 플러그인 설정
  claude-dashboard.local.json    # claude-dashboard 플러그인 설정
  commands/                      # 슬래시 커맨드 (Skills)
    create-issue.md              # Linear 이슈 생성
    create-plan.md               # 실행 계획 수립
    document.md                  # 문서화
    execute.md                   # 계획 실행
    explore.md                   # 코드베이스 탐색
    handoff.md                   # 핸드오프 문서 작성
    learning-opportunity.md      # 학습 기회 식별
    peer-review.md               # 피어 리뷰
    review.md                    # 코드 리뷰
install.sh                       # 설치 스크립트
```

## 설치

```bash
git clone https://github.com/nan702ya/claude-code-base.git
cd claude-code-base
./install.sh
```

설치 스크립트가 수행하는 작업:

| 소스 | 대상 |
|---|---|
| `claude-dashboard.local.json` | `~/.claude/` |
| `setting.json` | `~/.claude/` |
| `commands/*.md` | `~/.claude/commands/` |
| `CLAUDE.md` | `../.claude/` (부모 디렉토리) |

## 주요 설정

- **언어**: 한국어
- **허용 도구**: Read, WebSearch, WebFetch, Fetch, Bash, Skill
- **차단 명령**: `rm -rf`, `sudo`, `chmod 777`, `wget | bash`
- **플러그인**: claude-dashboard
- **팀메이트 모드**: tmux
