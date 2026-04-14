#!/usr/bin/env python3
"""Client CLI pour l’API Thamous v2 logique."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import webbrowser
from typing import Any, Iterable

import requests

DEFAULT_BASE_URL = "https://thamous.ouvaton.org/thamous/php/api/v2/index.php"
DEFAULT_BW_ITEM_NAME = "Al1 - Thamous API Token"
DEFAULT_TOKEN_FILE = os.path.expanduser("~/.config/thamous/token")
DEFAULT_HISTORY_FILE = os.path.expanduser("~/.config/thamous/history_v2.jsonl")


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _ensure_parent_dir(path: str) -> None:
    pathlib.Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _history_file_from_args(args: argparse.Namespace | None = None) -> str:
    if args is not None:
        candidate = getattr(args, "history_file", None)
        if candidate:
            return os.path.expanduser(candidate)
    return os.path.expanduser(os.environ.get("THAMOUS_HISTORY_FILE", DEFAULT_HISTORY_FILE))


def _safe_slug(text: str, max_len: int = 48) -> str:
    txt = (text or "").strip().lower()
    txt = re.sub(r"[^\w\s-]", " ", txt, flags=re.UNICODE)
    txt = re.sub(r"[\s_]+", "_", txt, flags=re.UNICODE).strip("_")
    txt = re.sub(r"_+", "_", txt)
    if not txt:
        txt = "resultat"
    return txt[:max_len].strip("_") or "resultat"


def _result_table_from_response(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    compiled = data.get("compiled")
    if isinstance(compiled, dict):
        table = str(compiled.get("table") or "").strip()
        if table:
            return table
    structure = data.get("structure_response")
    if isinstance(structure, dict):
        node = structure.get("structure")
        if isinstance(node, dict):
            table = str(node.get("table") or "").strip()
            if table:
                return table
    return ""


def _result_ids_from_response(data: Any) -> list[int]:
    if not isinstance(data, dict):
        return []
    results = data.get("results")
    if not isinstance(results, list):
        return []
    ids: list[int] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        value = row.get("id")
        try:
            if value is not None and str(value).strip() != "":
                ids.append(int(value))
        except Exception:
            continue
    return ids


def _history_read(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    entries: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                entries.append(obj)
    return entries


def _history_write_entry(path: str, entry: dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _history_make_name(query: str, table: str, existing: list[dict[str, Any]]) -> str:
    prefix = _safe_slug(query)
    if table:
        prefix = f"{prefix}_{table}"
    existing_names = {str(e.get("name") or "") for e in existing}
    if prefix not in existing_names:
        return prefix
    i = 2
    while f"{prefix}_{i}" in existing_names:
        i += 1
    return f"{prefix}_{i}"


def _history_entry_table(entry: dict[str, Any]) -> str:
    table = str(entry.get("table") or entry.get("type") or "").strip()
    if table in {"tbiblio", "tpersonnes", "tinstitutions", "trevues", "tgraphes", "tliens"}:
        return table
    return ""


def _history_entry_ids(entry: dict[str, Any]) -> list[int]:
    raw = entry.get("ids")
    if not isinstance(raw, list):
        raw = entry.get("value")
    if not isinstance(raw, list):
        return []
    ids: list[int] = []
    for value in raw:
        try:
            ivalue = int(value)
        except Exception:
            continue
        if ivalue > 0:
            ids.append(ivalue)
    return ids


def _history_is_table_entry(entry: dict[str, Any]) -> bool:
    return _history_entry_table(entry) != "" and bool(_history_entry_ids(entry))


def _history_store_named_result(
    args: argparse.Namespace,
    *,
    name: str,
    query: str | None,
    table: str,
    ids: list[int],
    response_path: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    history_file = _history_file_from_args(args)
    entry = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "name": name,
        "query": query,
        "project": getattr(args, "project", None),
        "provider": getattr(args, "provider", None),
        "model": getattr(args, "model", None),
        "type": table,
        "value": ids,
        "table": table,
        "ids": ids,
        "total": len(ids),
        "response_path": response_path,
    }
    if meta:
        entry["meta"] = meta
    _history_write_entry(history_file, entry)
    print(f"[result_name] {name}", file=sys.stderr)
    return entry


def _history_store_api_result(args: argparse.Namespace, data: Any) -> None:
    if not isinstance(data, dict):
        return
    if isinstance(data.get("error"), dict):
        return
    if str(data.get("mode") or "").strip() == "clarify":
        return

    table = _result_table_from_response(data)
    ids = _result_ids_from_response(data)
    if table == "" or not ids:
        return

    history_file = _history_file_from_args(args)
    existing = _history_read(history_file)
    requested_name = getattr(args, "result_name", None)
    name = (requested_name or "").strip() or _history_make_name(getattr(args, "q", "") or "résultat", table, existing)
    _history_store_named_result(
        args,
        name=name,
        query=getattr(args, "q", None),
        table=table,
        ids=ids,
        response_path="ask_logic",
    )


def _history_select(entries: list[dict[str, Any]], *, name: str | None = None, previous: bool = False) -> dict[str, Any] | None:
    if not entries:
        return None
    if name:
        wanted = name.strip()
        for entry in reversed(entries):
            if str(entry.get("name") or "") == wanted:
                return entry
        return None
    if previous:
        return entries[-1]
    return None


def _history_select_base_entry(args: argparse.Namespace, *, expected_table: str | None = None) -> dict[str, Any]:
    entries = _history_read(_history_file_from_args(args))
    base_name = str(getattr(args, "base_name", "") or "").strip() or None
    use_previous = bool(getattr(args, "previous", False))
    if base_name:
        for entry in reversed(entries):
            if str(entry.get("name") or "") != base_name:
                continue
            if not _history_is_table_entry(entry):
                continue
            if expected_table and _history_entry_table(entry) != expected_table:
                continue
            return entry
        raise SystemExit("Aucun résultat compatible trouvé pour ce nom dans l’historique.")

    for entry in reversed(entries):
        if not _history_is_table_entry(entry):
            continue
        if expected_table and _history_entry_table(entry) != expected_table:
            continue
        return entry

    if use_previous:
        raise SystemExit("Aucune liste précédente compatible dans l’historique.")
    raise SystemExit("Aucun résultat local compatible dans l’historique.")


def cmd_history(args: argparse.Namespace) -> None:
    history_file = _history_file_from_args(args)
    entries = _history_read(history_file)
    if args.clear:
        _ensure_parent_dir(history_file)
        with open(history_file, "w", encoding="utf-8"):
            pass
        print(json.dumps({"ok": True, "cleared": True, "history_file": history_file}, ensure_ascii=False, indent=2))
        return

    if args.name or args.previous:
        entry = _history_select(entries, name=args.name, previous=args.previous)
        if entry is None:
            raise SystemExit("Aucun résultat correspondant dans l’historique.")
        _emit_output(200, entry, args.format)
        return

    if args.format == "table":
        rows = []
        for entry in reversed(entries[-args.limit:]):
            rows.append(
                {
                    "timestamp": entry.get("timestamp"),
                    "name": entry.get("name"),
                    "table": entry.get("table"),
                    "total": entry.get("total"),
                    "project": entry.get("project"),
                    "query": entry.get("query"),
                }
            )
        if not rows:
            print("historique vide")
            return
        _print_table(rows)
        return

    _emit_output(200, {"history_file": history_file, "count": len(entries), "results": entries[-args.limit:]}, args.format)



def cmd_add_to_list(args: argparse.Namespace) -> None:
    base_entry = _history_select_base_entry(args)
    base_table = _history_entry_table(base_entry)
    base_ids = _history_entry_ids(base_entry)

    code, data = _request(
        base_url=args.base_url,
        path="ask_logic",
        method="POST",
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=args.raw,
        response_format=args.response_format,
        payload=_base_payload_from_args(args),
    )
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        _emit_output(code, data, args.format)
        raise SystemExit(1)

    new_table = _result_table_from_response(data)
    new_ids = _result_ids_from_response(data)
    if new_table == "" or not new_ids:
        _emit_output(code, data, args.format)
        return
    if new_table != base_table:
        raise SystemExit(f"La nouvelle demande renvoie la table {new_table}, incompatible avec la liste de base {base_table}.")

    merged_ids = list(dict.fromkeys(base_ids + new_ids))
    result_name = (getattr(args, "result_name", None) or "").strip() or str(base_entry.get("name") or "").strip() or _history_make_name(args.q, base_table, _history_read(_history_file_from_args(args)))
    entry = _history_store_named_result(
        args,
        name=result_name,
        query=args.q,
        table=base_table,
        ids=merged_ids,
        response_path="add_to_list",
        meta={
            "base_name": base_entry.get("name"),
            "base_total": len(base_ids),
            "added_total": len(new_ids),
        },
    )
    _emit_output(
        200,
        {
            "ok": True,
            "updated": True,
            "name": entry["name"],
            "table": base_table,
            "ids": merged_ids,
            "total": len(merged_ids),
            "base_total": len(base_ids),
            "added_total": len(new_ids),
        },
        args.format,
    )



def cmd_follow_links(args: argparse.Namespace) -> None:
    base_entry = _history_select_base_entry(args)
    input_table = _history_entry_table(base_entry)
    input_ids = _history_entry_ids(base_entry)
    payload = {
        "project": args.project or base_entry.get("project"),
        "input_table": input_table,
        "input_ids": input_ids,
        "link_type": args.link_type,
        "from": args.from_side,
        "to": args.to_side,
        "output_table": args.output_table,
    }
    code, data = _request(
        base_url=args.base_url,
        path="follow_links",
        method="POST",
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=args.raw,
        response_format=args.response_format,
        payload=payload,
    )
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        _emit_output(code, data, args.format)
        raise SystemExit(1)

    result_table = str((data or {}).get("type") or args.output_table).strip()
    result_ids = []
    if isinstance(data, dict) and isinstance(data.get("value"), list):
        for value in data["value"]:
            try:
                ivalue = int(value)
            except Exception:
                continue
            if ivalue > 0:
                result_ids.append(ivalue)
    result_name = (getattr(args, "result_name", None) or "").strip() or str(base_entry.get("name") or "").strip() or _history_make_name(args.link_type, result_table, _history_read(_history_file_from_args(args)))
    entry = _history_store_named_result(
        args,
        name=result_name,
        query=f"{args.link_type} from {base_entry.get('name')}",
        table=result_table,
        ids=result_ids,
        response_path="follow_links",
        meta={
            "base_name": base_entry.get("name"),
            "link_type": args.link_type,
            "from": args.from_side,
            "to": args.to_side,
            "input_table": input_table,
            "output_table": result_table,
        },
    )
    _emit_output(
        code,
        {
            "ok": True,
            "name": entry["name"],
            "table": result_table,
            "ids": result_ids,
            "total": len(result_ids),
            "meta": (data or {}).get("meta") if isinstance(data, dict) else None,
        },
        args.format,
    )


def get_token() -> str:
    tok = os.environ.get("THAMOUS_TOKEN")
    if tok:
        return tok.strip()

    tok_file = os.environ.get("THAMOUS_TOKEN_FILE") or DEFAULT_TOKEN_FILE
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

    raise SystemExit(
        "THAMOUS_TOKEN manquant. "
        "Enregistre-le dans ~/.config/thamous/token "
        "ou utilise --token-file /chemin/vers/token. "
        "Pour le régénérer depuis le web : connecte-toi à Thamous puis ouvre "
        "https://thamous.ouvaton.org/thamous/php/ajax_get_api_token.php"
    )


def _token_help_message() -> str:
    return (
        "Token Thamous invalide ou expiré.\n"
        "Procédure simple :\n"
        "1. Se connecter sur https://thamous.ouvaton.org/thamous/\n"
        "2. Ouvrir https://thamous.ouvaton.org/thamous/php/ajax_get_api_token.php\n"
        "3. Copier la valeur `token`\n"
        "4. L’enregistrer avec :\n"
        "   python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py "
        "save-token --token VOTRE_TOKEN\n"
        "5. Vérifier avec :\n"
        "   python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py token-status"
    )


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    return json.dumps(v, ensure_ascii=False)


def _pick_table_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "id",
        "nom",
        "titre",
        "annee",
        "type",
        "langue",
        "editeur",
        "count",
        "role",
        "url",
    ]
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


def _request(
    *,
    base_url: str,
    path: str,
    method: str,
    auth: bool,
    timeout_s: int,
    verbose: bool,
    raw: bool,
    response_format: str,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
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


def cmd_save_token(args: argparse.Namespace) -> None:
    token_file = os.path.expanduser(args.token_file or DEFAULT_TOKEN_FILE)
    token = (args.token or "").strip()
    if not token:
        raise SystemExit("Token vide.")
    _ensure_parent_dir(token_file)
    with open(token_file, "w", encoding="utf-8") as fh:
        fh.write(token)
    print(
        json.dumps(
            {
                "ok": True,
                "token_file": token_file,
                "length": len(token),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_token_status(args: argparse.Namespace) -> None:
    token_file = os.path.expanduser(args.token_file or os.environ.get("THAMOUS_TOKEN_FILE") or DEFAULT_TOKEN_FILE)
    source = None
    token = None
    if os.environ.get("THAMOUS_TOKEN"):
        token = os.environ["THAMOUS_TOKEN"].strip()
        source = "env:THAMOUS_TOKEN"
    elif os.path.exists(token_file):
        token = _read_text_file(token_file).strip()
        source = token_file
    else:
        print(
            json.dumps(
                {
                    "ok": False,
                    "status": "missing",
                    "message": "Aucun token local trouvé.",
                    "expected_token_file": token_file,
                    "help": _token_help_message(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Authorization": f"Bearer {token}",
        "X-Thamous-Token": token,
    }
    try:
        response = requests.get(
            args.base_url,
            params={"path": "logic_context", "projet": args.projet, "token": token},
            headers=headers,
            timeout=args.timeout,
        )
        data = response.json()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "status": "error",
                    "source": source,
                    "message": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)

    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        err = data["error"]
        code = str(err.get("code") or "")
        message = str(err.get("message") or "")
        expired = code == "UNAUTHORIZED" and message in {"Invalid token", "Missing token"}
        print(
            json.dumps(
                {
                    "ok": False,
                    "status": "expired_or_invalid" if expired else "error",
                    "source": source,
                    "error": err,
                    "help": _token_help_message() if expired else "",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)

    print(
        json.dumps(
            {
                "ok": True,
                "status": "valid",
                "source": source,
                "signature": data.get("signature"),
                "projects": data.get("projects"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _open_url(url: str) -> None:
    url = (url or "").strip()
    if not url:
        raise SystemExit("URL vide, ouverture impossible.")
    if webbrowser.open(url):
        return

    if sys.platform.startswith("darwin"):
        fallback = ["open", url]
    elif os.name == "nt":
        fallback = ["cmd", "/c", "start", "", url]
    else:
        fallback = ["xdg-open", url]
    subprocess.check_call(fallback)



def cmd_fiche_url(args: argparse.Namespace) -> None:
    code, data = _request(
        base_url=args.base_url,
        path="fiche_url",
        method="GET",
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=args.raw,
        response_format=args.response_format,
        params={"id": args.id, "table": args.table, **({"projet": args.projet} if args.projet else {})},
    )
    if args.response_format == "url" and isinstance(data, dict) and data.get("_raw"):
        print(str(data.get("_raw", "")).strip())
        return
    _emit_output(code, data, args.format)


def cmd_open_fiche(args: argparse.Namespace) -> None:
    code, data = _request(
        base_url=args.base_url,
        path="fiche_url",
        method="GET",
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=False,
        response_format="url",
        params={"id": args.id, "table": args.table, **({"projet": args.projet} if args.projet else {})},
    )
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
    _open_url(url)
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(url)


def cmd_open_list(args: argparse.Namespace) -> None:
    code, data = _request(
        base_url=args.base_url,
        path="ask_logic",
        method="POST",
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=False,
        response_format="url",
        payload=_base_payload_from_args(args),
    )
    url = ""
    if isinstance(data, dict) and data.get("_raw"):
        url = str(data["_raw"]).strip()
    elif isinstance(data, str):
        url = data.strip()
    if not url:
        _emit_output(code, data, args.format)
        return
    if args.print_only:
        print(url)
        return
    _open_url(url)
    if args.format == "json":
        print(json.dumps({"url": url}, ensure_ascii=False, indent=2))
    else:
        print(url)


def cmd_project_keywords(args: argparse.Namespace) -> None:
    params = {}
    if args.project:
        params['project'] = args.project
    code, data = _request(
        base_url=args.base_url,
        path='keywords_project',
        method='GET',
        auth=True,
        timeout_s=args.timeout,
        verbose=args.verbose,
        raw=args.raw,
        response_format=args.response_format,
        params=params,
    )
    _emit_output(code, data, args.format)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base-url",
        default=os.environ.get("THAMOUS_V2_BASE_URL", DEFAULT_BASE_URL),
        help="URL de base de l’API v2 (ou THAMOUS_V2_BASE_URL).",
    )
    ap.add_argument("--timeout", type=int, default=45, help="Timeout HTTP en secondes.")
    ap.add_argument(
        "--token-file",
        default=os.environ.get("THAMOUS_TOKEN_FILE"),
        help="Chemin d’un fichier contenant le token (ou THAMOUS_TOKEN_FILE).",
    )
    ap.add_argument(
        "--history-file",
        default=os.environ.get("THAMOUS_HISTORY_FILE", DEFAULT_HISTORY_FILE),
        help="Chemin du fichier d’historique local (ou THAMOUS_HISTORY_FILE).",
    )
    ap.add_argument("--raw", action="store_true", help="Affiche la réponse brute.")
    ap.add_argument("--verbose", action="store_true", help="Logs HTTP sur stderr.")
    ap.add_argument("--response-format", default="json", choices=["json", "url"], help="Format demandé à l’API.")
    ap.add_argument("--format", default="json", choices=["json", "jsonl", "table"], help="Format d’affichage local.")

    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("health")

    sp = sub.add_parser("history")
    sp.add_argument("--name")
    sp.add_argument("--previous", action="store_true")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("add-to-list")
    sp.add_argument("--q", required=True)
    sp.add_argument("--project")
    sp.add_argument("--provider")
    sp.add_argument("--model")
    sp.add_argument("--result-name")
    sp.add_argument("--base-name")
    sp.add_argument("--previous", action="store_true")
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

    sp = sub.add_parser("follow-links")
    sp.add_argument("--project")
    sp.add_argument("--base-name")
    sp.add_argument("--previous", action="store_true")
    sp.add_argument("--result-name")
    sp.add_argument("--link-type", required=True)
    sp.add_argument("--from", dest="from_side", required=True, choices=["source", "but"])
    sp.add_argument("--to", dest="to_side", required=True, choices=["source", "but"])
    sp.add_argument("--output-table", required=True)

    sp = sub.add_parser("save-token")
    sp.add_argument("--token", required=True)
    sp.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)

    sp = sub.add_parser("token-status")
    sp.add_argument("--projet", default="perso")
    sp.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)

    sp = sub.add_parser("project-keywords")
    sp.add_argument("--project")

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

    for name in ["text-to-structure", "ask-logic"]:
        sp = sub.add_parser(name)
        sp.add_argument("--q", required=True)
        sp.add_argument("--project")
        sp.add_argument("--provider")
        sp.add_argument("--model")
        sp.add_argument("--result-name")
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

    if args.action == "save-token":
        cmd_save_token(args)
        return
    elif args.action == "token-status":
        cmd_token_status(args)
        return
    elif args.action == "history":
        cmd_history(args)
        return
    elif args.action == "project-keywords":
        cmd_project_keywords(args)
        return
    elif args.action == "add-to-list":
        cmd_add_to_list(args)
        return
    elif args.action == "follow-links":
        cmd_follow_links(args)
        return
    elif args.action == "health":
        code, data = _request(
            base_url=args.base_url,
            path="health",
            method="GET",
            auth=False,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
        )
    elif args.action == "logic-context":
        params = {}
        if args.projet:
            params["projet"] = args.projet
        code, data = _request(
            base_url=args.base_url,
            path="logic_context",
            method="GET",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            params=params,
        )
    elif args.action == "text-to-structure":
        code, data = _request(
            base_url=args.base_url,
            path="text_to_structure",
            method="POST",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            payload=_base_payload_from_args(args),
        )
    elif args.action == "ask-logic":
        code, data = _request(
            base_url=args.base_url,
            path="ask_logic",
            method="POST",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            payload=_base_payload_from_args(args),
        )
    elif args.action == "fiche-url":
        cmd_fiche_url(args)
        return
    elif args.action == "open-fiche":
        cmd_open_fiche(args)
        return
    elif args.action == "open-list":
        cmd_open_list(args)
        return
    elif args.action == "compile-logic":
        code, data = _request(
            base_url=args.base_url,
            path="compile_logic",
            method="POST",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            payload=_load_json_from_args(args.payload_file, args.payload_json),
        )
    elif args.action == "search-logic":
        code, data = _request(
            base_url=args.base_url,
            path="search_logic",
            method="POST",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            payload=_load_json_from_args(args.payload_file, args.payload_json),
        )
    elif args.action == "replay-logic":
        code, data = _request(
            base_url=args.base_url,
            path="replay_logic",
            method="POST",
            auth=True,
            timeout_s=args.timeout,
            verbose=args.verbose,
            raw=args.raw,
            response_format=args.response_format,
            payload=_load_json_from_args(args.payload_file, args.payload_json),
        )
    else:
        raise SystemExit(f"Action inconnue: {args.action}")

    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        err = data["error"]
        code_str = str(err.get("code") or "")
        msg = str(err.get("message") or "")
        if code_str == "UNAUTHORIZED" and msg in {"Invalid token", "Missing token"}:
            print(json.dumps({"error": err, "help": _token_help_message()}, ensure_ascii=False, indent=2))
            raise SystemExit(1)
        _emit_output(code, data, args.format)
        raise SystemExit(1)

    if args.response_format == "url" and isinstance(data, dict) and data.get("_raw"):
        print(str(data.get("_raw", "")).strip())
        return

    if args.action == "ask-logic":
        _history_store_api_result(args, data)

    _emit_output(code, data, args.format)


if __name__ == "__main__":
    main()
