#!/usr/bin/env python3
"""
Confluence 문서 조작 CLI — notion-to-confluence 스킬 전용

기존 confluence-docs 스킬의 confluence_client.py + skills_confluence.py를 통합.
create / read / update / attach / search 명령을 지원합니다.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv

load_dotenv(".env")


# ============================================================
# Confluence Client
# ============================================================

class ConfluenceClient:
    """Confluence REST API 클라이언트"""

    def __init__(self):
        self.url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN", "")
        self.space_key = os.getenv("CONFLUENCE_SPACE_KEY", "")
        self.username = os.getenv("CONFLUENCE_USERNAME", "")

        if not self.url or not self.api_token:
            raise ValueError(
                "CONFLUENCE_URL, CONFLUENCE_API_TOKEN 환경변수가 필요합니다. "
                ".env 파일을 확인하세요."
            )

        self.base_url = f"{self.url}/rest/api"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _request(self, method: str, endpoint: str,
                 params: Optional[Dict] = None,
                 data: Optional[Dict] = None) -> Dict[str, Any]:
        resp = self.session.request(
            method=method,
            url=f"{self.base_url}/{endpoint}",
            params=params,
            json=data,
        )
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text if e.response else str(e)
            print(json.dumps({"status": "error", "message": f"HTTP {e.response.status_code}: {detail}"},
                             ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(1)
        return resp.json() if resp.text else {"status": "success"}

    # --- CRUD ---

    def create_page(self, title: str, body: str,
                    space_key: Optional[str] = None,
                    parent_id: Optional[str] = None) -> Dict:
        space = space_key or self.space_key
        if not space:
            raise ValueError("스페이스 키가 지정되지 않았습니다.")
        payload: Dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        return self._request("POST", "content", data=payload)

    def get_page(self, page_id: Optional[str] = None,
                 title: Optional[str] = None,
                 space_key: Optional[str] = None,
                 expand: Optional[List[str]] = None) -> Dict:
        if page_id:
            params = {"expand": ",".join(expand)} if expand else {}
            return self._request("GET", f"content/{page_id}", params=params)
        if title:
            space = space_key or self.space_key
            params = {"spaceKey": space, "title": title}
            if expand:
                params["expand"] = ",".join(expand)
            result = self._request("GET", "content", params=params)
            if result.get("results"):
                return result["results"][0]
            raise ValueError(f"페이지를 찾을 수 없습니다: {title}")
        raise ValueError("page_id 또는 title이 필요합니다.")

    def update_page(self, page_id: str, title: str, body: str,
                    version: Optional[int] = None) -> Dict:
        if not version:
            cur = self.get_page(page_id=page_id, expand=["version"])
            version = cur["version"]["number"]
            if not title:
                title = cur["title"]
        return self._request("PUT", f"content/{page_id}", data={
            "type": "page",
            "title": title,
            "body": {"storage": {"value": body, "representation": "storage"}},
            "version": {"number": version + 1},
        })

    def add_attachment(self, page_id: str, file_path: str,
                       comment: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/content/{page_id}/child/attachment"
        saved = self.session.headers.pop("Content-Type", None)
        headers = {"X-Atlassian-Token": "nocheck"}
        try:
            with open(file_path, "rb") as f:
                resp = self.session.post(url, headers=headers,
                                         files={"file": f},
                                         data={"comment": comment} if comment else {})
                resp.raise_for_status()
                return resp.json()
        finally:
            if saved:
                self.session.headers["Content-Type"] = saved

    def search(self, cql: str, limit: int = 25) -> Dict:
        return self._request("GET", "content/search",
                             params={"cql": cql, "limit": limit})

    def page_url(self, page_id: str) -> str:
        return f"{self.url}/pages/viewpage.action?pageId={page_id}"


# ============================================================
# CLI Commands
# ============================================================

def cmd_create(args, client: ConfluenceClient):
    body = _read_body(args)
    result = client.create_page(
        title=args.title, body=body,
        space_key=args.space, parent_id=args.parent,
    )
    _print_result("create", result, client)


def cmd_read(args, client: ConfluenceClient):
    expand = ["body.storage", "version", "space"]
    if args.id:
        result = client.get_page(page_id=args.id, expand=expand)
    else:
        result = client.get_page(title=args.title, space_key=args.space, expand=expand)
    out = {
        "page_id": result["id"],
        "title": result["title"],
        "space_key": result.get("space", {}).get("key", ""),
        "version": result["version"]["number"],
        "url": client.page_url(result["id"]),
    }
    if args.content:
        out["content"] = result["body"]["storage"]["value"]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_update(args, client: ConfluenceClient):
    body = _read_body(args)
    if args.id:
        page_id = args.id
        page = client.get_page(page_id=page_id, expand=["version"])
    else:
        page = client.get_page(title=args.title, space_key=args.space, expand=["version"])
        page_id = page["id"]
    title = args.new_title if args.new_title else page["title"]
    result = client.update_page(page_id=page_id, title=title, body=body)
    _print_result("update", result, client)


def cmd_attach(args, client: ConfluenceClient):
    fp = Path(args.file)
    if not fp.exists():
        print(f"오류: 파일 없음: {args.file}", file=sys.stderr)
        sys.exit(1)
    if args.id:
        page_id = args.id
    else:
        page = client.get_page(title=args.title, space_key=args.space, expand=["version"])
        page_id = page["id"]
    result = client.add_attachment(page_id, str(fp), comment=args.comment)
    att = result.get("results", [result])[0] if "results" in result else result
    print(json.dumps({
        "status": "success", "action": "attach",
        "page_id": page_id, "filename": fp.name,
        "attachment_id": att.get("id", ""),
        "url": client.page_url(page_id),
    }, ensure_ascii=False, indent=2))


def cmd_search(args, client: ConfluenceClient):
    parts = []
    if args.query:
        parts.append(f'text ~ "{args.query}"')
    space = args.space or client.space_key
    if space:
        parts.append(f'space = "{space}"')
    parts.append("type = page")
    cql = args.cql if args.cql else " AND ".join(parts)
    result = client.search(cql, limit=args.limit)
    pages = []
    for item in result.get("results", []):
        c = item.get("content", item)
        pages.append({
            "page_id": c.get("id", ""),
            "title": c.get("title", ""),
            "url": client.page_url(c.get("id", "")),
        })
    print(json.dumps({"status": "success", "total": result.get("totalSize", len(pages)),
                       "pages": pages}, ensure_ascii=False, indent=2))


def cmd_env(args, client: ConfluenceClient):
    """현재 Confluence 환경 설정 출력"""
    print(json.dumps({
        "url": client.url,
        "space_key": client.space_key,
        "space_url": f"{client.url}/display/{client.space_key}" if client.space_key else "",
        "username": client.username,
        "token_set": bool(client.api_token),
    }, ensure_ascii=False, indent=2))


# ============================================================
# Helpers
# ============================================================

def _read_body(args) -> str:
    if getattr(args, "file", None):
        fp = Path(args.file)
        if not fp.exists():
            print(f"오류: 파일 없음: {args.file}", file=sys.stderr)
            sys.exit(1)
        return fp.read_text(encoding="utf-8")
    if getattr(args, "body", None):
        return args.body
    print("오류: --body 또는 --file 필요", file=sys.stderr)
    sys.exit(1)


def _print_result(action: str, result: Dict, client: ConfluenceClient):
    print(json.dumps({
        "status": "success",
        "action": action,
        "page_id": result["id"],
        "title": result["title"],
        "version": result.get("version", {}).get("number", 0),
        "url": client.page_url(result["id"]),
    }, ensure_ascii=False, indent=2))


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Confluence 문서 조작 CLI")
    sub = parser.add_subparsers(dest="command")

    # create
    p = sub.add_parser("create")
    p.add_argument("--title", "-t", required=True)
    p.add_argument("--body", "-b")
    p.add_argument("--file", "-f")
    p.add_argument("--space", "-s")
    p.add_argument("--parent", "-p")

    # read
    p = sub.add_parser("read")
    p.add_argument("--id")
    p.add_argument("--title", "-t")
    p.add_argument("--space", "-s")
    p.add_argument("--content", "-c", action="store_true")

    # update
    p = sub.add_parser("update")
    p.add_argument("--id")
    p.add_argument("--title", "-t")
    p.add_argument("--new-title")
    p.add_argument("--body", "-b")
    p.add_argument("--file", "-f")
    p.add_argument("--space", "-s")

    # attach
    p = sub.add_parser("attach")
    p.add_argument("--id")
    p.add_argument("--title", "-t")
    p.add_argument("--space", "-s")
    p.add_argument("--file", "-f", required=True)
    p.add_argument("--comment", "-c")

    # search
    p = sub.add_parser("search")
    p.add_argument("--query", "-q")
    p.add_argument("--cql")
    p.add_argument("--space", "-s")
    p.add_argument("--limit", "-l", type=int, default=25)

    # env
    sub.add_parser("env")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = ConfluenceClient()
    {"create": cmd_create, "read": cmd_read, "update": cmd_update,
     "attach": cmd_attach, "search": cmd_search, "env": cmd_env}[args.command](args, client)


if __name__ == "__main__":
    main()
