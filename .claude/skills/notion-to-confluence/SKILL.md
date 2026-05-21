---
name: notion-to-confluence
description: Notion 문서를 Confluence로 복사. Notion MCP로 검색·조회하고, 이미지(signed URL)·mermaid 등 변환 불가 블록을 이미지로 변환해 Confluence에 생성. Keywords: notion, confluence, 복사, 마이그레이션, 문서, copy, migrate.
---

> **[Critical] 모든 Bash 명령은 본 스킬을 호출했을 때 시스템이 알려준 `Base directory for this skill: <SKILL_DIR>` 의 절대경로를 사용합니다. 상대경로(`.claude/skills/...`)는 Claude의 cwd에 따라 실패하므로 사용 금지.**
> `<SKILL_DIR>` 자리에 실제 절대경로(예: `/Users/1110450/.claude/skills/notion-to-confluence`) 그대로 치환해서 실행하세요. `confluence_ops.py`는 자기 폴더의 `.env`를 자동으로 로드하므로 호출자의 cwd와 무관하게 동작합니다.

---

## 0단계: 환경 점검

### Notion MCP 확인

1. `mcp__notion__notion-search` 도구가 사용 가능한지 확인합니다.
2. 사용 불가하면:
   - `.mcp.json`에 아래 설정 추가:
     ```json
     "notion": {
       "type": "http",
       "url": "https://mcp.notion.com/mcp"
     }
     ```
   - `.claude/settings.local.json`의 `enabledMcpjsonServers`에 `"notion"` 추가
   - 사용자에게 **세션 재시작** 필요를 안내하고 중단

### Confluence 환경 확인

1. 스킬 폴더 내 `.env`의 설정값을 한 번에 확인합니다 (스크립트는 자기 옆 `.env`를 자동 로드):
   ```bash
   python3 <SKILL_DIR>/confluence_ops.py env
   ```
   출력 예:
   ```json
   {
     "env_file": "/Users/.../notion-to-confluence/.env",
     "env_file_exists": true,
     "url": "https://confluence.tde.sktelecom.com",
     "space_key": "DIAAS",
     "username": "1110450",
     "token_set": true
   }
   ```

2. **모든 값이 채워져 있고 `token_set: true` 면 그대로 진행합니다 — 사용자에게 묻지 마세요.** 사용자에게는 한 줄 요약만 안내:
   ```
   Confluence: <url> / Space=<space_key> / User=<username> / Token=설정됨 (.env)
   ```

3. **`url`/`space_key`/`username` 중 빈 값이 있거나 `token_set: false` 인 경우에만** 사용자에게 입력 요청:
   - "Confluence 사용자명(사번)을 입력해주세요: (예: 1110450)"
   - "Confluence API 토큰을 입력해주세요: (생성: 프로필 > 개인 액세스 토큰)"
   - 입력받은 값을 스킬 폴더 내 `.env` 파일에 저장 (cwd 무관, 절대경로 사용):
     ```bash
     python3 - <<'PY' "<SKILL_DIR>" "<USERNAME>" "<TOKEN>"
     import re, sys
     from pathlib import Path
     env_path = Path(sys.argv[1]) / ".env"
     env_path.parent.mkdir(parents=True, exist_ok=True)
     env_path.touch()
     content = env_path.read_text(encoding="utf-8")
     for key, val in [("CONFLUENCE_USERNAME", sys.argv[2]),
                      ("CONFLUENCE_API_TOKEN", sys.argv[3])]:
         if re.search(rf'^{key}=', content, re.M):
             content = re.sub(rf'^{key}=.*$', f'{key}={val}', content, flags=re.M)
         else:
             content += f'\n{key}={val}'
     env_path.write_text(content.strip() + "\n", encoding="utf-8")
     print(f"saved → {env_path}")
     PY
     ```
   - URL/SPACE_KEY가 비어있으면 동일한 패턴으로 추가 입력받아 저장.

4. 저장 후 1번 명령을 다시 실행해 모든 값이 채워졌는지 확인하고 진행합니다.

> **묻지 마세요. 이미 .env에 모든 값이 있으면 즉시 진행하세요.** 사용자가 명시적으로 "변경하고 싶다"고 말한 경우에만 재입력을 받습니다.

---

## 1단계: Notion 문서 검색

`$ARGUMENTS`에서 검색할 제목을 추출합니다. 비어있으면 사용자에게 질문합니다.

```
mcp__notion__notion-search(query: "<제목>", filter: {"property": "object", "value": "page"})
```

검색 결과를 사용자에게 보여줍니다:
- 번호, 제목, 마지막 수정일
- 여러 개이면 목록에서 선택
- 없으면 다른 키워드 안내

**사용자 확인:** "이 문서가 맞습니까?" → 확인 후 진행

---

## 2단계: Notion 문서 전체 내용 가져오기

```
mcp__notion__notion-fetch(url: "https://www.notion.so/<page_id_without_hyphens>")
```

- 검색 결과의 `url` 필드 또는 `id`에서 하이픈 제거하여 URL 구성
- 반환된 Markdown 콘텐츠를 파싱

---

## 3단계: Confluence 대상 위치 확인

1. 기본 스페이스와 URL을 보여줍니다:
```
기본 위치: {CONFLUENCE_SPACE_KEY} 스페이스 루트
→ {CONFLUENCE_URL}/display/{CONFLUENCE_SPACE_KEY}
```

2. 부모 페이지 지정 원하면 ID 또는 제목을 입력하도록 안내. 제목만 알고 있으면 검색으로 ID 조회:
   ```bash
   python3 <SKILL_DIR>/confluence_ops.py search --query "<부모 페이지 제목>" --space <SPACE_KEY>
   ```
