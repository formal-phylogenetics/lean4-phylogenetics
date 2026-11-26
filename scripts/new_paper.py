#!/usr/bin/env python3
"""Start the repository of a paper of a hub's catalog.

    python3 scripts/new_paper.py ID              # e.g. snaq, nanuq-plus
    python3 scripts/new_paper.py ID --dry-run    # show what it would do

Run it when the paper's formalization starts, one paper at a time, not ahead of it: a repository
that waits moves with every train with nothing in it (docs/WORKFLOW.md, Section 2).

It creates lean4-<id> in the workspace's papers/<hub>/, on the train, under the paper's hub, in the layout of
docs/CONVENTIONS.md, Section 3, with <Root> the catalog's root and <Paper> the paper's name (the
root, unless the entry gives `paper`):

  - lakefile.toml, lean-toolchain and lake-manifest.json: the libraries <Root> and, last, Palomar;
    it requires Mathlib, the root library Phylogenetics, the library of its hub and of every hub
    above it, the libraries of the hubs it `uses`, and the repositories of the formalized papers it
    builds on, each by commit;
  - <Root>/Basic/ and <Root>/External/, each with a README, and <Root>/Defs.lean,
    palomar/<Paper>/Challenge.lean and palomar/<Paper>/Solution.lean as placeholder modules;
  - .gitignore, LICENSE, a stub README.md, and CI that builds;
  - its private files (notes/, .vscode/, CLAUDE.md), kept outside the
    repository and linked into it by gitignored symbolic links, from templates kept with this
    repository's own private files (where its gitignored `notes` link points);

then seeds .lake/packages from local checkouts on the train, by hard links, so that nothing is
downloaded or rebuilt; builds; checks that the dependencies are up to date; commits; and marks the
paper "in-progress" in its hub's catalog. Nothing is pushed and no GitHub repository is created.

It only starts a repository, in the layout of one paper. When papers share one (their entries give
the same `repo`), it starts it with the first, and the others join it by hand, as
formalize-math-paper's references/multi-paper.md says: it refuses a repository that exists already.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path

import collection as col

TEMPLATES = col.COLLECTION / 'templates' / 'paper'
INDENT = ' ' * 18  # the value column of the Phase 0 configuration block


def render(path: Path, values: dict[str, str]) -> str:
    text = path.read_text()

    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise SystemExit(f'{path.name}: no value for {{{{{key}}}}}')
        return values[key]

    return re.sub(r'\{\{(\w+)\}\}', sub, text)


def run(cmd: list, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print('  $', ' '.join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, text=True, capture_output=True)
    if check and r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f'failed: {" ".join(str(c) for c in cmd)}')
    return r


def wrap(text: str) -> str:
    return textwrap.fill(text, width=100, subsequent_indent=INDENT, break_on_hyphens=False)


# ---------------------------------------------------------------------------------------------
# What the repository requires


def requirements(c: col.Collection, p: col.Paper) -> tuple[list[dict], list[str]]:
    """The direct git requirements besides Mathlib (name, url, rev, local checkout or None,
    comment), and notes on the papers it builds on that cannot be required."""
    pins = c.train['pins']
    reqs = [dict(name='Phylogenetics', url=c.repo('lean4-phylogenetics')['url'], rev=pins['Phylogenetics'],
                 local=None, comment='The root of the collection: the shared library of phylogenetics.')]
    above = [h['name'] for h in c.hubs_above(p.hub)]
    for name in above + [h for h in p.uses if h not in above]:
        hub = c.repo(name)
        what = ('The hub of this paper' if name == p.hub else
                f'The hub {name}, above the hub of this paper' if name in above else
                f'The library {name}, which this paper uses' if hub.get('role') == 'library' else
                f'The hub {name}, whose library this paper uses')
        reqs.append(dict(name=hub['package'], url=hub['url'], rev=pins[hub['package']], local=c.path(name),
                         comment=f'{what}: {hub.get("title", "")}.'))
    notes = []
    for dep in p.builds_on:
        q = c.paper(dep)
        if q.repo == p.repo:
            continue   # a paper of the same repository: its library is imported directly
        if q.commit and q.path.is_dir() and c.on_train(q.repo):
            reqs.append(dict(name=q.root, url=q.github, rev=q.commit, local=q.path,
                             comment=f'{q.cite}, which this paper builds on.'))
        else:
            notes.append(dep)
    return reqs, notes


def lake_requires(path: Path) -> list[dict]:
    """The git requirements of a local checkout's lakefile.toml."""
    f = path / 'lakefile.toml'
    if not f.is_file():
        return []
    return [r for r in tomllib.loads(f.read_text()).get('require', []) if 'git' in r]


