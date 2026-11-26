# Workflow

How a paper of a hub's catalog becomes a finished formalization, and how the collection is kept
together. The rules are in [CONVENTIONS.md](CONVENTIONS.md). The repositories are in one directory,
the workspace: this one and the private repository at its top, the hubs and the libraries under
them in `hubs/`, and the repositories of papers in `papers/`, one folder per hub (`papers/network/`,
`papers/species-tree/`, …, and `papers/background/` for those under no hub). The private files of
each repository are at the same place in the private repository (CONVENTIONS, Section 7). The
commands run from this repository.

## Contents

1. Choose a paper
2. Start its repository
3. Formalize it
4. Finish it
5. Publish it
6. Move shared code up the tree
7. Move the train
8. Keep the registry and the catalogs current

## 1. Choose a paper

```sh
python3 scripts/status.py next
```

lists the open papers hub by hub, family by family, with each paper's state: *ready* when every
paper that its entry says it builds on is formalized, or *waits on* the ones that are not. A paper
that waits can still be done first: what it uses from the earlier paper is then stated and proved in
its `<Root>/External/` (CONVENTIONS, Section 4). But the earlier paper usually costs less to do
first, and then the later one imports it. `builds_on` holds only what was known before each paper's
inventory; the inventory (the skill's Phase 1) completes it.

## 2. Start its repository

```sh
python3 scripts/new_paper.py <id> --dry-run   # the plan: hub, root, paper, requirements, paths
python3 scripts/new_paper.py <id>
```

Start it when its formalization starts, and start one paper at a time: a repository that waits for
its turn has to move with every train (Section 7) with nothing in it. A paper of a catalog that has
no repository loses nothing: its entry keeps its place, its `builds_on` and its `covered_by`, and
`scripts/new_paper.py` creates the repository on the train of the day it starts.

It creates `../lean4-<id>` (or the entry's `repo`) in the layout of CONVENTIONS, Section 3, and its
private files (Section 7). It requires the root library, the libraries of the hubs above the paper
(its hub, and the hubs above a sub-hub), the hubs and libraries it `uses`, and the formalized papers
it builds on, each at its pin, and lists in the manifest
everything they require in turn. It hard-links the compiled dependencies from local checkouts
(Mathlib from the hub's), builds, checks that the dependencies are up to date, makes the first
commit, and marks the paper `in-progress` in its hub's catalog. Nothing is downloaded, pushed or
created on GitHub.

- Papers on one topic may share a repository (CONVENTIONS, Sections 2 and 3). The script starts it
  with the first of them, in the layout of one paper, and refuses a repository that exists: the
  others join it by hand, as the skill's `references/multi-paper.md` says. When the second joins,
  the first paper's code moves to `<Root>/<Root>/` and `<Root>/Common/` (its Section 9); each paper
  then has a library, a submission and a directory of documents, and the README becomes the
  umbrella README. Their entries are then marked `in-progress`.
- `--no-seed` fetches the dependencies instead (`lake update`, `lake exe cache get`).
- `--seed <path>` hard-links Mathlib from another local repository on the train.
- A hard-linked file is shared by two checkouts. Both pin the same commits, so neither should
  ever rebuild a dependency. If a build in the new repository starts compiling Mathlib or a library
  of the collection, stop it, delete its `.lake/packages`, and fetch them with `lake exe cache get`
  there, so that the other checkout's files stay as they were.

Then run `python3 scripts/status.py readme --write`, and commit the hub.

## 3. Formalize it

```sh
cd ../lean4-<id>
claude
```

and in the session:

```text
/formalize-math-paper <the paper's DOI or arXiv link>
```

The scaffold has written the session's instructions (private: CONVENTIONS, Section 7), which import
CONVENTIONS.md and answer the Phase 0 questions that the collection settles. The skill then asks
only what is still open, and its Phase 2 finds the project set up: it adds the paper's sections
under `<Root>/`, general mathematics under `<Root>/Basic/` and the results the paper cites under
`<Root>/External/`.

What to watch for, beyond the skill's own gates:

- **Phase 1.** For each cited result, where its proof can come from: Mathlib, the root library, a
  hub's library, another paper's repository, or nowhere yet. Record the papers that the proofs use
  in `builds_on` in the hub's catalog.
- **Phase 2.** Missing foundations (`collection/foundations.toml`): if another paper will need the
  same definitions, the maintainer decides whether to build them in their home first (Section 6).
- **Phase 3.** The Challenge, `palomar/<Paper>/Challenge.lean`, restates its definitions in
  Mathlib's vocabulary (copied from `<Root>/Defs.lean`), and the library proves the bridges to the
  collection's definitions.
- **Phase 6.** In the audit and in CI, the skill's `ProjectName` is `<Root>` and its `PaperName` is
  `<Paper>`; the audit imports the modules of the required libraries too.

## 4. Finish it

When the skill's completion gates are met, update the hub (CONVENTIONS, Section 9): the entry's
status, commit and citation, `builds_on`, and `covered_by` of other entries; then
`python3 scripts/status.py readme --write` and `python3 scripts/status.py check` here, and commit
the hub.

## 5. Publish it

Only with the maintainer's go-ahead, each step on its own (CONVENTIONS, Section 8), and upstream
first:

```sh
gh repo create formal-phylogenetics/lean4-<id> --private --source . --push   # or --public
```

Then Palomar's preflight (`.github/workflows/palomar_preflight_<paper>.yml`, with the paper's name
in lower case, naming `palomar/<Paper>/comparator.json` and `palomar/<Paper>/formalization.yaml`)
and submission, as the skill's Phase 9 describes.

## 6. Move shared code up the tree

When a second repository needs a definition or a result that lives lower in the tree:

1. Find its new home: the lowest node above both repositories (CONVENTIONS, Section 4).
2. In that repository, on a branch: add it under the home's names and in the directory of its topic,
   acknowledged to its source; keep the home's conventions (its README, its changelog if it has one,
   the audit); bump `version` in its lakefile.
3. Where it was, replace the definition by a deprecated alias of the new one
   (`@[deprecated (since := "<date>")] alias Old.name := New.name`), so that nothing breaks.
4. Move the train's pin of the home (Section 7), then, in each repository that had its own copy, use
   the home's, and prove that no statement changed (the skill's `scripts/stmt_diff.py`).

