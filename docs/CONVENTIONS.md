# Conventions of the collection

These rules apply to every repository of the collection of Lean formalizations rooted at
lean4-phylogenetics. An agent that formalizes a paper of the collection with the
formalize-math-paper skill reads them first. Where these rules and the skill's defaults differ,
these rules apply. The skill's rules on statements, faithful proofs, cited results, permissions,
credit and honest reporting apply unchanged.

## Contents

1. The tree of repositories
2. Names
3. Layout of a paper's repository, and of a hub
4. Where code goes
5. Versions: the train
6. Requiring another repository
7. Private files
8. Publishing
9. When a paper is done

## 1. The tree of repositories

The collection is a tree. Each node holds a Lean library of what the repositories below it share:

| Node | Repository | Library | Holds |
| --- | --- | --- | --- |
| Root | [lean4-phylogenetics](https://github.com/vltanh/lean4-phylogenetics) | `Phylogenetics` | what every repository shares; also the registry, the foundations, these conventions, the workflow and the tools |
| Hub | [lean4-tob](https://github.com/vltanh/lean4-tob) | `TreeOfBlobs` | what the papers on the tree of blobs share; their catalog; the overview of their field |
| Hub | [lean4-phylo-network](https://github.com/vltanh/lean4-phylo-network) | `PhyloNetwork` | what the papers on network estimation share; their catalog |
| Paper | `lean4-<id>` | `<Root>` | one paper of a hub's catalog |

A hub may have sub-hubs in the same way. The registry, [`collection/repos.toml`](../collection/repos.toml),
lists the root, the hubs and the repositories that need a note; each hub's `catalog/papers.toml`
lists its papers.

What may require what:

- A paper's repository requires the root library and its hub's library, always, at the train's
  pins (Section 5); the libraries of the other hubs it uses (`uses` in its catalog entry); and the
  repositories of the papers whose results its proofs use (`builds_on`), in any hub.
- A hub's library requires the root library, and may require another hub's library or a paper's
  repository that is not below it. A library never requires a repository below it: a hub cannot
  require its own papers, and nothing can require the root's dependents.
- Requirements never form a cycle. `scripts/status.py check` checks the pins and the module names.

Older repositories have restrictions, recorded in the registry and checked by
`scripts/status.py check`: lean4-camus, lean4-adr11 and lean4-gusfield2007 use generic top-level
modules (`Challenge`, `Solution`, `External`, `MainResults`), which no other repository may use, and
lean4-camus requires lean4-adr11 rather than the root library.

## 2. Names

- **Repository** `lean4-<id>`, where `<id>` is the paper's id in its hub's catalog: the method's
  name in lower case when the paper names one (`snaq`, `nanuq-plus`), otherwise first author and
  year (`banos2019`), with a keyword when two papers would share it (`holtgrefe2025-level2`). Ids
  are unique across all hubs.
- **Lake package, module root and namespace** `<Root>`, the catalog's `root` (`Snaq`, `NanuqPlus`,
  `Banos2019`). The Challenge's namespace is `<Root>Challenge`. A hub's package names its library
  (`TreeOfBlobs`, `PhyloNetwork`).
- **Every module** of a repository is under its root, `<Root>/`, except `<Root>Challenge` and
  `<Root>Solution`. No repository has a top-level `Basic`, `External`, `Challenge`, `Solution`,
  `MainResults` or `Defs`: Lean module names are global, and the repositories of the collection
  import one another. The skill's single-paper layout puts `Basic/`, `External/` and
  `Challenge.lean` at the top; here they move under the root (Section 3).
- **Labels.** Docstrings carry the paper's TeX labels as the skill says
  (``**Theorem 1.2** (`thm:main`).``). A result of another repository restated in
  `<Root>/External/` carries the label of its row in `docs/paper_routes.tsv`, prefixed with that
  repository's id (``(`nanuq:thm:36`)``), so that it cannot collide with this paper's labels.
- **Kept names.** The repositories split out of lean4-tob on 2026-11-21 kept every declaration's
  name, so some declarations live outside their repository's namespace: the main results in
  `TreeOfBlobs`, NANUQ's in `External.AllmanBanosRhodes2019`, some of `TreeOfBlobs`'s in
  `TOBQMC.Level1` or `ECToBlob`. Renaming them is a change of its own, with deprecated aliases.

## 3. Layout of a paper's repository, and of a hub

`scripts/new_paper.py` creates the files marked *scaffold*; the skill writes the rest.

```text
lakefile.toml, lean-toolchain, lake-manifest.json    scaffold: on the train (Section 5)
LICENSE                                              scaffold: Apache-2.0
README.md                                            scaffold stub; rewritten in the skill's Phase 8
.gitignore                                           scaffold: ignores .lake and the private files (Section 7)
.github/workflows/lean_action_ci.yml                 scaffold: build only; the skill adds its checks
<Root>/Basic/            general mathematics, in Mathlib's namespaces (the skill's Basic/)
<Root>/External/<Src>/   cited results, namespace External.<Src>, each with a README.md (the skill's External/)
<Root>/Defs.lean         every definition the Challenge uses, between the sync markers
<Root>/<Section>/…       the paper's library, in the namespace <Root>, by section
<Root>Challenge.lean     module <Root>Challenge: the statements of record; imports only Mathlib
<Root>Solution.lean      module <Root>Solution: their proofs; the library's entry point
comparator.json          "challenge_module": "<Root>Challenge", "solution_module": "<Root>Solution"
formalization.yaml, REPORT.md, CREDITS.md
docs/paper_routes.tsv, docs/route_differences.tsv
scripts/Audit.lean and the skill's other tools
```

The lakefile has one `lean_lib` `<Root>` (`globs = ["<Root>.+"]`) and the libraries
`<Root>Challenge` and `<Root>Solution`. The skill's layering still holds, and is checked in
review: `<Root>/Basic/` imports only Mathlib; `<Root>/External/` imports Mathlib, `Basic` and the
libraries this repository requires; the paper's library imports anything below it;
`<Root>/Defs.lean` and the Challenge import only Mathlib. Where the skill's tools and CI name the
library roots `PaperName External Basic`, use the one root `<Root>`. The audit covers the
repositories that this one requires too (its `import all` lines include their modules, and CI
builds their libraries first), so that one run checks every axiom that a result depends on.

A hub has its library under `<Package>/` (with a README that says what is there and why), its
catalog `catalog/papers.toml`, its README (whose tables `scripts/status.py` generates from the
catalog), and, for a field with formalized papers, an overview of the field in `docs/`.

## 4. Where code goes

The rule: **a definition or result goes to the lowest node of the tree above every repository
that uses it.**

| What | Where |
| --- | --- |
| A result of this paper | this repository |
| What two papers or more of one hub use | that hub's library |
| What papers of several hubs use, or a definition or result that textbooks state | the root library, `Phylogenetics`, acknowledged to its source |
| General mathematics | `<Root>/Basic/` (or the hub's `ForMathlib/`); later Mathlib, or `Phylogenetics/ForMathlib/` |
| A result of a source outside the catalogs that the paper cites | `<Root>/External/<Src>/`, unless a repository of the collection formalizes it already: then require that repository and prove this statement from its theorem |
| A result of a paper of a catalog whose repository does not exist yet | `<Root>/External/<Src>/`, stated in the source's terms and proved (the skill's Stage 2). Note it in that paper's entry (`covered_by`), so that its repository starts from it |
| A result of a paper of a catalog that is formalized, on the train | require its repository (Section 6) |

A paper's theorem that several repositories use is a foundation (Baños 2019's concordance factors
of level-1 cycles, Theorem 5.1 of Huber et al. 2025): it goes up the tree like any other shared
result, acknowledged to the paper, and the paper's own repository imports it and reports it as
formalized there. When a second repository needs something that lives lower, move it up: to the
lowest node above both, under that node's names, leaving deprecated aliases for the old names.

Before defining anything, search Mathlib, the root library, the hubs' libraries and the
repositories that this one requires, in their pinned sources under `.lake/packages`. Do not define
a second version of a notion the collection has. When the paper's definition differs, state the
paper's in its own terms and prove the bridge (the skill's principle "Representation choices need
bridges"). [`collection/foundations.toml`](../collection/foundations.toml) lists what the libraries
hold and lack, and where each missing foundation belongs. Building a foundation that several papers
need is worth proposing to the maintainer in its home from the start, rather than inside one
paper's repository. The maintainer decides.

The Challenge is the exception to reuse: Palomar accepts only Lean, Mathlib, Tau Ceti and CSLib in
a Challenge's imports. So `<Root>/Defs.lean` restates in Mathlib's vocabulary every definition that
the Challenge needs, even those that a library of the collection has, and the library proves that
the two agree.

## 5. Versions: the train

Repositories that require one another must share one Lean and one Mathlib release, and one commit
of each library of the tree. The train is the `[train]` table of the registry: the Lean and Mathlib
release, and in `[train.pins]` the commit of each library (`Phylogenetics`, `TreeOfBlobs`,
`PhyloNetwork`, …).

- A new repository uses the train, not the newest Lean release (which the skill's Phase 0 would
  otherwise choose). It gets the train from `scripts/new_paper.py`.
- Requirements are pinned by full commit hash (Mathlib by its release tag). To move one pin, run
  `lake update <Package>` alone, so that Mathlib's pin does not move.
- A library's commits that change no Lean file (its catalog, its documents) do not move its pin.
- No repository leaves the train alone. The train moves as a whole, root first
  (docs/WORKFLOW.md, Section 7).

## 6. Requiring another repository

- Require a paper's repository at the `commit` of its catalog entry, at which it builds and passes
  its audit. While both are local and unpublished, require it by that commit anyway: the scaffold
  seeds `.lake/packages` with a local clone, and the repositories are then pushed upstream first.
- Each result of the other repository that this paper's proofs use is stated in
  `<Root>/External/<Src>/`, in its source's terms, and proved from the other repository's theorem,
  as the skill does for a package it requires (`references/separate-packages.md`, Section 4). The
  report counts it as a cited result, proved, and names the repository and the theorem.
- Its row in `docs/paper_routes.tsv` has `proved = 0` and the prefixed label of Section 2.
- When this paper's `builds_on` changes, update its hub's catalog.

## 7. Private files

Every repository of the collection is public-facing: the root, the hubs and the papers'. What the
skill keeps out of git is private, and stays outside the repository:

| Path in the repository | Holds |
| --- | --- |
| `notes/` | the working notes: the Phase 0 configuration, the inventory, the run log, the TeX source, drafts and scratch |
| `NEXT.md` | the follow-up papers (the skill's Phase 8) |
| `.vscode/` | the editor's settings |
| `CLAUDE.md` | the agent's instructions for the repository |

Each is a symbolic link to a private location, ignored by the repository's `.gitignore` with no
trailing slash (`/notes`, not `/notes/`: a pattern with one does not match a link). The skill's
"untracked `notes/`" is this folder.

- Never commit them, and never put notes on a branch: visibility applies to every branch.
- Nothing committed (code, comments, documents, commit messages, pull request descriptions) says
  where the private files are kept, or quotes them. The public report says only that `NEXT.md`
  exists (the skill's Phase 8).
- Plans and decisions that are not public yet, and repositories that are private, belong with the
  private files, not in the registry or a catalog. The tools merge a private overlay for local
  checks; the READMEs, which are public, are generated without it.

## 8. Publishing

Repositories are created under `github.com/vltanh`. Creating one, pushing, changing its
visibility, opening or closing pull requests, running Palomar's preflight and submitting to Palomar
each need the maintainer's explicit permission, and permission for one is not permission for
another (the skill's Rules). Push in the order of the requirements, upstream first, so that every
pinned commit exists when a repository that requires it is pushed. Each paper is a Palomar
submission of its own.

## 9. When a paper is done

When the skill's completion gates are met:

1. In its hub's catalog, set the entry to `status = "formalized"` with `commit = "<full hash>"`,
   correct its citation, and complete its `builds_on`. Update `covered_by` of the papers whose
   results it formalized in passing.
2. Run `python3 scripts/status.py readme --write` and `python3 scripts/status.py check` here, and
   commit the hub.
3. What another paper will need moves up the tree (Section 4).
4. Repositories that formalized this paper's results in their `External/` may now require it
   instead. This is optional: what they prove is already proved.