def closure(reqs: list[dict]) -> list[dict]:
    """The requirements of the requirements that are repositories of the collection, recursively:
    the packages that the manifest must list as inherited. Pins must agree."""
    seen = {r['name']: r for r in reqs}
    out: list[dict] = []
    stack = [r for r in reqs if r['local'] is not None]
    while stack:
        r = stack.pop()
        for sub in lake_requires(r['local']):
            name = sub['name']
            if name == 'mathlib':
                continue
            if name in seen:
                if seen[name]['rev'] != sub['rev']:
                    raise SystemExit(f'{r["name"]} requires {name} at {sub["rev"][:7]}, '
                                     f'but this repository requires it at {seen[name]["rev"][:7]}')
                continue
            repo = sub['git'].rstrip('/').rsplit('/', 1)[-1]
            local = col.repo_path(repo)
            entry = dict(name=name, url=sub['git'], rev=sub['rev'], local=local if name != 'Phylogenetics' else None)
            seen[name] = entry
            out.append(entry)
            if entry['local'] is not None:
                stack.append(entry)
    return out


def requires_block(c: col.Collection, reqs: list[dict]) -> str:
    blocks = [f"# {r['comment']}\n[[require]]\nname = \"{r['name']}\"\ngit = \"{r['url']}\"\n"
              f"rev = \"{r['rev']}\"\n" for r in reqs]
    blocks.append(f"[[require]]\nname = \"mathlib\"\nscope = \"leanprover-community\"\n"
                  f"rev = \"{c.train['mathlib']}\"\n")
    return '\n'.join(blocks)


def siblings_text(c: col.Collection, p: col.Paper, notes: list[str]) -> str:
    lines = []
    for dep in p.builds_on:
        q = c.paper(dep)
        if q.repo == p.repo:
            how = (f'a paper of this repository ({q.status}): import its library once it has joined '
                   '(formalize-math-paper, references/multi-paper.md, Section 4)')
        elif dep not in notes:
            how = f'formalized in {q.repo}, required at `{q.commit[:7]}`: import it (CONVENTIONS, Section 6)'
        elif q.status == 'formalized':
            how = (f'formalized in {q.repo}, which is off the train and cannot be required: state what the '
                   f'proofs use in `{p.root}/External/` and prove it there (CONVENTIONS, Section 4)')
        else:
            how = (f'not formalized yet ({q.status}): state what the proofs use in `{p.root}/External/` and '
                   f'prove it there, and record it in the catalog (CONVENTIONS, Section 4)')
        for cov in q.covered_by:
            how += f'; already in {cov["repo"]}: {cov["what"]}'
        lines.append(f'- `{q.id}`, {q.cite}: {how}.')
    if not lines:
        return ('None known before the inventory. Phase 1 lists them here, and in `builds_on` in the '
                "hub's catalog.")
    return '\n'.join(lines)


# ---------------------------------------------------------------------------------------------
# Lake


def manifest_entry(name: str, url: str, rev: str, inherited: bool) -> dict:
    return {'url': url, 'type': 'git', 'subDir': None, 'scope': '', 'rev': rev, 'name': name,
            'manifestFile': 'lake-manifest.json', 'inputRev': rev, 'inherited': inherited,
            'configFile': 'lakefile.toml'}


def lake_json(m: dict) -> str:
    """The manifest in the layout that `lake update` writes."""
    v = lambda x: json.dumps(x, ensure_ascii=False)
    pkgs = ['{' + ',\n   '.join(f'{v(k)}: {v(x)}' for k, x in e.items()) + '}' for e in m['packages']]
    return ('{' + f'"version": {v(m["version"])},\n "packagesDir": {v(m["packagesDir"])},\n'
            ' "packages":\n [' + ',\n  '.join(pkgs) + '],\n'
            f' "name": {v(m["name"])},\n "lakeDir": {v(m["lakeDir"])},\n'
            f' "fixedToolchain": {v(m["fixedToolchain"])}' + '}\n')


