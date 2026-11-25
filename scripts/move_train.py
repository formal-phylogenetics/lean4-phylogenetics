#!/usr/bin/env python3
"""Move papers' repositories onto the train, each in one step.

    python3 scripts/move_train.py                  # the papers' repositories behind the train
    python3 scripts/move_train.py ID...            # move these papers' repositories
    python3 scripts/move_train.py --behind         # move every one that is behind and can move
    python3 scripts/move_train.py ... --dry-run    # print the plan and stop

A repository is behind when its toolchain is not the train's Lean, or its lakefile does not require
the train's Mathlib and the train's pins of the root, of the hubs above it and of the hubs it uses.
A repository on the train that does not require a formalized paper it builds on is listed, and
moves only when named.

Moving a repository writes the train's toolchain, and into its lakefile what scripts/new_paper.py
would require today: those pins, and the formalized papers it builds on, on the train. It seeds
.lake/packages again by hard links from its hub's checkout, which must be on the train, and writes
the manifest; checks with `lake build --no-build` that every dependency is up to date BEFORE
anything builds, since a rebuild would write into files that other checkouts share; builds with
--wfail; refreshes the `libraries` and the papers of the catalog in its private configuration; and
commits the toolchain, the lakefile and the manifest. Nothing is pushed.

It moves only the repositories of papers in progress, with a clean working tree. A formalized
paper's repository moves by hand, since its audit and its Comparator run again
(docs/WORKFLOW.md, Section 7); a repository with uncommitted work moves in the session that owns it.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib

import collection as col
import new_paper as np

LIBRARIES = {'Phylogenetics': 'lean4-phylogenetics'}


def sh(cmd: list, cwd, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run([str(x) for x in cmd], cwd=cwd, text=True, capture_output=True)
    if check and r.returncode:
        raise SystemExit(f'{cwd}: {" ".join(map(str, cmd))} failed:\n{r.stdout}{r.stderr}')
    return r


def current(repo) -> dict[str, str]:
    """The requirements of a repository's lakefile, by name, with their revisions (Mathlib's tag)."""
    conf = tomllib.loads((repo / 'lakefile.toml').read_text())
    return {r['name']: r.get('rev', '') for r in conf.get('require', [])}


def state(c: col.Collection, p: col.Paper) -> tuple[str, list[dict], list[str]]:
    """Whether the repository of `p` is behind, and why it cannot move if it cannot."""
    repo = p.path
    reqs, cannot = np.requirements(c, p)
    if not (repo / 'lakefile.toml').is_file():
        return 'absent', reqs, cannot
    want = {r['name']: r['rev'] for r in reqs} | {'mathlib': c.train['mathlib']}
    have = current(repo)
    toolchain = (repo / 'lean-toolchain').read_text().strip() == c.train['lean']
    if have == want and toolchain:
        return 'on the train', reqs, cannot
    libraries = {h['package'] for h in c.library_repos()} | {'mathlib'}
    if toolchain and all(have.get(n) == rev for n, rev in want.items() if n in libraries):
        missing = sorted(n for n in want if n not in libraries and have.get(n) != want[n])
        if missing:
            return (f'on the train; does not require {", ".join(missing)} (builds_on) at its commit: '
                    'its own session adds it, or name it here'), reqs, cannot
        return 'on the train', reqs, cannot
    if p.status == 'formalized':
        return 'behind; formalized: moves by hand (WORKFLOW, Section 7)', reqs, cannot
    if sh(['git', 'status', '--porcelain', '--untracked-files=no'], repo).stdout.strip():
        return 'behind; uncommitted work: moves in its own session', reqs, cannot
    return 'behind', reqs, cannot


def move(c: col.Collection, p: col.Paper, reqs: list[dict], cannot: list[str]) -> str:
    repo = p.path
    lf = repo / 'lakefile.toml'
    text = lf.read_text()
    # Every [[require]] block, from the root's comment to the end of Mathlib's, whatever its tag.
    start = text.index('# The root of the collection')
    end = re.compile(r'name = "mathlib"\n(?:[^\n\[]*\n)*?rev = "[^"]*"\n').search(text, start).end()
    lf.write_text(text[:start] + np.requires_block(c, reqs) + text[end:])
    (repo / 'lean-toolchain').write_text(c.train['lean'] + '\n')
    shutil.rmtree(repo / '.lake' / 'packages', ignore_errors=True)
    inherited = np.seed_packages(c, p.root, reqs, (col.WORKSPACE / p.hub).resolve(), repo)
    stale = [r['name'] for r in reqs + inherited
             if sh(['lake', 'build', '--no-build',
                    '+Phylogenetics.Network.Defs:olean' if r['local'] is None else f'@{r["name"]}'],
                   repo, check=False).returncode]
    if stale:
        raise SystemExit(f'{p.repo}: {", ".join(stale)} not up to date in the seeded packages: stopped '
                         'before building, with the move uncommitted (build the seed\'s checkout first)')
    if sh(['lake', 'build', '--wfail'], repo, check=False).returncode:
        raise SystemExit(f'{p.repo}: the build fails on the train: the move is left uncommitted to fix '
                         'there (git checkout lakefile.toml lake-manifest.json undoes it)')

    folder = col.private_folder()
    config = folder.parent / p.repo / 'notes' / 'config.md' if folder else None
    if config and config.is_file():
        cfg = config.read_text()
        libs = np.wrap('; '.join([f'{r["name"]} at {r["rev"][:7]} ({r["url"]})' for r in reqs]
                                 + ['nothing in the Challenge but Mathlib']))
        cfg = re.sub(r'^libraries:.*?(?=^packages:)', 'libraries:' + ' ' * 8 + libs + '\n', cfg,
                     count=1, flags=re.S | re.M)
        head = '## Papers of the catalog this one may use\n\n'
        if head in cfg:
            i = cfg.index(head) + len(head)
            j = cfg.find('\n## ', i)
            cfg = cfg[:i] + np.siblings_text(c, p, cannot) + '\n' + (cfg[j:] if j >= 0 else '')
        config.write_text(cfg)

    hubs = {h['package']: h['name'] for h in c.library_repos()}
    named = [r for r in reqs if r['name'] in hubs]
    papers = [r for r in reqs if r['name'] not in hubs]
    pins = ', '.join(f'{hubs[r["name"]]} {r["rev"][:7]}' for r in named)
    body = f"Requires, by full commit, the train's pins: {pins}."
    for r in papers:
        q = next(x for x in c.papers if x.root == r['name'])
        body += (f' It also requires {q.repo} {r["rev"][:7]}, {q.cite}, which this paper builds on and '
                 'which is formalized')
        subs = [x for x in inherited if x['name'] not in hubs]
        if subs:
            body += ', with ' + ', '.join(f'{x["url"].rsplit("/", 1)[-1]} {x["rev"][:7]}' for x in subs)
        body += '.'
    body += ' The build passes.'
    message = (f'Move to the train: {pins}\n\n{textwrap.fill(body, 100)}\n\n'
               'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n')
    sh(['git', 'add', 'lakefile.toml', 'lake-manifest.json', 'lean-toolchain'], repo)
    subprocess.run(['git', 'commit', '-q', '-F', '-'], cwd=repo, input=message, text=True, check=True)
    return sh(['git', 'rev-parse', '--short', 'HEAD'], repo).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('ids', nargs='*', help="papers' ids in their hubs' catalogs")
    ap.add_argument('--behind', action='store_true', help='every repository that is behind and can move')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    c = col.load(private=True)
    errors = c.validate()
    if errors:
        raise SystemExit('the catalogs have errors; run scripts/status.py check')
    # One entry per repository: the first paper of a shared one.
    papers = list({p.repo: p for p in reversed(c.papers)}.values())[::-1]
    if args.ids:
        papers = [c.paper(i) for i in args.ids]
    rows = [(p, *state(c, p)) for p in papers]
    rows = [r for r in rows if r[1] != 'absent']
    if not args.ids and not args.behind:
        for p, st, reqs, _ in rows:
            if st != 'on the train':
                print(f'{p.repo:32} {st}')
        return
    for p, st, reqs, cannot in rows:
        if args.ids and st.startswith('on the train; does not require'):
            st = 'behind'
        if st != 'behind':
            print(f'{p.repo:32} {st}{"" if st == "on the train" else ": skipped"}')
            continue
        print(f'{p.repo:32} -> ' + ', '.join(f'{r["name"]}@{r["rev"][:7]}' for r in reqs))
        if not args.dry_run:
            print(f'{"":32}    committed {move(c, p, reqs, cannot)}')


if __name__ == '__main__':
    main()