3. 부모 페이지가 지정되면 해당 페이지 정보 조회 후 링크 표시:
   ```bash
   python3 <SKILL_DIR>/confluence_ops.py read --id <parent_id>
   ```
   ```
   삽입 위치: "{부모 페이지 제목}" 하위
   → {CONFLUENCE_URL}/pages/viewpage.action?pageId={parent_id}
   ```

4. **사용자 확인:** "이 위치에 생성하시겠습니까?" → 확인 후 진행

---

## 4단계: 콘텐츠 변환

### 4-1. 이미지 처리

**[Critical] Notion 이미지는 signed URL(임시)입니다. query string 포함 전체 URL로 다운로드해야 합니다.**

1. 콘텐츠에서 이미지 URL 추출 (Notion S3 signed URL 등)
2. 전체 URL 그대로 다운로드:
   ```bash
   curl -L -o "/tmp/notion_img_{n}.png" "<full_signed_url_including_query_params>"
   ```
3. 본문의 이미지 참조를 Confluence 첨부파일 매크로로 변환:
   ```html
   <ac:image ac:width="680"><ri:attachment ri:filename="notion_img_{n}.png" /></ac:image>
   ```

### 4-2. Mermaid 및 변환 불가 블록

**Mermaid → PNG 변환:**
```bash
npx mmdc --version 2>/dev/null || echo "mermaid-cli 미설치 — npx로 실행"
echo '<mermaid_code>' > /tmp/mermaid_{n}.mmd
npx mmdc -i /tmp/mermaid_{n}.mmd -o /tmp/mermaid_{n}.png -b transparent
```

**블록 매핑 테이블:**

| Notion 블록 | Confluence 변환 |
|-------------|----------------|
| mermaid 코드블록 | `npx mmdc` → PNG 첨부 + `<ac:image>` |
| callout | `<ac:structured-macro ac:name="info"><ac:rich-text-body>...</ac:rich-text-body></ac:structured-macro>` |
| toggle | `<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">제목</ac:parameter><ac:rich-text-body>...</ac:rich-text-body></ac:structured-macro>` |
| table_of_contents | `<ac:structured-macro ac:name="toc" />` |
| bookmark / embed | `<a href="url">제목</a>` 링크로 대체 |
| equation (KaTeX) | LaTeX 매크로 또는 이미지 변환 |
| 코드블록 (일반) | `<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{lang}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>` |

### 4-3. Markdown → Confluence Storage Format

Notion fetch 결과는 Markdown입니다. 아래 순서로 변환합니다:

1. 이미지, mermaid 등 특수 블록을 먼저 추출/변환 (4-1, 4-2)
2. 나머지 Markdown을 Confluence Storage Format HTML로 변환:
   - `# H1` → `<h1>`, `## H2` → `<h2>`, ...
   - `**bold**` → `<strong>`, `*italic*` → `<em>`
   - `- item` → `<ul><li>`, `1. item` → `<ol><li>`
   - `` `code` `` → `<code>`
   - `[text](url)` → `<a href="url">text</a>`
   - 테이블 → `<table><tr><th>/<td>` 구조
   - `> quote` → `<blockquote>`
   - `---` → `<hr />`
3. 변환된 HTML을 `/tmp/notion_to_confluence_body.html`에 저장

---

## 5단계: Confluence 페이지 생성 및 첨부

### 페이지 생성
```bash
python3 <SKILL_DIR>/confluence_ops.py create \
  --title "<문서 제목>" \
  --file /tmp/notion_to_confluence_body.html \
  --space <SPACE_KEY> \
  [--parent <parent_id>]
```

### 이미지 첨부
다운로드/변환한 이미지 파일을 모두 첨부합니다:
```bash
python3 <SKILL_DIR>/confluence_ops.py attach \
  --id <page_id> --file "/tmp/notion_img_1.png"
python3 <SKILL_DIR>/confluence_ops.py attach \
  --id <page_id> --file "/tmp/mermaid_1.png"
# ... 반복
```

### 본문 업데이트 (첨부파일 참조 반영)
첨부 완료 후, 이미지 매크로가 첨부파일명을 정확히 참조하도록 본문을 최종 업데이트합니다:
```bash
python3 <SKILL_DIR>/confluence_ops.py update \
  --id <page_id> \
  --file /tmp/notion_to_confluence_body.html
```

---

## 6단계: 정리 및 결과 보고

임시 파일 정리:
```bash
rm -f /tmp/notion_img_* /tmp/mermaid_* /tmp/notion_to_confluence_body.html
```

결과 보고:
```
## Notion → Confluence 복사 완료

| 항목 | 내용 |
|------|------|
| 원본 (Notion) | [문서 제목](notion_url) |
| 사본 (Confluence) | [문서 제목](confluence_url) |
| 첨부 이미지 | N개 |
| 변환 블록 | mermaid N개, callout N개 등 |
| 주의 | [수동 확인 필요 항목] |
```

---

## 주의사항

- Notion 이미지 signed URL은 **1시간 후 만료** — fetch 직후 즉시 다운로드
- Confluence 동일 스페이스 내 페이지 제목 고유 — 중복 시 다른 제목 제안
- 대용량 문서: `notion-fetch` 결과가 잘리면 추가 요청
- `.env`의 `CONFLUENCE_URL`, `CONFLUENCE_SPACE_KEY`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`은 변경 요청이 명시적으로 들어왔을 때만 수정. 그 외에는 기존 값을 그대로 사용하고 사용자에게 묻지 않음.
- `confluence_ops.py`는 `__file__` 위치 기준으로 자기 옆 `.env`를 로드하므로, 어떤 cwd에서 호출해도 동일하게 동작합니다.