def check_seed(c: col.Collection, seed: Path) -> dict:
    """The seed repository's manifest, after checking that it is on the train."""
    if not (seed / '.lake' / 'packages' / 'mathlib').is_dir():
        raise SystemExit(f'{seed} has no compiled Mathlib in .lake/packages: build it, or use --no-seed')
    if (seed / 'lean-toolchain').read_text().strip() != c.train['lean']:
        raise SystemExit(f'{seed} is not on the train ({c.train["lean"]}): use another --seed, or --no-seed')
    m = json.loads((seed / 'lake-manifest.json').read_text())
    by = {e['name']: e for e in m['packages']}
    if by.get('mathlib', {}).get('inputRev') != c.train['mathlib']:
        raise SystemExit(f'{seed} does not require Mathlib {c.train["mathlib"]}: use another --seed')
    if by.get('Phylogenetics', {}).get('rev') != c.train['pins']['Phylogenetics']:
        raise SystemExit(f'{seed} requires another commit of lean4-phylogenetics than the train: '
                         'use another --seed, or --no-seed')
    return m


LEAN_PATHS = ['*.lean', 'lakefile.toml', 'lake-manifest.json', 'lean-toolchain']


def vendor_local(name: str, url: str, rev: str, local: Path, packages: Path) -> bool:
    """Clone a local checkout into .lake/packages/<name> at `rev`, with the GitHub remote, and
    hard-link its build when no Lean file of the checkout differs from `rev`. Returns whether it
    linked one."""
    dest = packages / name
    run(['git', 'clone', '--quiet', local, dest], cwd=packages)
    run(['git', 'checkout', '--quiet', '--detach', rev], cwd=dest)
    run(['git', 'remote', 'set-url', 'origin', url], cwd=dest)
    same = run(['git', 'diff', '--quiet', rev, '--', *LEAN_PATHS], cwd=local, check=False).returncode == 0
    build = local / '.lake' / 'build'
    if same and build.is_dir():
        (dest / '.lake').mkdir()
        run(['cp', '-al', build, dest / '.lake' / 'build'], cwd=packages)
        return True
    print(f'  ! {local} differs from {rev[:7]} in its Lean files, or has no build: {name} will be built')
    return False


def seed_packages(c: col.Collection, root: str, reqs: list[dict], seed: Path, repo: Path) -> list[dict]:
    m = check_seed(c, seed)
    by = {e['name']: e for e in m['packages']}
    packages = repo / '.lake' / 'packages'
    packages.mkdir(parents=True)
    inherited = closure(reqs)
    direct = [r['name'] for r in reqs] + ['mathlib']
    entries = []
    for name in reversed(direct):  # `lake update` lists the direct requirements last to first
        r = next((r for r in reqs if r['name'] == name), None)
        if r is not None and r['local'] is not None:
            entries.append(manifest_entry(name, r['url'], r['rev'], inherited=False))
            vendor_local(name, r['url'], r['rev'], r['local'], packages)
        else:
            entries.append(dict(by[name], inherited=False))
            run(['cp', '-al', seed / '.lake' / 'packages' / name, packages / name], cwd=repo)
    for r in inherited:
        if r['local'] is not None:
            entries.append(manifest_entry(r['name'], r['url'], r['rev'], inherited=True))
            vendor_local(r['name'], r['url'], r['rev'], r['local'], packages)
    for name, e in by.items():
        if name not in direct and all(name != r['name'] for r in inherited if r['local'] is not None):
            entries.append(dict(e, inherited=True))
            run(['cp', '-al', seed / '.lake' / 'packages' / name, packages / name], cwd=repo)
    manifest = {'version': m['version'], 'packagesDir': '.lake/packages', 'packages': entries,
                'name': root, 'lakeDir': '.lake', 'fixedToolchain': False}
    (repo / 'lake-manifest.json').write_text(lake_json(manifest))
    return inherited


