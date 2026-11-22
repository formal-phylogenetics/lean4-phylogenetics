# Changelog

## 2026-11-21: the layout of new repositories

The library does not change: it stays at 0.4.1, and the train's pin of `Phylogenetics` does not move.

A new paper's repository has the standard layout of formalize-math-paper (`docs/CONVENTIONS.md`, Sections 2 and 3):
its code in `<Root>/Common/` and `<Root>/<Paper>/`, its Palomar submission in `palomar/<Paper>/` (the modules
`<Paper>.Challenge` and `<Paper>.Solution`, the Challenge's theorems in the namespace `<Paper>Challenge`), and its
documents, the private `NEXT.md` among them, in `docs/<Paper>/`. `<Paper>` is the catalog's new field `paper`: the
first author's surname and the year (`SolisLemus2016`), derived when an entry gives none, unique across the hubs, and
different from every repository's root. The repositories made earlier keep their layout.

- `scripts/collection.py` derives and checks `paper`. `scripts/status.py check` accepts a repository's Palomar
  submissions, and fails on one named as another repository's root or module root.
- `scripts/new_paper.py` scaffolds the new layout. It takes `--root` for a paper whose catalog root is its author and
  year, refuses to start such a repository without it, and records the root and the paper's name in its hub's catalog.

## 0.4.1

The library moves to Lean and Mathlib `v4.37.0-rc1`. No declaration changed its name or its statement. The proofs
follow Mathlib's changes: the renamed lemmas (`Finset.ne_empty_iff_nonempty`, `Finset.singleton_nonempty`,
`Real.exp_natCast_mul`, `smul_apply`; `Finset.sup_eq_union` is now a syntactic equality), `Set.Iio` in
`SimpleGraph.Walk.IsCycle.getVert_injOn'`, and the stricter elaboration of set notation.

## 0.4.0

The library's areas import one another without a cycle, and `scripts/check_layers.py`, with the areas in
`scripts/layers.toml`, keeps them so: graphs and trees at the bottom, networks above both, the coalescent above trees,
and the network multispecies coalescent above networks and the coalescent. Each area could become a Lake package of its
own. No declaration changed its name or its statement.

The repository is also the root of the collection of formalizations that require it: the registry of its repositories,
the shared foundations, the conventions, the workflow and the tools (`collection/`, `docs/`, `scripts/*.py`).

### Module paths

| Earlier | Now |
| --- | --- |
| `Phylogenetics.Hierarchy.Small` | `Phylogenetics.MSC.Small` |
| `Phylogenetics.Hierarchy.Classify` | `Phylogenetics.MSC.Classify` |
| `Phylogenetics.Hierarchy.Shapes` | `Phylogenetics.MSC.Shapes` |
| `treeOfBlobs_isUnrootedTree`, in `Phylogenetics.Tree.Splits` | the same theorem, in `Phylogenetics.Network.CutHierarchy` |

## 0.3.1

### New results

- The Splits Equivalence Theorem (Semple, Steel 2003, Theorem 3.1.4), for `X`-trees as Mathlib graphs: a collection of
  `X`-splits is the split system of an `X`-tree exactly when its splits are pairwise compatible
  (`SplitsEquivalence.exists_xTree_iff`), and the `X`-tree is unique up to isomorphism (`SplitsEquivalence.xTree_unique`),
  in `Phylogenetics/Tree/SplitsEquivalence.lean`, with what it uses on trees and laminar families in
  `Phylogenetics/Tree/XTree.lean`.

## 0.3.0

The library moves to Lean and Mathlib `v4.36.0-rc1`, and gains directed multigraphs, general rooted
networks, unrooted trees as split families, and the network multispecies coalescent on general networks.
The modules are reorganized by topic. Declarations keep their names
except for those listed below.

### New results

The library holds definitions and general results, each acknowledged to its source.

- The term-based coalescent is the general one at correlation `0` (`Net.geneTreeDist_toRootedNetwork`,
  `Net.nmscCF_toRootedNetwork`), and the multispecies coalescent is the general one on a tree
  (`SpeciesTree.rootedDist_eq_geneTreeDist`). The tool is gluing a network from pieces
  (`NMSC.IsGlued.rootDist_eq`).
- Induced parameters and the induced coalescent (`NMSC.nmscCF_inducedNetwork`).
- A binary digraph with edge-disjoint cycles is level-1 in the sense of its blobs
  (`MetricDigraph.isLevelOne_ofBinary`).
- The displayed tree model, with the mixture at `ρ = 1` (`RootedNetwork.nmscCF_rho_one`,
  `RootedNetwork.one_sub_exp_le_sub_nmscCF_rho_one`).
- Counts and probabilities of displayed quartet trees (`quartetCount`, `displayCF`).
- Neighbor joining (`NJ.isExactBuilder_nj`), Buneman's four-point theorem (`FourPoint.isFourPoint_iff`), and the ASTRAL
  dynamic program (`astralTree_isAstralOptimal`).

### Module paths

