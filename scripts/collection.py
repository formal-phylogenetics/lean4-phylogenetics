"""The collection of Lean formalizations rooted at lean4-phylogenetics.

The collection is a tree of repositories. Its root, lean4-phylogenetics, holds the library that
everything shares, the registry of the repositories (collection/repos.toml), the shared foundations
(collection/foundations.toml), the conventions and the tools. Each hub holds a library of what its
papers share, and a catalog of its papers (catalog/papers.toml). A hub's parent is the root or another
hub, of which it is a sub-hub: lean4-tob is a sub-hub of lean4-phylo-network. The repositories sit
side by side in one directory, the workspace.

Imported by scripts/status.py and scripts/new_paper.py. Python 3.11 or later.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # this repository
COLLECTION = ROOT / 'collection'
WORKSPACE = ROOT.parent
GITHUB_OWNER = 'vltanh'

STATUSES = ('formalized', 'in-progress', 'partial', 'todo')
KINDS = ('theory', 'theory+algorithm', 'method')
ROLES = ('root', 'hub', 'paper', 'background', 'tool')
# Generic module roots that older repositories use and that no new repository may use: Lean module
# names are global, and the repositories of the collection import one another.
RESERVED_ROOTS = {'Basic', 'External', 'Challenge', 'Solution', 'MainResults', 'Main', 'Defs'}


@dataclass
class Paper:
    id: str
    family: int
    order: int
    authors: str
    year: str
    title: str
    url: str
    kind: str
    root: str
    status: str
    hub: str = ''
    paper: str = ''         # the paper's name, if not its root (docs/CONVENTIONS.md, Section 2)
    short: str = ''
    repo: str = ''
    commit: str = ''
    uses: list[str] = field(default_factory=list)
    builds_on: list[str] = field(default_factory=list)
    covered_by: list[dict] = field(default_factory=list)
    note: str = ''

    def __post_init__(self):
        if not self.repo:
            self.repo = f'lean4-{self.id}'
        self.paper_given = bool(self.paper)   # whether the entry states `paper`
        if not self.paper:
            self.paper = self.root

    @property
    def path(self) -> Path:
        return WORKSPACE / self.repo

    @property
    def github(self) -> str:
        return f'https://github.com/{GITHUB_OWNER}/{self.repo}'

    @property
    def cite(self) -> str:
        base = f'{self.authors} {self.year}'
        return f'{self.short} ({base})' if self.short else base


@dataclass
class Collection:
    train: dict
    repos: list[dict]
    foundations: list[dict]
    families: dict[tuple[str, int], dict] = field(default_factory=dict)
    papers: list[Paper] = field(default_factory=list)
    catalogs: dict[str, Path] = field(default_factory=dict)   # hub -> its catalog, if on disk
    subhubs: dict[str, list[dict]] = field(default_factory=dict)   # hub -> the [[subhub]] of its catalog

    @property
    def by_id(self) -> dict[str, Paper]:
        return {p.id: p for p in self.papers}

    @property
    def hubs(self) -> list[dict]:
        return [r for r in self.repos if r.get('role') == 'hub']

    def paper(self, pid: str) -> Paper:
        try:
            return self.by_id[pid]
        except KeyError:
            raise SystemExit(f'no paper {pid!r} in the catalogs of the hubs') from None

    def repo(self, name: str) -> dict | None:
        return next((r for r in self.repos if r['name'] == name), None)

    def in_family(self, hub: str, fid: int) -> list[Paper]:
        return sorted((p for p in self.papers if p.hub == hub and p.family == fid), key=lambda p: p.order)

    def lean_version(self) -> str:
        return self.train['lean'].split(':', 1)[1]

    def on_train(self, repo: str) -> bool:
        r = self.repo(repo)
        return r is None or r.get('lean', self.lean_version()) == self.lean_version()

    def library_repos(self) -> list[dict]:
        """The root and the hubs: the nodes of the tree that hold a library, in the order of the
        tree (each hub after the hub above it)."""
        out: list[dict] = []

        def visit(parent: str) -> None:
            for r in self.repos:
                if r.get('role') == 'hub' and r.get('parent') == parent and r not in out:
                    out.append(r)
                    visit(r['name'])

        for r in self.repos:
            if r.get('role') == 'root':
                out.append(r)
                visit(r['name'])
        return out + [r for r in self.repos if r.get('role') in ('root', 'hub') and r not in out]

    def hubs_above(self, name: str) -> list[dict]:
        """The hubs above a hub or a paper's hub, from the top of the tree down to `name` itself if it
        is a hub: the libraries that a repository under `name` requires besides the root's."""
        chain: list[dict] = []
        r = self.repo(name)
        while r is not None and r.get('role') == 'hub' and r not in chain:
            chain.append(r)
            r = self.repo(r.get('parent', ''))
        return chain[::-1]

    def depth(self, hub: dict) -> int:
        """0 for a hub under the root, 1 for its sub-hubs, and so on."""
        return len(self.hubs_above(hub['name'])) - 1

    def validate(self) -> list[str]:
        errors = []
        names = [r['name'] for r in self.repos]
        for r in self.repos:
            where = f"repository {r.get('name')!r}"
            if r.get('role') not in ROLES:
                errors.append(f"{where}: role {r.get('role')!r} is not one of {ROLES}")
            if r.get('role') in ('hub', 'paper', 'background') and r.get('parent') not in names:
                errors.append(f"{where}: its parent {r.get('parent')!r} is not in the registry")
            if r.get('role') == 'hub':
                above = self.repo(r.get('parent', ''))
                if above is not None and above.get('role') not in ('root', 'hub'):
                    errors.append(f"{where}: the parent of a hub is the root or a hub, not {above['name']}")
                seen_up, up = set(), r
                while up is not None and up.get('role') == 'hub':
                    if up['name'] in seen_up:
                        errors.append(f"{where}: the parents of the hubs form a cycle")
                        break
                    seen_up.add(up['name'])
                    up = self.repo(up.get('parent', ''))
            if r.get('role') in ('root', 'hub') and r.get('package') not in self.train.get('pins', {}):
                errors.append(f"{where}: [train.pins] has no commit of its library {r.get('package')!r}")
        if len(set(names)) != len(names):
            errors.append('the registry lists a repository twice')
        hubs = {h['name'] for h in self.hubs}
        # The roots of the repositories, by owner: each package of the registry, and each paper's.
        # Papers that share a repository share its root.
        packages = {r['package']: r['name'] for r in self.repos if r.get('package')}
        roots = {p.root: p.repo for p in self.papers} | packages
        seen_id: dict[str, str] = {}
        seen_root: dict[str, str] = {}            # root -> repository
        seen_paper: dict[str, Paper] = {}         # an explicit `paper` -> its entry
        for p in self.papers:
            where = f'paper {p.id!r} ({p.hub})'
            if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', p.id):
                errors.append(f'{where}: an id is lower case letters, digits and hyphens')
            # The root, and the paper's name when the entry states one; by default it is the root.
            for key in ('root', 'paper') if p.paper_given else ('root',):
                value = getattr(p, key)
                if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', value):
                    errors.append(f'{where}: {key} {value!r} is not a capitalized ASCII Lean identifier')
                if value in RESERVED_ROOTS:
                    errors.append(f'{where}: {key} {value!r} is reserved')
            if packages.get(p.root, p.repo) != p.repo:
                errors.append(f'{where}: root {p.root!r} is the package of {packages[p.root]}')
            # The Palomar library's modules are <paper>.Challenge and <paper>.Solution: they may be
            # under the repository's own root, never under another's.
            if roots.get(p.paper, p.repo) != p.repo:
                errors.append(f'{where}: paper {p.paper!r} is the root of {roots[p.paper]}')
            if p.id in seen_id:
                errors.append(f'{where}: id {p.id!r} is also that of a paper of {seen_id[p.id]}')
            seen_id[p.id] = p.hub
            if seen_root.setdefault(p.root, p.repo) != p.repo:
                errors.append(f'{where}: root {p.root!r} is also that of {seen_root[p.root]}')
            if p.paper_given:
                other = seen_paper.setdefault(p.paper, p)
                if other.repo != p.repo:   # within a repository, the check below reports it
                    errors.append(f'{where}: paper {p.paper!r} is also that of {other.id!r}')
            if p.status not in STATUSES:
                errors.append(f'{where}: status {p.status!r} is not one of {STATUSES}')
            if p.kind not in KINDS:
                errors.append(f'{where}: kind {p.kind!r} is not one of {KINDS}')
            if (p.hub, p.family) not in self.families:
                errors.append(f'{where}: no family {p.family} in its hub')
            if p.status == 'formalized' and not re.fullmatch(r'[0-9a-f]{40}', p.commit):
                errors.append(f'{where}: a formalized paper needs the full hash of its commit')
            if p.status == 'partial' and not p.covered_by:
                errors.append(f'{where}: a partial paper says what covers it (covered_by)')
            for h in p.uses:
                if h not in hubs:
                    errors.append(f'{where}: uses {h!r}, which is not a hub')
            for dep in p.builds_on:
                if dep not in self.by_id:
                    errors.append(f'{where}: builds_on names an unknown paper {dep!r}')
            for cov in p.covered_by:
                if set(cov) != {'repo', 'what'}:
                    errors.append(f'{where}: each covered_by entry has exactly `repo` and `what`')
        # A repository with several papers (formalize-math-paper, references/multi-paper.md): one
        # root, and a name of its own for each paper, at most one of them the default, the root.
        by_repo: dict[str, list[Paper]] = {}
        for p in self.papers:
            by_repo.setdefault(p.repo, []).append(p)
        for repo, ps in by_repo.items():
            if len({q.root for q in ps}) > 1:
                errors.append(f'repository {repo}: its papers share its root, but their entries give '
                              + ', '.join(f'{q.root!r} ({q.id})' for q in ps))
            names: dict[str, str] = {}
            for q in ps:
                if q.paper in names:
                    errors.append(f'repository {repo}: papers {names[q.paper]!r} and {q.id!r} have the '
                                  f'same name {q.paper!r}; each paper of a repository has its own `paper` '
                                  '(at most one leaves it to the root)')
                names.setdefault(q.paper, q.id)
        # A hub's catalog lists its sub-hubs, which the registry places under it.
        for hub, listed in self.subhubs.items():
            names_listed = {x.get('repo') for x in listed}
            below = {h['name'] for h in self.hubs if h.get('parent') == hub}
            for x in sorted(names_listed - below):
                errors.append(f'catalog of {hub}: lists the sub-hub {x!r}, whose parent in the registry is not {hub}')
            for x in sorted(below - names_listed):
                errors.append(f'catalog of {hub}: does not list its sub-hub {x!r} ([[subhub]])')
        cycle = find_cycle({p.id: p.builds_on for p in self.papers})
        if cycle:
            errors.append('builds_on has a cycle: ' + ' -> '.join(cycle))
        for f in self.foundations:
            if f.get('status') not in ('available', 'partial', 'missing'):
                errors.append(f"foundation {f.get('id')!r}: bad status {f.get('status')!r}")
        for key in ('lean', 'mathlib', 'pins'):
            if key not in self.train:
                errors.append(f'[train] has no {key!r}')
        return errors


