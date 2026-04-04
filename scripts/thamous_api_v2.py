#!/usr/bin/env python3
"""Client CLI pour l’API Thamous v2 logique."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import time
from typing import Any, Iterable

import requests

DEFAULT_BASE_URL = "https://thamous.ouvaton.org/thamous/php/api/v2/index.php"
DEFAULT_BW_ITEM_NAME = "Al1 - Thamous API Token"


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_token() -> str:
    tok = os.environ.get("THAMOUS_TOKEN")
    if tok:
        return tok.strip()

    tok_file = os.environ.get("THAMOUS_TOKEN_FILE")
    if tok_file:
        try:
            return _read_text_file(tok_file).strip()
        except Exception:
            pass

    try:
        bw_item_name = os.environ.get("THAMOUS_BW_ITEM", DEFAULT_BW_ITEM_NAME)
        out = subprocess.check_output(["bw", "get", "item", bw_item_name], stderr=subprocess.DEVNULL)
        item = json.loads(out.decode("utf-8"))
        notes = (item.get("notes") or "").strip()
        if notes:
            return notes
        wanted_field = os.environ.get("THAMOUS_BW_FIELD", "token").strip().lower()
        fields = item.get("fields") or []
        if isinstance(fields, list):
            for fld in fields:
                if not isinstance(fld, dict):
                    continue
                name = (fld.get("name") or "").strip().lower()
                if name == wanted_field:
                    val = (fld.get("value") or "").strip()
                    if val:
                        return val
            for fld in fields:
                if not isinstance(fld, dict):
                    continue
                name = (fld.get("name") or "").strip().lower()
                if "token" in name:
                    val = (fld.get("value") or "").strip()
                    if val:
                        return val
    except Exception:
        pass

    raise SystemExit("THAMOUS_TOKEN manquant. Exporte THAMOUS_TOKEN=... ou THAMOUS_TOKEN_FILE=... puis réessaie.")


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    return json.dumps(v, ensure_ascii=False)


def _pick_table_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["id", "nom", "titre", "annee", "type", "langue", "editeur", "count", "role", "url"]
    present = [k for k in preferred if any(k in r and r.get(k) not in (None, "") for r in rows)]
    if present:
        return present[:8]
    keys: set[str] = set()
    for r in rows:
        keys.update(r.keys())
    return sorted(keys)[:8]


def _print_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    cols = _pick_table_columns(rows)
    str_rows = [[_as_str(r.get(c)) for c in cols] for r in rows]
    widths = [len(c) for c in cols]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_line(parts: Iterable[str]) -> str:
        return "  ".join(p.ljust(widths[i]) for i, p in enumerate(parts))

    print(fmt_line(cols))
    print(fmt_line(["-" * w for w in widths]))
    for row in str_rows:
        print(fmt_line(row))


def _request(*, base_url: str, path: str, method: str, auth: bool, timeout_s: int, verbose: bool, raw: bool, response_format: str, params: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    headers: dict[str, str] = {}
    token = ""
    if auth:
        token = get_token()
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Authorization"] = f"Bearer {token}"
        headers["X-Thamous-Token"] = token

    started = time.time()
    try:
        if method == "GET":
            response = requests.get(
                base_url,
                params={"path": path, "format": response_format, **(params or {}), **({"token": token} if auth else {})},
                headers=headers,
                timeout=timeout_s,
            )
        else:
            headers["Content-Type"] = "application/json; charset=utf-8"
            response = requests.post(
                f"{base_url}?path={path}",
                headers=headers,
                data=json.dumps({"format": response_format, **(payload or {}), **({"token": token} if auth else {})}, ensure_ascii=False).encode("utf-8"),
                timeout=timeout_s,
            )
    except requests.RequestException as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        if verbose:
            ts = _dt.datetime.now().isoformat(timespec="seconds")
            print(f"[{ts}] ERROR request failed after {elapsed_ms}ms: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc

    elapsed_ms = int((time.time() - started) * 1000)
    if verbose:
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        print(f"[{ts}] {method} {response.url} -> {response.status_code} ({elapsed_ms}ms)", file=sys.stderr)

    if raw:
        return response.status_code, {"_raw": response.text, "content_type": response.headers.get("content-type")}

    ct = (response.headers.get("content-type") or "").lower()
    if "application/json" in ct or response.text.strip().startswith("{"):
        try:
            return response.status_code, response.json()
        except Exception:
            return response.status_code, {"_raw": response.text}
    return response.status_code, {"_raw": response.text, "content_type": response.headers.get("content-type")}


def _load_json_from_args(payload_file: str | None, payload_json: str | None) -> dict[str, Any]:
    if payload_file:
        with open(payload_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    elif payload_json:
        data = json.loads(payload_json)
    else:
        raise SystemExit("Fournir --payload-file ou --payload-json.")
    if not isinstance(data, dict):
        raise SystemExit("Le payload JSON doit être un objet.")
    return data


def _maybe_set(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None and value != "":
        payload[key] = value


def _base_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    _maybe_set(payload, "q", getattr(args, "q", None))
    _maybe_set(payload, "project", getattr(args, "project", None) or getattr(args, "projet", None))
    _maybe_set(payload, "provider", getattr(args, "provider", None))
    _maybe_set(payload, "model", getattr(args, "model", None))
    if getattr(args, "trace", False):
        payload["trace"] = True
    _maybe_set(payload, "indication", getattr(args, "indication", None))
    _maybe_set(payload, "feedback", getattr(args, "feedback", None))
    _maybe_set(payload, "reformulation_precedente", getattr(args, "reformulation_precedente", None))
    _maybe_set(payload, "limit", getattr(args, "limit", None))
    _maybe_set(payload, "offset", getattr(args, "offset", None))
    _maybe_set(payload, "order1", getattr(args, "order1", None))
    _maybe_set(payload, "order2", getattr(args, "order2", None))
    _maybe_set(payload, "asc_desc1", getattr(args, "asc_desc1", None))
    _maybe_set(payload, "asc_desc2", getattr(args, "asc_desc2", None))
    _maybe_set(payload, "derive_limit", getattr(args, "derive_limit", None))
    return payload


def _emit_output(code: int, data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if fmt == "jsonl":
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            for row in data["results"]:
                print(json.dumps(row, ensure_ascii=False))
            return
        print(json.dumps(data, ensure_ascii=False))
        return
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            if "total" in data:
                print(f"total: {data['total']}")
            _print_table(data["results"])
            return
        if isinstance(data.get("projects"), list):
            _print_table(data["projects"])
            return
        if isinstance(data.get("types_biblio"), list):
            for item in data["types_biblio"]:
                print(item)
            return
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_fiche_url(args: argparse.Namespace) -> None:
    code, data = _request(base_url=args.base_url, path="fiche_url", method="GET", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, params={"id": args.id, "table": args.table, **({"projet": args.projet} if args.projet else {})})
    if args.response_format == "url" and isinstance(data, dict) and data.get("_raw"):
        print(str(data.get("_raw", "")).strip())
        return
    _emit_output(code, data, args.format)


def cmd_open_fiche(args: argparse.Namespace) -> None:
    code, data = _request(base_url=args.base_url, path="fiche_url", method="GET", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=False, response_format="url", params={"id": args.id, "table": args.table, **({"projet": args.projet} if args.projet else {})})
    url = ""
    if isinstance(data, dict):
        if data.get("form_url"):
            url = str(data["form_url"]).strip()
        elif data.get("_raw"):
            url = str(data["_raw"]).strip()
    if not url:
        _emit_output(code, data, args.format)
        return
    if args.print_only:
        print(url)
        return
    subprocess.check_call(["xdg-open", url])
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(url)


def cmd_open_list(args: argparse.Namespace) -> None:
    code, data = _request(base_url=args.base_url, path="ask_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=False, response_format="url", payload=_base_payload_from_args(args))
    url = ""
    if isinstance(data, dict) and data.get("_raw"):
        url = str(data.get("_raw", "")).strip()
    elif isinstance(data, str):
        url = data.strip()
    if not url:
        _emit_output(code, data, args.format)
        return
    if args.print_only:
        print(url)
        return
    subprocess.check_call(["xdg-open", url])
    if args.format == "json":
        print(json.dumps({"url": url}, ensure_ascii=False, indent=2))
    else:
        print(url)


def cmd_save_list(args: argparse.Namespace) -> None:
    payload = _base_payload_from_args(args)
    payload["nom_liste"] = args.nom_liste
    payload["save_mode"] = args.save_mode
    code, data = _request(base_url=args.base_url, path="save_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=False, response_format=args.response_format, payload=payload)
    if args.response_format == "url" and isinstance(data, dict) and data.get("_raw"):
        url = str(data.get("_raw", "")).strip()
        if args.print_only:
            print(url)
            return
        subprocess.check_call(["xdg-open", url])
        if args.format == "json":
            print(json.dumps({"url": url}, ensure_ascii=False, indent=2))
        else:
            print(url)
        return
    _emit_output(code, data, args.format)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("THAMOUS_V2_BASE_URL", DEFAULT_BASE_URL), help="URL de base de l’API v2 (ou THAMOUS_V2_BASE_URL).")
    ap.add_argument("--timeout", type=int, default=45, help="Timeout HTTP en secondes.")
    ap.add_argument("--token-file", default=os.environ.get("THAMOUS_TOKEN_FILE"), help="Chemin d’un fichier contenant le token (ou THAMOUS_TOKEN_FILE).")
    ap.add_argument("--raw", action="store_true", help="Affiche la réponse brute.")
    ap.add_argument("--verbose", action="store_true", help="Logs HTTP sur stderr.")
    ap.add_argument("--response-format", default="json", choices=["json", "url"], help="Format demandé à l’API.")
    ap.add_argument("--format", default="json", choices=["json", "jsonl", "table"], help="Format d’affichage local.")

    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("health")

    sp = sub.add_parser("logic-context")
    sp.add_argument("--projet")

    sp = sub.add_parser("fiche-url")
    sp.add_argument("--id", required=True)
    sp.add_argument("--table", required=True)
    sp.add_argument("--projet")

    sp = sub.add_parser("open-fiche")
    sp.add_argument("--id", required=True)
    sp.add_argument("--table", required=True)
    sp.add_argument("--projet")
    sp.add_argument("--print-only", action="store_true", help="Retourner l'URL sans lancer le navigateur.")

    sp = sub.add_parser("open-list")
    sp.add_argument("--q", required=True)
    sp.add_argument("--project")
    sp.add_argument("--provider")
    sp.add_argument("--model")
    sp.add_argument("--trace", action="store_true")
    sp.add_argument("--indication")
    sp.add_argument("--feedback")
    sp.add_argument("--reformulation-precedente")
    sp.add_argument("--limit", type=int)
    sp.add_argument("--offset", type=int)
    sp.add_argument("--order1")
    sp.add_argument("--order2")
    sp.add_argument("--asc-desc1", dest="asc_desc1")
    sp.add_argument("--asc-desc2", dest="asc_desc2")
    sp.add_argument("--derive-limit", type=int, dest="derive_limit")
    sp.add_argument("--print-only", action="store_true", help="Retourner l'URL sans lancer le navigateur.")

    sp = sub.add_parser("save-list")
    sp.add_argument("--q", required=True)
    sp.add_argument("--nom-liste", required=True)
    sp.add_argument("--save-mode", default="extension", choices=["extension", "comprehension"])
    sp.add_argument("--project")
    sp.add_argument("--provider")
    sp.add_argument("--model")
    sp.add_argument("--trace", action="store_true")
    sp.add_argument("--indication")
    sp.add_argument("--feedback")
    sp.add_argument("--reformulation-precedente")
    sp.add_argument("--limit", type=int)
    sp.add_argument("--offset", type=int)
    sp.add_argument("--order1")
    sp.add_argument("--order2")
    sp.add_argument("--asc-desc1", dest="asc_desc1")
    sp.add_argument("--asc-desc2", dest="asc_desc2")
    sp.add_argument("--derive-limit", type=int, dest="derive_limit")
    sp.add_argument("--print-only", action="store_true", help="Retourner l'URL sans lancer le navigateur quand --response-format=url.")

    for name in ["text-to-structure", "ask-logic"]:
        sp = sub.add_parser(name)
        sp.add_argument("--q", required=True)
        sp.add_argument("--project")
        sp.add_argument("--provider")
        sp.add_argument("--model")
        sp.add_argument("--trace", action="store_true")
        sp.add_argument("--indication")
        sp.add_argument("--feedback")
        sp.add_argument("--reformulation-precedente")
        if name == "ask-logic":
            sp.add_argument("--limit", type=int)
            sp.add_argument("--offset", type=int)
            sp.add_argument("--order1")
            sp.add_argument("--order2")
            sp.add_argument("--asc-desc1", dest="asc_desc1")
            sp.add_argument("--asc-desc2", dest="asc_desc2")
            sp.add_argument("--derive-limit", type=int, dest="derive_limit")

    for name in ["compile-logic", "search-logic", "replay-logic"]:
        sp = sub.add_parser(name)
        sp.add_argument("--payload-file")
        sp.add_argument("--payload-json")

    return ap


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.token_file:
        os.environ["THAMOUS_TOKEN_FILE"] = args.token_file

    if args.action == "health":
        code, data = _request(base_url=args.base_url, path="health", method="GET", auth=False, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format)
    elif args.action == "logic-context":
        params = {}
        if args.projet:
            params["projet"] = args.projet
        code, data = _request(base_url=args.base_url, path="logic_context", method="GET", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, params=params)
    elif args.action == "text-to-structure":
        code, data = _request(base_url=args.base_url, path="text_to_structure", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, payload=_base_payload_from_args(args))
    elif args.action == "ask-logic":
        code, data = _request(base_url=args.base_url, path="ask_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, payload=_base_payload_from_args(args))
    elif args.action == "fiche-url":
        cmd_fiche_url(args)
        return
    elif args.action == "open-fiche":
        cmd_open_fiche(args)
        return
    elif args.action == "open-list":
        cmd_open_list(args)
        return
    elif args.action == "save-list":
        cmd_save_list(args)
        return
    elif args.action == "compile-logic":
        code, data = _request(base_url=args.base_url, path="compile_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, payload=_load_json_from_args(args.payload_file, args.payload_json))
    elif args.action == "search-logic":
        code, data = _request(base_url=args.base_url, path="search_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, payload=_load_json_from_args(args.payload_file, args.payload_json))
    elif args.action == "replay-logic":
        code, data = _request(base_url=args.base_url, path="replay_logic", method="POST", auth=True, timeout_s=args.timeout, verbose=args.verbose, raw=args.raw, response_format=args.response_format, payload=_load_json_from_args(args.payload_file, args.payload_json))
    else:
        raise SystemExit(f"Action inconnue: {args.action}")

    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        _emit_output(code, data, args.format)
        raise SystemExit(1)

    if args.response_format == "url" and isinstance(data, dict) and data.get("_raw"):
        print(str(data.get("_raw", "")).strip())
        return

    _emit_output(code, data, args.format)


if __name__ == "__main__":
    main()