# ---------------------------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('id', help="the paper's id in its hub's catalog/papers.toml")
    ap.add_argument('--workspace', type=Path, default=col.WORKSPACE,
                    help='the workspace, whose papers/<hub>/ gets the repository (default: the one this repository is in)')
    ap.add_argument('--private-root', type=Path, default=None,
                    help='the private repository, with one folder per repository, as the workspace has them (default: the one '
                         "that this repository's `notes` link points into)")
    ap.add_argument('--seed', type=Path, default=None,
                    help='a local repository on the train whose compiled Mathlib to hard-link '
                         "(default: the paper's hub)")
    ap.add_argument('--no-seed', action='store_true',
                    help='fetch the dependencies with `lake update` and `lake exe cache get` instead')
    ap.add_argument('--no-build', action='store_true', help='do not build or check the dependencies')
    ap.add_argument('--no-commit', action='store_true', help='do not make the first commit')
    ap.add_argument('--trailer', action='append', default=[],
                    help="a trailer line for the first commit's message (repeatable)")
    ap.add_argument('--keep-status', action='store_true', help="leave the paper's status unchanged")
    ap.add_argument('--dry-run', action='store_true', help='print the plan and stop')
    args = ap.parse_args()

    c = col.load(private=True)
    errors = c.validate()
    if errors:
        raise SystemExit('the catalogs have errors; run scripts/status.py check:\n  ' + '\n  '.join(errors))
    p = c.paper(args.id)
    if p.status == 'formalized':
        raise SystemExit(f'{p.id} is formalized already, in {p.repo}')
    folder = col.private_folder()
    if folder is None:
        raise SystemExit("this repository has no `notes` link to its private folder, which holds the "
                         'templates of the private files')
    workspace = args.workspace.resolve()
    repo = workspace / 'papers' / col.paper_folder(p.hub) / p.repo
    private_root = (args.private_root or folder.parent).resolve()
    notes = private_root / 'papers' / col.paper_folder(p.hub) / p.repo
    if repo.exists() or repo.is_symlink():
        raise SystemExit(f'{repo} exists already. To add {p.id} to it, follow formalize-math-paper\'s '
                         'references/multi-paper.md by hand (CONVENTIONS, Section 3): this script only '
                         'starts a repository')
    if notes.exists() or notes.is_symlink():
        raise SystemExit(f'{notes} exists already')
    if not private_root.is_dir():
        raise SystemExit(f'no private repository at {private_root} (use --private-root)')
    seed = (args.seed or c.path(p.hub)).resolve()

    reqs, cannot = requirements(c, p)
    print(f'{p.repo}: {p.cite}, "{p.title}"')
    print(f'  hub           {p.hub}')
    print(f'  root          {p.root}/   (package {p.root})')
    print(f'  paper         {p.paper}   (namespace {p.paper}; Challenge palomar/{p.paper}/, namespace '
          f'{p.paper}Challenge' + ('; the entry\'s `paper`' if p.paper_given else '; the root') + ')')
    others = [q.id for q in c.papers if q.repo == p.repo and q is not p]
    if others:
        print(f'  shares        {p.repo} with {", ".join(others)}: they join it later, by hand, and this '
              "paper's code then moves (references/multi-paper.md, Section 9)")
    print(f'  train         {c.train["lean"]}, Mathlib {c.train["mathlib"]}')
    for r in reqs:
        print(f'  requires      {r["name"]} at {r["rev"][:7]} ({r["url"]})')
    for d in cannot:
        print(f'  builds on     {d} ({c.paper(d).status}): not required; see notes/config.md')
    print(f'  repository    {repo}')
    print(f'  private files {notes}')
    print(f'  dependencies  {"lake update + lake exe cache get" if args.no_seed else f"hard-linked from {seed}"}')
    if args.dry_run:
        return

    hub = c.repo(p.hub)
    values = {
        'id': p.id, 'repo': p.repo, 'notes_folder': f'papers/{col.paper_folder(p.hub)}/{p.repo}', 'root': p.root, 'paper': p.paper, 'cite': p.cite,
        'authors': p.authors, 'title': p.title, 'year': p.year, 'url': p.url, 'lean': c.train['lean'],
        'mathlib': c.train['mathlib'], 'date': datetime.date.today().isoformat(),
        'hub': p.hub, 'hub_url': hub['url'], 'hub_title': hub.get('title', p.hub),
        'root_path': str(col.ROOT), 'catalog_path': str(c.catalogs[p.hub]),
        'conventions_path': str(col.ROOT / 'docs' / 'CONVENTIONS.md'),
        'description': f'A Lean 4 formalization of {p.authors} {p.year}, {p.title}'.replace('"', '\\"'),
        'requires': requires_block(c, reqs),
        'libraries': wrap('; '.join([f'{r["name"]} at {r["rev"][:7]} ({r["url"]})' for r in reqs]
                                    + ['nothing in the Challenge but Mathlib'])),
        'earlier': wrap('; '.join([f'{cov["repo"]}: {cov["what"]}' for cov in p.covered_by]
                                  or ['none in the collection']) + '; search for others (Phase 0)'),
        'siblings': siblings_text(c, p, cannot),
    }

    print('Writing the repository')
    # Lake fails on a glob whose directory, or a root whose file, does not exist: the scaffold
    # creates each.
    for d in (f'{p.root}/Basic', f'{p.root}/External', f'palomar/{p.paper}', f'docs/{p.paper}',
              '.github/workflows'):
        (repo / d).mkdir(parents=True)
    files = {
        'lakefile.toml': 'lakefile.toml.in', '.gitignore': 'gitignore.in', 'README.md': 'README.md.in',
        '.github/workflows/lean_action_ci.yml': 'lean_action_ci.yml.in',
        f'{p.root}/Basic/README.md': 'Basic-README.md.in',
        f'{p.root}/External/README.md': 'External-README.md.in',
        f'{p.root}/Defs.lean': 'Defs.lean.in',
        f'palomar/{p.paper}/Challenge.lean': 'Challenge.lean.in',
        f'palomar/{p.paper}/Solution.lean': 'Solution.lean.in',
    }
    for out, template in files.items():
        (repo / out).write_text(render(TEMPLATES / template, values))
    (repo / 'lean-toolchain').write_text(c.train['lean'] + '\n')
    shutil.copyfile(col.ROOT / 'LICENSE', repo / 'LICENSE')

    print('Writing the private files')
    templates = folder / 'templates'
    (notes / 'notes').mkdir(parents=True)
    (notes / '.vscode').mkdir()
    (notes / 'notes' / 'config.md').write_text(render(templates / 'config.md.in', values))
    (notes / 'notes' / 'follow-up-papers.md').write_text(render(templates / 'follow-up-papers.md.in', values))
    (notes / 'CLAUDE.md').write_text(render(templates / 'CLAUDE.md.in', values))
    shutil.copyfile(templates / 'vscode-settings.json', notes / '.vscode' / 'settings.json')
    links = {'notes': 'notes', '.vscode': '.vscode', 'CLAUDE.md': 'CLAUDE.md'}
    for at, name in links.items():
        os.symlink(os.path.relpath(notes / name, (repo / at).parent), repo / at)

    print('Setting up the dependencies')
    inherited: list[dict] = []
    if args.no_seed:
        run(['lake', 'update'], cwd=repo)
        run(['lake', 'exe', 'cache', 'get'], cwd=repo)
    else:
        inherited = seed_packages(c, p.root, reqs, seed, repo)

    if not args.no_build:
        print('Building')
        run(['lake', 'build'], cwd=repo)
        for r in reqs + inherited:
            if r['local'] is None:
                target = '+Phylogenetics.Network.Defs:olean'
            else:
                target = f'@{r["name"]}'
            out = run(['lake', 'build', '--no-build', target], cwd=repo, check=False)
            if out.returncode != 0:
                print(f'  ! {r["name"]} is not up to date: the first build that imports it rebuilds it')

    if not args.no_commit:
        print('Committing')
        run(['git', 'init', '--quiet', '-b', 'main'], cwd=repo)
        run(['git', 'add', '-A'], cwd=repo)
        message = (f'Start the project from the templates of lean4-phylogenetics\n\n'
                   f'{p.cite}, {p.url}. A paper of the hub {p.hub}. Root {p.root}, paper {p.paper}; '
                   f'Lean and Mathlib {c.train["mathlib"]}; '
                   + ', '.join(f'{r["name"]} at {r["rev"][:7]}' for r in reqs) + '.\n')
        if args.trailer:
            message += '\n' + '\n'.join(args.trailer) + '\n'
        run(['git', 'commit', '--quiet', '-m', message], cwd=repo)

    if not args.keep_status and p.status in ('todo', 'partial'):
        col.set_status(c, p.id, 'in-progress')
        print(f'Marked {p.id} in-progress in {c.catalogs[p.hub]} (run scripts/status.py readme --write)')

    print(f'\nNext:\n  cd {repo}\n  claude\n  /formalize-math-paper {p.url}')


if __name__ == '__main__':
    main()