def find_cycle(graph: dict[str, list[str]]) -> list[str]:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(n):
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if state.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if m in graph and state.get(m) is None:
                found = visit(m)
                if found:
                    return found
        stack.pop()
        state[n] = 2
        return []

    for n in graph:
        if state.get(n) is None:
            found = visit(n)
            if found:
                return found
    return []


def _toml(path: Path) -> dict:
    with open(path, 'rb') as f:
        return tomllib.load(f)


def private_folder() -> Path | None:
    """This repository's private folder, where its gitignored `notes` link points; None without it."""
    link = ROOT / 'notes'
    return link.resolve().parent if link.is_symlink() else None


def load(private: bool = False, hubs_from: Path | None = None) -> Collection:
    """The registry, the foundations, and the catalog of every hub found in the workspace. With
    `private`, the private overlay (catalog-private.toml in the private folder) is merged in: it
    holds what the public files must not say. READMEs are rendered without it."""
    reg = _toml(COLLECTION / 'repos.toml')
    c = Collection(train=reg.get('train', {}), repos=reg.get('repo', []),
                   foundations=_toml(COLLECTION / 'foundations.toml').get('foundation', []))
    overlay = {}
    folder = private_folder()
    if private and folder and (folder / 'catalog-private.toml').exists():
        overlay = _toml(folder / 'catalog-private.toml')
        c.repos += overlay.get('repo', [])
    workspace = hubs_from or WORKSPACE
    for hub in c.hubs:
        path = workspace / hub['name'] / 'catalog' / 'papers.toml'
        if not path.exists():
            continue
        c.catalogs[hub['name']] = path
        data = _toml(path)
        for f in data.get('family', []):
            c.families[(hub['name'], f['id'])] = f
        c.subhubs[hub['name']] = data.get('subhub', [])
        for p in data.get('paper', []):
            c.papers.append(Paper(hub=hub['name'], **p))
    for o in overlay.get('paper', []):
        p = c.by_id.get(o['id'])
        if p:
            for k, v in o.items():
                setattr(p, k, v)
            if 'paper' in o:
                p.paper_given = True
            elif not p.paper_given:
                p.paper = p.root
    return c


def set_field(c: Collection, pid: str, key: str, value: str, after: str = 'root') -> None:
    """Set one string field of a paper in its hub's catalog, leaving the rest of the file as it is:
    its line is replaced, or, if the entry has none, added after the line of `after`."""
    p = c.paper(pid)
    path = c.catalogs[p.hub]
    lines = path.read_text().splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.strip() == f'id = "{pid}"'), None)
    if start is None:
        raise SystemExit(f'no paper {pid!r} in {path}')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('[[')), len(lines))
    line = f'{key} = "{value}"\n'
    for i in range(start + 1, end):
        if re.match(rf'{key}\s*=', lines[i]):
            lines[i] = line
            break
    else:
        at = next((i for i in range(start + 1, end) if re.match(rf'{after}\s*=', lines[i])), None)
        if at is None:
            raise SystemExit(f'paper {pid!r} has no {key} line and no {after} line in {path}')
        lines.insert(at + 1, line)
    path.write_text(''.join(lines))
    setattr(p, key, value)


def set_status(c: Collection, pid: str, status: str) -> None:
    """Change one paper's `status` line in its hub's catalog, leaving the rest of the file as it is."""
    assert status in STATUSES
    set_field(c, pid, 'status', status)
