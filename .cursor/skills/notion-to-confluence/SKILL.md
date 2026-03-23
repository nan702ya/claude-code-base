---
name: notion-to-confluence
description: Notion 문서를 Confluence로 복사. Notion MCP로 검색·조회하고, 이미지(signed URL)·mermaid 등 변환 불가 블록을 이미지로 변환해 Confluence에 생성. Keywords: notion, confluence, 복사, 마이그레이션, 문서, copy, migrate.
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

1. `.claude/skills/notion-to-confluence/.env` 파일에서 Confluence 설정값을 읽어옵니다:
```bash
python3 -c "
from dotenv import load_dotenv; import os
load_dotenv('.claude/skills/notion-to-confluence/.env')
url = os.getenv('CONFLUENCE_URL', '')
space = os.getenv('CONFLUENCE_SPACE_KEY', '')
user = os.getenv('CONFLUENCE_USERNAME', '')
token = 'SET' if os.getenv('CONFLUENCE_API_TOKEN') else 'NOT SET'
print(f'URL={url}')
print(f'SPACE_KEY={space}')
print(f'USERNAME={user}')
print(f'TOKEN={token}')
"
```

2. 사용자에게 현재 설정을 보여줍니다:
```
## Confluence 연결 설정

| 항목 | 현재값 |
|------|--------|
| URL | {CONFLUENCE_URL} |
| Space | {CONFLUENCE_SPACE_KEY} → {CONFLUENCE_URL}/display/{CONFLUENCE_SPACE_KEY} |
| Username(사번) | {CONFLUENCE_USERNAME} |
| API Token | {'설정됨' or '미설정'} |
```

3. **URL과 Space Key는 기본값을 그대로 사용합니다.** 변경을 원하면 말해달라고 안내합니다.
4. **USERNAME과 TOKEN이 비어있으면 사용자에게 입력을 요청합니다:**
   - "Confluence 사용자명(사번)을 입력해주세요: (예: 1110450)"
   - "Confluence API 토큰을 입력해주세요: (생성: 프로필 > 개인 액세스 토큰)"
   - 입력받은 값을 `.claude/skills/notion-to-confluence/.env` 파일에 저장합니다:
     ```bash
     # 기존 값 업데이트 또는 추가
     python3 -c "
     import re, sys
     from pathlib import Path
     env_path = '.claude/skills/notion-to-confluence/.env'
     Path(env_path).touch()
     with open(env_path, 'r') as f:
         content = f.read()
     for key, val in [('CONFLUENCE_USERNAME', sys.argv[1]), ('CONFLUENCE_API_TOKEN', sys.argv[2])]:
         if re.search(rf'^{key}=', content, re.M):
             content = re.sub(rf'^{key}=.*$', f'{key}={val}', content, flags=re.M)
         else:
             content += f'\n{key}={val}'
     with open(env_path, 'w') as f:
         f.write(content)
     print('saved')
     " "<사번>" "<token>"
     ```

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

2. 부모 페이지 지정 원하면 ID 또는 제목을 입력하도록 안내
3. 부모 페이지가 지정되면 해당 페이지 정보 조회 후 링크 표시:
```bash
python3 .claude/skills/notion-to-confluence/confluence_ops.py read --id <parent_id>
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
python3 .claude/skills/notion-to-confluence/confluence_ops.py create \
  --title "<문서 제목>" \
  --file /tmp/notion_to_confluence_body.html \
  --space <SPACE_KEY> \
  [--parent <parent_id>]
```

### 이미지 첨부
다운로드/변환한 이미지 파일을 모두 첨부합니다:
```bash
python3 .claude/skills/notion-to-confluence/confluence_ops.py attach \
  --id <page_id> --file "/tmp/notion_img_1.png"
python3 .claude/skills/notion-to-confluence/confluence_ops.py attach \
  --id <page_id> --file "/tmp/mermaid_1.png"
# ... 반복
```

### 본문 업데이트 (첨부파일 참조 반영)
첨부 완료 후, 이미지 매크로가 첨부파일명을 정확히 참조하도록 본문을 최종 업데이트합니다:
```bash
python3 .claude/skills/notion-to-confluence/confluence_ops.py update \
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
- `.claude/skills/notion-to-confluence/.env` 파일의 CONFLUENCE_URL, CONFLUENCE_SPACE_KEY는 변경 요청 시에만 수정