## 7. Move the train

To a new Lean and Mathlib release, or to new commits of the libraries:

1. This repository: move its toolchain and Mathlib, build, audit, commit.
2. Each hub and library, in the order of their requirements, a hub before its sub-hubs and its
   libraries: move Mathlib and the pins (`lake update Phylogenetics`, and the other libraries it
   requires), build, audit, commit.
3. Edit `[train]` in `collection/repos.toml`.
4. Each formalized paper's repository, upstream first (`builds_on` order): the same as a hub, then
   its Comparator; and the `commit` of its entry in its hub's catalog.
5. The repositories of the papers in progress: `python3 scripts/move_train.py` lists those behind
   the train, and `python3 scripts/move_train.py --behind` moves each one with a clean working tree,
   in one commit: the toolchain, the requirements that `scripts/new_paper.py` would write today, the
   packages hard-linked from its hub's checkout, a build, and its private configuration. One with
   uncommitted work moves in the session that owns it, with `python3 scripts/move_train.py <id>`.
6. Run `python3 scripts/status.py check`, which must report no repository off the train apart from
   the known ones.

A Palomar entry stays pinned to the commit it was submitted at: moving the train does not change
it, and resubmitting is the maintainer's decision. A repository that is off the train joins it the
same way.

## 8. Keep the registry and the catalogs current

- `collection/repos.toml` is the source of truth for the tree and the train,
  `collection/foundations.toml` for the shared mathematics, and each hub's `catalog/papers.toml`
  for its papers. The READMEs' tables are generated from them: never edit those tables by hand.
- `python3 scripts/status.py check` compares the registry and the catalogs with the repositories in
  the workspace: versions against the train, the libraries of the hubs above each repository that
  its lakefile must require, module names that two repositories share (which prevents requiring
  both), cited sources that two repositories formalize, and papers that two entries of the catalogs
  list. A paper has one entry in all the catalogs, in the hub of its estimator or, for a general
  result, in the hub of theory of its kind (CONVENTIONS, Section 1), and the other hubs refer to it
  by `builds_on`: two entries that share a DOI, an arXiv, PubMed or PubMed Central identifier,
  or a title and a first author are an error. Two entries by one first author with nearly the same
  title are a warning, since a preprint, a proceedings paper and a journal paper are one paper unless
  their results differ; an entry that builds on the other is not reported. It fails only on
  errors: a bad registry or catalog, or a repository of a catalog, the root or a hub that breaks the
  conventions.
- To add a paper: add its `[[paper]]` entry to its hub's catalog (a paper in no catalog yet, an id
  unused in every hub, and a root unused by the other repositories; for a shared repository, its
  `repo`, its root and a `paper`), then `python3 scripts/status.py readme --write`. To add a hub: add it to the registry
  with its `parent` (the root, or the hub it is a sub-hub of) and its library's pin, give it a
  library that requires the libraries above it, a catalog and a README with the generated blocks. A
  library under a hub (role `library`) is added the same way, with no catalog; the papers that
  require it name it in `uses`.
