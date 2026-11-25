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
| Root | [lean4-phylogenetics](https://github.com/formal-phylogenetics/lean4-phylogenetics) | `Phylogenetics` | general phylogenetics, which every repository shares: trees, networks as objects (rooted and semidirected), the coalescents, concordance factors, and the analysis and measure theory they need; also the registry, the foundations, these conventions, the workflow and the tools |
| Hub of inference | [lean4-phylo-alignment](https://github.com/formal-phylogenetics/lean4-phylo-alignment) | `PhyloAlignment` | what the papers on sequence alignment, and on its joint estimation with trees, share; their catalog |
| Hub of inference | [lean4-phylo-gene-tree](https://github.com/formal-phylogenetics/lean4-phylo-gene-tree) | `PhyloGeneTree` | what the papers on estimating a tree from sequences share; their catalog |
| Hub of inference | [lean4-phylo-species-tree](https://github.com/formal-phylogenetics/lean4-phylo-species-tree) | `PhyloSpeciesTree` | what the papers on species tree estimation share; their catalog |
| Hub of inference | [lean4-phylo-network](https://github.com/formal-phylogenetics/lean4-phylo-network) | `PhyloNetwork` | what the papers on network estimation share, those of its sub-hub included; their catalog |
| Sub-hub of lean4-phylo-network | [lean4-phylo-tree-of-blobs](https://github.com/formal-phylogenetics/lean4-phylo-tree-of-blobs) | `TreeOfBlobs` | what only the papers on the tree of blobs share; their catalog; the overview of their field |
| Hub of theory | [lean4-phylo-combinatorics](https://github.com/formal-phylogenetics/lean4-phylo-combinatorics) | `PhyloCombinatorics` | what the papers on the combinatorics of trees and networks, compatibility and complexity share; their catalog |
| Hub of theory | [lean4-phylo-algebraic](https://github.com/formal-phylogenetics/lean4-phylo-algebraic) | `PhyloAlgebraic` | what the papers on invariants, identifiability and mixtures share; their catalog |
| Hub of theory | [lean4-phylo-statistics](https://github.com/formal-phylogenetics/lean4-phylo-statistics) | `PhyloStatistics` | what the papers on consistency, sample complexity and the limits of inference share; their catalog |
| Hub of theory | [lean4-phylo-geometry](https://github.com/formal-phylogenetics/lean4-phylo-geometry) | `PhyloGeometry` | what the papers on spaces of trees, their geodesics and the statistics in them share; their catalog |
| Paper | `lean4-<id>` | `<Root>` (Section 3) | one paper of a hub's catalog, or several on one topic (Section 2) |

The hubs under the root are of two kinds: hubs of inference, one for each object that is estimated
(alignments, trees from sequences, species trees, networks), and hubs of theory, each for a kind of
result: combinatorics, for the discrete characterization of trees and networks, their compatibility and the
complexity of problems on them; algebraic phylogenetics, for invariants and algebraic
identifiability; statistics, for consistency and the limits of information; geometry, for the
structure of spaces of phylogenetic objects and the analysis in them. A paper is in the hub of the
estimator it is about, with the theory of that estimator (the sample complexity of ASTRAL is with
ASTRAL); a general result that serves several methods (an identifiability theorem for a model, the
sequence length that every method needs, the complexity of a problem on trees, the geodesics of tree
space) is in the hub of theory of its kind. The registry gives each hub under the root its `kind`,
`inference` or `theory`; a sub-hub is of its hub's kind. Each paper has one entry in all the
catalogs, whichever hubs use its results.

A hub may have sub-hubs: hubs under it, each for a part of its field whose papers share more than
the rest of the field does. Inferring the tree of blobs is a step of network estimation, so
lean4-phylo-tree-of-blobs is a sub-hub of lean4-phylo-network. The registry,
[`collection/repos.toml`](../collection/repos.toml), lists the root, the hubs, each with its
`parent` (the root or the hub above it), and the repositories that need a note; each hub's
`catalog/papers.toml` lists its papers. The hubs above a paper are its hub and every hub above that
one.

What may require what:

- A paper's repository requires, always, at the train's pins (Section 5), the root library and the
  libraries of the hubs above it: a paper on the tree of blobs requires `Phylogenetics`,
  `PhyloNetwork` and `TreeOfBlobs`. It also requires the libraries of the other hubs it uses
  (`uses` in its catalog entry), and the repositories of the papers whose results its proofs use
  (`builds_on`), in any hub.
- A hub's library requires the root library and the libraries of the hubs above it, and may require
  another hub's library or a paper's repository that is not below it. A library never requires a
  repository below it: a hub cannot require its own papers or its sub-hubs, and nothing can
  require the root's dependents.
- Requirements never form a cycle. `scripts/status.py check` checks the pins, that each repository
  requires the libraries of the hubs above it, and the module names.

## 2. Names

- **Repository** `lean4-<id>`, where `<id>` is the paper's id in its hub's catalog: the method's
  name in lower case when the paper names one (`snaq`, `nanuq-plus`), otherwise first author and
  year (`banos2019`), with a keyword when two papers would share it (`holtgrefe2025-level2`). Ids
  are unique across all hubs. One paper per repository is the default, not a rule: papers on one
  topic may share a repository (Section 3). Their entries then name it in `repo`
  (`repo = "lean4-quarnets"`) and share its root, named after the topic (`Quarnets`), and each paper
  has a name of its own (`paper`; at most one of them leaves it to its default, the root).
- **Root** `<Root>`, the catalog's `root`: the Lake package, and the directory that holds the
  repository's code. It is the method's name when the paper names one (`Snaq`, `NanuqPlus`),
  otherwise first author and year (`Banos2019`), with the id's keyword when there is one
  (`Holtgrefe2025Level2`). The root follows the id: a repository whose id changes takes the root of
  its new id, and its code, its namespaces and its Palomar submission follow. Only the entries of
  one repository share a root. A hub's package names its library (`PhyloNetwork`, `TreeOfBlobs`).
- **Paper** `<Paper>`: the name of the paper's directories (`palomar/<Paper>/`, `docs/<Paper>/`,
  and `<Root>/<Paper>/` in a repository with several papers), of its namespace and of its Palomar
  submission. It is the root, unless the entry states another in the optional field `paper`: for a
  repository with several papers, where each paper needs a name of its own, or when the maintainer
  wants another name.
- **Uniqueness.** A `paper` that an entry states is a capitalized Lean identifier, unique among the
  papers of all hubs, and is not the root of another repository: the modules `<Paper>.Challenge`
  and `<Paper>.Solution` would otherwise be under that root. It may be its own repository's root,
  which is the default. The papers of one repository have distinct names. `scripts/status.py
  check` checks all of this.
- **Namespaces.** The paper's library is in the namespace `<Paper>`, the Challenge's theorems in
  `<Paper>Challenge`, the results the paper cites in `External.<Src>`, and general mathematics in
  Mathlib's namespaces. Namespaces do not follow directories (the skill's
  `references/lean-project.md`, Section 2).
- **Modules.** Every module of a repository is in its root's directory, `<Root>/`, except the
  modules of its Palomar submissions: `<P>.Challenge` and `<P>.Solution`, in `palomar/<P>/`, where
  `<P>` is the paper's `<Paper>` (by default the root, so that these names are under the root too)
  or the name of an addition with a Challenge of its own, which follows the rules of `paper`. No
  repository has a top-level `Basic`, `External`, `Challenge`, `Solution`, `MainResults` or `Defs`:
  Lean module names are global, and the repositories of the collection import one another.
- **Labels.** Docstrings carry the paper's TeX labels as the skill says
  (``**Theorem 1.2** (`thm:main`).``). A result of another repository restated in
  `<Root>/External/` carries the label of its row in that repository's routes file,
  prefixed with that repository's id (``(`nanuq:thm:36`)``), so that it cannot collide with this
  paper's labels.

## 3. Layout of a paper's repository, and of a hub

A paper's repository has the skill's layout (`references/lean-project.md`, Sections 2 and 3), with
the root `<Root>` for the skill's `ProjectName` and the paper `<Paper>` for its `PaperName`; for
one paper, `<Paper>` is the root. `scripts/new_paper.py` creates the files marked *scaffold*, and
the links to the private files (Section 7); the skill writes the rest.

```text
README.md                         scaffold: a stub; rewritten in the skill's Phase 8
LICENSE                           scaffold: Apache-2.0
lakefile.toml, lean-toolchain,    scaffold: on the train (Section 5), with the libraries below
  lake-manifest.json
.gitignore                        scaffold: ignores .lake and the private files (Section 7)
<Root>/Basic/                     general mathematics, in Mathlib's namespaces; scaffold: README.md
<Root>/External/<Src>/            cited results, namespace External.<Src>, each with a README.md;
                                  scaffold: <Root>/External/README.md
<Root>/Defs.lean                  scaffold: every definition the Challenge uses, between the sync
                                  markers
<Root>/<Section>/…                the paper's library, in the namespace <Paper>, by section
palomar/<Paper>/Challenge.lean    scaffold: module <Paper>.Challenge, the statements of record, in
                                  the namespace <Paper>Challenge; imports only Mathlib
palomar/<Paper>/Solution.lean     scaffold: module <Paper>.Solution, their proofs; the library's
                                  entry point
palomar/<Paper>/comparator.json   "challenge_module": "<Paper>.Challenge",
                                  "solution_module": "<Paper>.Solution"
palomar/<Paper>/formalization.yaml
docs/<Paper>/                     REPORT.md, CREDITS.md, paper_routes.tsv, route_differences.tsv,
                                  numerics/ if any
scripts/                          Audit.lean and the skill's other tools
.github/workflows/                lean_action_ci.yml (scaffold: it builds; the skill adds its
                                  checks); palomar_preflight_<paper>.yml (the skill's Phase 9)
```

For example, the repository of SNaQ (Solís-Lemus, Ané 2016) will have `Snaq/Basic/`,
`Snaq/External/`, `Snaq/Defs.lean`, `Snaq/<Section>/`, `palomar/Snaq/` (the modules
`Snaq.Challenge` and `Snaq.Solution`) and `docs/Snaq/`, with the library in the namespace `Snaq`
and the Challenge's theorems in `SnaqChallenge`.

The lakefile has two libraries, both default targets: `<Root>` (`globs = ["<Root>.+"]`), then
`Palomar` (`srcDir = "palomar"`, `roots = ["<Paper>.Challenge", "<Paper>.Solution"]`). `Palomar`
is declared last: Lake gives a module to the last library whose patterns match it, and the glob
`<Root>.+` matches `<Root>.Challenge` and `<Root>.Solution` too. Declared first, `Palomar` loses
them, and `lake build <Paper>.Solution`, as Comparator runs it, looks for them in `<Root>/` and
fails. `scripts/status.py check` fails on a library declared after `Palomar` whose patterns match
one of its modules. Lake also fails on a glob whose directory, or a root whose file, does not
exist: the scaffold creates each.

The skill's layering holds, and is checked in review: `<Root>/Basic/` imports only Mathlib;
`<Root>/External/` imports Mathlib, `<Root>/Basic/` and the libraries this repository requires;
the paper's library imports anything below it, and nothing in `Basic/` or `External/` imports it;
`<Root>/Defs.lean` and the Challenge import only Mathlib. Where the skill's tools and CI name
`ProjectName` and `PaperName`, use `<Root>` and `<Paper>`.

The audit, `scripts/Audit.lean`, imports with `import all` every module of `<Root>/` and the
Solution of each submission, never a Challenge (the skill's `references/multi-paper.md`,
Section 5). It covers the repositories that this one requires too (its `import all` lines include
their modules, and CI builds their libraries first), so that one run checks every axiom that a
result depends on.

A repository with several papers has the layout of the skill's `references/multi-paper.md`: the
shared code in `<Root>/Common/Basic/` and `<Root>/Common/External/`, and for each paper its
library `<Root>/<Paper>/` (with its `Defs.lean`), its submission `palomar/<Paper>/` and its
documents `docs/<Paper>/`, with the umbrella README at the top (`multi-paper.md`, Section 6). Its
lakefile has the library `Common` (`globs = ["<Root>.Common.+"]`), one library per paper
(`globs = ["<Root>.<Paper>.+"]`), and, last, `Palomar`, whose `roots` list each paper's two
modules. When a paper joins a repository of one paper, the first paper keeps the root's name and
its code moves, as `multi-paper.md`, Section 9, says: its library to `<Root>/<Root>/`, and
`Basic/` and `External/` to `<Root>/Common/`. SNaQ.jl joining SNaQ's repository
(`repo = "lean4-snaq"`, `root = "Snaq"`, `paper = "SnaqJl"`) gives `Snaq/Common/`, `Snaq/Snaq/` and
`Snaq/SnaqJl/`. `scripts/new_paper.py` starts a repository with its first paper; the others join it
by hand. In the rest of these conventions, `<Root>/Basic/`, `<Root>/External/` and
`<Root>/Defs.lean` stand, in such a repository, for `<Root>/Common/Basic/`,
`<Root>/Common/External/` and `<Root>/<Paper>/Defs.lean`.

Every repository of a paper has this layout, with no exception. To bring a repository to it, move
its files with `git mv` and rename its modules by their exact names (the skill's
`references/multi-paper.md`, Section 9).

A hub has its library under `<Package>/` (with a README that says what is there and why), its
catalog `catalog/papers.toml`, its README (whose tables `scripts/status.py` generates from the
catalog), and, for a field with formalized papers, an overview of the field in `docs/`. It holds no
paper, so none of a paper's files: no Palomar submission, routes or audit of a paper. In its
library, general mathematics is in `<Package>/ForMathlib/`, in Mathlib's namespaces, and imports
only Mathlib, the libraries above and `ForMathlib/` itself; the results of a cited source are in
`<Package>/External/<Src>/`, in the namespace `External.<Src>`, each with a README; and the rest is
in the namespace of the package (`PhyloNetwork.Level1`) or in the root's (`Phylogenetics`,
`Phylogenetics.RootedNetwork`), which a declaration keeps when it moves up to the root, never in a
paper's.

## 4. Where code goes

The rule: **a definition or result goes to the lowest node of the tree above every repository
that uses it.**

| What | Where |
| --- | --- |
| A result of this paper | this repository |
| What two papers or more of one hub use, or papers of a hub and of its sub-hubs | the library of the lowest hub above all of them |
| What papers of hubs that have no hub above them all use, or a definition or result that textbooks state | the root library, `Phylogenetics`, acknowledged to its source |
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

The Challenge is the exception to reuse: Palomar accepts only Lean, Mathlib, Tau Ceti and CSLib in a
Challenge's imports. So `<Root>/Defs.lean` restates in Mathlib's vocabulary every definition that
the Challenge needs, between the sync markers, even those that a library of the collection has, and
the library proves that the two agree.

## 5. Versions: the train

Repositories that require one another must share one Lean and one Mathlib release, and one commit
of each library of the tree. The train is the `[train]` table of the registry: the Lean and Mathlib
release, and in `[train.pins]` the commit of each library (`Phylogenetics`, `PhyloNetwork`,
`TreeOfBlobs`, …).

- A new repository uses the train, not the newest Lean release (which the skill's Phase 0 would
  otherwise choose). It gets the train from `scripts/new_paper.py`.
- A paper's repository is created when its formalization starts, not before
  (docs/WORKFLOW.md, Section 2): every repository moves with the train, and one that waits for its
  turn would move each time with nothing in it.
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
  `<Root>/External/<Src>/`, in its source's terms, and proved from the other repository's
  theorem, as the skill does for a package it requires (`references/separate-packages.md`,
  Section 4). The report counts it as a cited result, proved, and names the repository and the
  theorem.
- Its row in `docs/<Paper>/paper_routes.tsv` has `proved = 0` and the prefixed label of Section 2.
- When this paper's `builds_on` changes, update its hub's catalog.

## 7. Private files

Every repository of the collection is public-facing: the root, the hubs and the papers'. What the
skill keeps out of git is private, and stays outside the repository:

| Path in the repository | Holds |
| --- | --- |
| `notes/` | the working notes: the Phase 0 configuration, the inventory, the run log, the TeX source, the follow-up papers (the skill's Phase 8), drafts and scratch |
| `.vscode/` | the editor's settings |
| `CLAUDE.md` | the agent's instructions for the repository |

Each is a symbolic link to a private location, ignored by the repository's `.gitignore` with no
trailing slash (`/notes`, not `/notes/`: a pattern with one does not match a link). The skill's
untracked `notes/` is this folder.

- Never commit them, and never put notes on a branch: visibility applies to every branch.
- Nothing committed (code, comments, documents, commit messages, pull request descriptions) says
  where the private files are kept, says what they hold, or quotes them.
- Plans and decisions that are not public yet, and repositories that are private, belong with the
  private files, not in the registry or a catalog. The tools merge a private overlay for local
  checks; the READMEs, which are public, are generated without it.

## 8. Publishing

Repositories are created in the GitHub organization
[formal-phylogenetics](https://github.com/formal-phylogenetics). Creating one, pushing, changing its
visibility, opening or closing pull requests, running Palomar's preflight and submitting to Palomar
each need the maintainer's explicit permission, and permission for one is not permission for another
(the skill's Rules). Push in the order of the requirements, upstream first, so that every pinned
commit exists when a repository that requires it is pushed. Each paper is a Palomar submission of
its own.

A repository's description on GitHub has one of these forms, with no count of anything:

- a hub: `<its title> in Lean 4: a hub of <inference or theory>, with its shared library <Package>
  and its catalog of papers` (a sub-hub: `a sub-hub of <its hub>`);
- a paper: `Lean 4 formalization of <the authors in full> (<year>), "<the paper's title>"`, with `,
  in progress,` after `formalization` while it is.

The README of a paper opens the same way: its first sentence names the authors in full, the year, the
title in quotes and the venue, and says that it is a Lean 4 formalization.

## 9. When a paper is done

When the skill's completion gates are met:

1. In its hub's catalog, set the entry to `status = "formalized"` with `commit = "<full hash>"`,
   correct its citation, and complete its `builds_on`. Update `covered_by` of the papers whose
   results it formalized in passing.
2. Run `python3 scripts/status.py readme --write` and `python3 scripts/status.py check` here, and
   commit the hub.
3. What another paper will need moves up the tree (Section 4).
4. Repositories that formalized this paper's results in their `<Root>/External/` may now require
   it instead. This is optional: what they prove is already proved.
