#!/usr/bin/env python3
"""HakoAgent installer — cross-platform (stdlib only). Replaces install.sh.

Usage:
  python install.py              # project-local: ./hakoagent + ./AGENTS.md + .opencode/ + lib/
  python install.py --global|-g  # global: bin dir + ~/.hakoagent + OpenCode/Claude skills & commands
  python install.py --uninstall  # uninstall (project-local or global, same scope as install)
  python install.py --remove-data  # (with --uninstall) also delete the .hakoagent/ data directory
  python install.py --help|-h

The native hakodb library is downloaded from the latest github.com/hakodb/hakodb
release. Supported platforms: Windows x86_64 (.dll), Linux x86_64 (.so).
macOS has no released native library yet — installation fails with a clear
error on purpose: hakoagent runs only on a real hakodb engine, no fallback.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

RELEASE_API = "https://api.github.com/repos/hakodb/hakodb/releases/latest"
_GITHUB_HEADERS = {"User-Agent": "hakoagent-installer", "Accept": "application/vnd.github+json"}

# Asset names, in try-order (Linux: oldest glibc build loads on any newer glibc).
_NATIVE_ASSETS = {
    "win32": ["hakodb-x86_64-pc-windows-msvc.dll"],
    "linux": [
        "libhakodb-x86_64-unknown-linux-glibc2.28-el8.so",
        "libhakodb-x86_64-unknown-linux-glibc2.35-ubuntu22.so",
        "libhakodb-x86_64-unknown-linux-glibc2.39-ubuntu24.so",
    ],
}

SCRIPT_DIR = Path(__file__).resolve().parent
BIN_NAMES = ("hakoagent", "hakoagent-mcp", "hakoagent-cli")


def _agents_md_src():
    return SCRIPT_DIR / "assets" / "AGENTS.md"


def _agents_md_owned(path):
    """True when the file was installed by hakoagent (safe to overwrite on
    uninstall). Pre-existing user AGENTS.md files are never touched."""
    try:
        return path.exists() and "HakoAgent" in path.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        return False


def _copy_agents_md(dst):
    """Install AGENTS.md without clobbering an existing user file.
    Never copies onto the source itself (repo-local install is a same walk)."""
    src = _agents_md_src()
    if not src.exists() or dst.resolve() == src.resolve():
        return
    if dst.exists() and not _agents_md_owned(dst):
        print("Found existing %s — kept (hakoagent never overwrites it).\n"
              "Merge agent instructions from %s manually." % (dst, src))
        return
    shutil.copyfile(src, dst)
    print("Installed AGENTS.md to %s" % dst)


# ---------------------------------------------------------------------------
# Native library download (github.com/hakodb/hakodb releases)
# ---------------------------------------------------------------------------

def _fail(msg):
    print("ERROR: %s" % msg, file=sys.stderr)
    sys.exit(1)


def _download(name, dest):
    """Download a release asset to dest. Returns dest path."""
    data = _download_bytes(name)
    dest.write_bytes(data)
    print("Downloaded: %s -> %s (%d KB)" % (name, dest, len(data) // 1024))
    return dest


def _download_bytes(name):
    release = _get_release()
    asset = next((a for a in release["assets"] if a["name"] == name), None)
    if asset is None:
        _fail("asset %s not found in release %s" % (name, release.get("tag_name", "?")))
    return _fetch(asset["browser_download_url"])


def _fetch(url):
    req = urllib.request.Request(url, headers=_GITHUB_HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _get_release():
    try:
        req = urllib.request.Request(RELEASE_API, headers=_GITHUB_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except (OSError, ValueError) as exc:
        _fail("cannot query %s: %s\nCheck your network connection." % (RELEASE_API, exc))


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def install_native_lib(lib_dir):
    """Ensure a loadable native hakodb lib exists in lib_dir.

    Downloads the platform asset from the latest release and verifies it
    (SHA256SUMS + ctypes load). Returns the loaded lib path.
    """
    names = _NATIVE_ASSETS.get(sys.platform)
    if not names:
        _fail(
            "unsupported platform %r: no hakodb native library (Windows x86_64 and "
            "Linux x86_64 only for now). hakoagent cannot run without it." % (sys.platform,)
        )
    lib_dir.mkdir(parents=True, exist_ok=True)

    # SHA256SUMS asset maps every asset name -> digest.
    sums = {}
    try:
        for line in _download_bytes("SHA256SUMS").decode("utf-8", "replace").splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                sums[parts[1].strip().lstrip("*")] = parts[0]
    except (OSError, ValueError):
        sums = {}
    (lib_dir / "SHA256SUMS.txt").write_text(
        "\n".join("%s  %s" % (d, n) for n, d in sorted(sums.items())) + "\n"
    )

    for name in names:
        dest = lib_dir / name
        want = sums.get(name)
        if dest.exists() and want and _sha256(dest) == want:
            print("Native library already installed: %s" % dest)
        else:
            _download(name, dest)
            if want:
                got = _sha256(dest)
                if got != want:
                    dest.unlink()
                    print("WARN: SHA256 mismatch for %s (got %s, want %s)" % (name, got, want))
            _download("hakodb.h", lib_dir / "hakodb.h")

        # Verify it actually loads on this machine.
        from ctypes import CDLL
        try:
            CDLL(str(dest))
        except OSError as exc:
            print("WARN: %s failed to load (%s); trying next variant" % (name, exc))
            dest.unlink()
            continue
        return dest

    _fail("no loadable hakodb native library for %s" % sys.platform)


# ---------------------------------------------------------------------------
# Skill / command deployment (OpenCode + Claude)
# ---------------------------------------------------------------------------

def _skill_names():
    base = SCRIPT_DIR / ".opencode" / "skills"
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if (d / "SKILL.md").exists())


def _glob_global_dirs():
    """(skills dirs, command dirs) — same layout on POSIX and Windows
    (OpenCode and Claude both read ~/.config/opencode and ~/.claude)."""
    home = Path.home()
    skills = [home / ".config" / "opencode" / "skills", home / ".claude" / "skills"]
    commands = [home / ".config" / "opencode" / "commands", home / ".claude" / "commands"]
    return skills, commands


def _copy_skills_commands(skills_dirs, commands_dirs, uninstall=False):
    for name in _skill_names():
        for d in skills_dirs:
            target = d / name / "SKILL.md"
            if uninstall:
                if target.parent.is_dir():
                    shutil.rmtree(target.parent, ignore_errors=True)
                    print("Removed: %s" % target.parent)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SCRIPT_DIR / ".opencode" / "skills" / name / "SKILL.md", target)
                print("Installed skill: %s" % target)

    cmd_src = SCRIPT_DIR / ".opencode" / "commands" / "hakoagent.md"
    for d in commands_dirs:
        target = d / "hakoagent.md"
        if uninstall:
            if target.exists():
                target.unlink()
                print("Removed: %s" % target)
        elif cmd_src.exists():
            d.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cmd_src, target)
            print("Installed command: %s" % target)


def _clean_mcp_config():
    """Remove hakoagent MCP entries from global Claude/OpenCode configs."""
    home = Path.home()
    claude = home / ".claude.json"
    if claude.exists():
        try:
            data = json.loads(claude.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        if isinstance(data, dict) and "hakoagent" in data.get("mcpServers", {}):
            del data["mcpServers"]["hakoagent"]
            claude.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print("Removed hakoagent from %s" % claude)

    oc = home / ".config" / "opencode" / "opencode.jsonc"
    if not oc.exists():
        oc = home / ".config" / "opencode" / "opencode.json"
    if oc.exists():
        try:
            data = json.loads(oc.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None  # JSONC with comments: refuse to rewrite, tell the user
            print("Could not parse %s (JSONC?) — remove the hakoagent server entry manually." % oc)
        if isinstance(data, dict):
            mcp = data.get("mcp", {})
            if isinstance(mcp, dict):
                changed = False
                if "hakoagent" in mcp:  # legacy V1 shape
                    del mcp["hakoagent"]
                    changed = True
                servers = mcp.get("servers")
                if isinstance(servers, dict) and "hakoagent" in servers:  # V2 shape
                    del servers["hakoagent"]
                    changed = True
                    if not servers:
                        mcp.pop("servers", None)
                if not isinstance(mcp, dict) or not mcp:
                    data.pop("mcp", None)
                if changed:
                    oc.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                    print("Removed hakoagent from %s" % oc)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

def install_paths(global_mode):
    if global_mode:
        if os.name == "nt":
            bin_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hakoagent" / "bin"
        else:
            bin_dir = Path.home() / ".local" / "bin"
        return {"bin": bin_dir, "agent": Path.home() / ".hakoagent", "lib": bin_dir / "lib",
                "project": bin_dir}
    return {"bin": Path.cwd(), "agent": Path.cwd() / ".hakoagent", "lib": Path.cwd() / "lib",
            "project": Path.cwd()}


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def do_uninstall(global_mode, remove_data):
    p = install_paths(global_mode)
    label = "globally" if global_mode else "from project"
    print("=== Uninstalling HakoAgent %s ===" % label)

    for bin_name in BIN_NAMES:
        for f in [p["bin"] / bin_name] + ([p["bin"] / (bin_name + ".cmd")] if os.name == "nt" else []):
            if f.exists():
                f.unlink()
                print("Removed: %s" % f)
            else:
                print("Not found: %s" % f)

    extra = [p["lib"] / "hakodb.h", p["lib"] / "SHA256SUMS.txt"]
    for f in extra + sorted(p["lib"].glob("libhakodb-*.so")) + sorted(p["lib"].glob("hakodb-*.dll")):
        if f.exists():
            f.unlink()
            print("Removed: %s" % f)
    shutil.rmtree(p["lib"], ignore_errors=True)

    if global_mode:
        skills, commands = _glob_global_dirs()
        _copy_skills_commands(skills, commands, uninstall=True)
        agents_md = p["agent"] / "AGENTS.md"
        if _agents_md_owned(agents_md):
            agents_md.unlink()
            print("Removed: %s" % agents_md)
        _clean_mcp_config()
    else:
        # project-local: skills/commands live inside this repo's .opencode/
        for name in _skill_names():
            d = p["project"] / ".opencode" / "skills" / name
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
                print("Removed: %s" % d)
        c = p["project"] / ".opencode" / "commands" / "hakoagent.md"
        if c.exists():
            c.unlink()
            print("Removed: %s" % c)
        a = p["project"] / "AGENTS.md"
        if _agents_md_owned(a):
            a.unlink()
            print("Removed: %s" % a)
        elif a.exists():
            print("Kept: %s (pre-existing AGENTS.md, not installed by hakoagent)" % a)

    if remove_data and p["agent"].is_dir():
        shutil.rmtree(p["agent"], ignore_errors=True)
        print("Removed: %s (--remove-data)" % p["agent"])
    elif p["agent"].is_dir():
        print("Kept: %s (pass --remove-data to delete)" % p["agent"])

    print("Uninstall complete%s." % (" (global)" if global_mode else ""))


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def _path_hint(bin_dir):
    if os.name == "nt":
        print("Add to PATH (PowerShell, one-time):")
        print('  setx PATH "%s;%%PATH%%"' % bin_dir)
        print("Then run: hakoagent-cli --help   (or: python %s\\hakoagent-cli)" % bin_dir)
    else:
        print('Add to PATH: export PATH="%s:$PATH"' % bin_dir)


def do_install(global_mode):
    p = install_paths(global_mode)
    print("=== Installing HakoAgent %s ===" % ("globally" if global_mode else "project-local"))

    # Native library first — hakoagent is dead without it (no fallback).
    lib = install_native_lib(p["lib"])
    if global_mode:
        bins = []
        for name in BIN_NAMES:
            src = SCRIPT_DIR / name
            dst = p["bin"] / name
            if src.exists():
                shutil.copyfile(src, dst)
                if os.name != "nt":
                    dst.chmod(dst.stat().st_mode | 0o111)
                bins.append(dst)
        # Windows .cmd shims so PATH exec works without .exe
        if os.name == "nt":
            for name in BIN_NAMES:
                (p["bin"] / (name + ".cmd")).write_text('@python "%%~dp0%s" %%*\r\n' % name)
        skills, commands = _glob_global_dirs()
        _copy_skills_commands(skills, commands)
        (p["agent"]).mkdir(parents=True, exist_ok=True)
        # ~/.hakoagent/AGENTS.md is hakoagent-owned storage: overwrite on upgrade is fine.
        _copy_agents_md(p["agent"] / "AGENTS.md")
        for dst in bins:
            print("Installed: %s" % dst)
        print("Installed skills to OpenCode/Claude skills directories")
        print("Installed /hakoagent command to global command directories")
        print("Native library: %s" % lib)
        print("MCP server is OFF by default. Run 'hakoagent mcp enable' inside a project.")
        _path_hint(p["bin"])
    else:
        if SCRIPT_DIR != p["project"]:
            for name in BIN_NAMES:
                src = SCRIPT_DIR / name
                if src.exists():
                    shutil.copyfile(src, p["project"] / name)
            for name in _skill_names():
                dst_dir = p["project"] / ".opencode" / "skills" / name
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SCRIPT_DIR / ".opencode" / "skills" / name / "SKILL.md",
                                dst_dir / "SKILL.md")
            cmd_src = SCRIPT_DIR / ".opencode" / "commands" / "hakoagent.md"
            if cmd_src.exists():
                dst = p["project"] / ".opencode" / "commands" / "hakoagent.md"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cmd_src, dst)
            # Only for external targets: never (re)create AGENTS.md inside
            # this repository itself — its copy lives in assets/.
            _copy_agents_md(p["project"] / "AGENTS.md")
        if os.name != "nt":
            for name in BIN_NAMES:
                f = p["project"] / name
                if f.exists():
                    f.chmod(f.stat().st_mode | 0o111)
        p["agent"].mkdir(parents=True, exist_ok=True)
        print("Native library: %s" % lib)
        print("Run: python hakoagent init --db ./.hakoagent/hakoagent.db --collections all")
        print("Run: python hakoagent-mcp   (mcp server; OFF until 'hakoagent mcp enable')")


def main():
    ap = argparse.ArgumentParser(prog="install.py", add_help=True,
                                 description="Install/uninstall HakoAgent (cross-platform).")
    ap.add_argument("--global", "-g", dest="global_mode", action="store_true",
                    help="install to the global bin dir (~/.local/bin or %%LOCALAPPDATA%%)")
    ap.add_argument("--uninstall", action="store_true", help="remove installed files")
    ap.add_argument("--remove-data", action="store_true",
                    help="(with --uninstall) also delete the .hakoagent/ data directory")
    ap.add_argument("--license", action="store_true", help="show license note")
    args = ap.parse_args()

    if args.license:
        print("HakoAgent: standalone Python script (see repository LICENSE).")
        return 0
    if args.uninstall:
        do_uninstall(args.global_mode, args.remove_data)
    elif args.remove_data and not args.uninstall:
        print("--remove-data only makes sense with --uninstall")
        return 1
    else:
        do_install(args.global_mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