| Earlier | Now |
| --- | --- |
| `Phylogenetics.Defs` | `Phylogenetics.Network.Level1.Defs` (networks and cycles), `Phylogenetics.NMSC.Level1.Defs` (the coalescent on them, metric cycles), `Phylogenetics.Network.Level1.CyclicOrder` (`SameCyclicOrder`), `Phylogenetics.Hierarchy.Defs` (`geneTreeDisplays`), `Phylogenetics.Coalescent.Defs` (`forestBelow`) |
| `Phylogenetics.MSC.Defs` | `Phylogenetics.Coalescent.Defs` (Kingman's coalescent, `roots`, `sampledForest`), `Phylogenetics.Hierarchy.Defs` (`childClusters`, `unroot`), `Phylogenetics.Hierarchy.SpeciesTree` (`SpeciesTree`), `Phylogenetics.MSC.Defs` (the model) |
| `Phylogenetics.MSC.Notions` | `Phylogenetics.Hierarchy.Defs` (`restrictClusters`, `restrictSplits`), `Phylogenetics.Hierarchy.SpeciesTree` (`SpeciesTree.restrict`), `Phylogenetics.Coalescent.Defs` (`singletonForest`, `coalescenceProb`), `Phylogenetics.MSC.Defs` (`rootedTripleProb`) |
| `Phylogenetics.MSC.Basic` | `Phylogenetics.Hierarchy.Defs` (`IsHierarchy`), `Phylogenetics.Hierarchy.Basic` (children of a cluster), `Phylogenetics.Hierarchy.SpeciesTree`, `Phylogenetics.MSC.Basic` |
| `Phylogenetics.MSC.Relabel` | `Phylogenetics.Coalescent.Relabel` (`relabelFamily`, Kingman's coalescent), `Phylogenetics.MSC.Relabel` (the model) |
| `Phylogenetics.MSC.Marginal` | `Phylogenetics.Coalescent.Lump` (`restrictForest`, lumpability, `unroot_restrictForest`), `Phylogenetics.MSC.Marginal` (the model) |
| `Phylogenetics.MSC.History` | `Phylogenetics.Coalescent.BinaryForest` (`IsBinaryForest`), `Phylogenetics.MSC.History` |
| `Phylogenetics.Hierarchy.Basic` | `Phylogenetics.Hierarchy.Basic` (hierarchies), `Phylogenetics.Hierarchy.SpeciesTree` (species trees) |
| `Phylogenetics.Hierarchy.Counts` | `Phylogenetics.Hierarchy.Defs` (`IsBinaryHierarchy`), `Phylogenetics.Hierarchy.Counts` |
| `Phylogenetics.Graph.*` | `Phylogenetics.Network.Level1.Digraph.*`. `Phylogenetics.Graph` is now general directed multigraphs. |
| `Phylogenetics.Cycle.*` | `Phylogenetics.NMSC.Level1.MetricCycle.*` |
| `Phylogenetics.CyclicOrder` | `Phylogenetics.Network.Level1.CyclicOrder` |
| `Phylogenetics.NMSC.*` | `Phylogenetics.NMSC.Level1.*`, except `Instance`: `Phylogenetics.NMSC.Level1.MetricCycle.Instance`. `Phylogenetics.NMSC` is now the coalescent on general networks. |
| `Phylogenetics.NMSC.Basic` | `Phylogenetics.Coalescent.BinaryForest` (`IsGoodForest`, `forestBelow_union`), `Phylogenetics.Coalescent.Relabel`, `Phylogenetics.NMSC.Level1.Basic` |
| `Phylogenetics.Tree.*` | `Phylogenetics.Tree.GeneTree.*`. `Phylogenetics.Tree` is now unrooted trees as split families. |

### Deprecated names

Each of these is an alias of the name after it, with `@[deprecated (since := "2026-10-31")]`.

| Deprecated | Use |
| --- | --- |
| `IsGood` | `IsGoodForest` |
| `isGood_empty` | `isGoodForest_empty` |
| `isGood_singletons` | `isGoodForest_singletons` |
| `IsGood.union` | `IsGoodForest.union` |
| `IsGood.relabel` | `IsGoodForest.relabel` |
| `isGood_forestBelow` | `isGoodForest_forestBelow` |
| `kingmanTransition_support_isGood` | `kingmanTransition_support_good` |
| `kingmanAbsorption_support` | `kingmanAbsorption_support_good` |
| `model_IsBinaryForest` | `IsBinaryForest` |
| `model_isBinaryForest_merge` | `isBinaryForest_merge` |
| `model_isBinaryForest_of_jumpMatrix_pow` | `isBinaryForest_of_jumpMatrix_pow` |
| `lineages_singletons` | `lineages_image_singleton` |
| `lineages_relabel` | `lineages_relabelFamily` |
| `relabel_union` | `relabelFamily_union` |
| `relabel_roots` | `roots_relabelFamily` |
| `kingmanTransition_relabel` | `kingmanTransition_relabelFamily` |
| `kingmanAbsorption_relabel` | `kingmanAbsorption_relabelFamily` |
| `kingmanTransition_row_sum` | `kingmanTransition_sum` |
| `kingmanAbsorption_row_sum` | `kingmanAbsorption_sum` |
| `absorb_mem_unroot`, `classify_mem_unroot` | `mem_unroot` |
| `classify_compl_mem_unroot` | `compl_mem_unroot` |
| `classify_mem_relabelFamily` | `mem_relabelFamily` |
| `classify_mem_rootings5` | `mem_rootings5` |
| `absorb_card_roots_singletonForest` | `card_roots_singletonForest` |
| `absorb_roots_singletonForest` | `roots_singletonForest` |

`isGoodForest_iff_binaryHierarchy` and `IsBinaryHierarchy` state the binary condition by "the union of two
disjoint clusters"; `isBinaryHierarchy_iff_card_childClusters` gives the form with two children.
