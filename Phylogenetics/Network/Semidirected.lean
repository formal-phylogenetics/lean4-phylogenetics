module

public import Phylogenetics.Network.Induced

/-!
# Semidirected networks

A semidirected network keeps the directions of the hybrid edges of a rooted network and forgets those of
its tree edges. The semidirected network `N⁻` of a binary rooted phylogenetic network `N⁺` is obtained
from the part of `N⁺` below the least stable ancestor (LSA) of all the taxa, rooted at the LSA, by
undirecting the tree edges and suppressing the root.

* `SemidirectedNetwork V E X`: a multigraph whose edges carry an order of their two ends, with the
  edges `IsDirected` (the hybrid edges), for which that order is the direction, and a labelling of
  the taxa. For the other edges the order has no meaning.
* `RootedNetwork.renameTaxa`: the same network with its taxa renamed by an equivalence.
* `RootedNetwork.unrootAt`: suppressing the root of a rooted network, merging its two edges.
* `RootedNetwork.lsaPlus`: the part of a network below the LSA of all the taxa, rooted at the LSA,
  on the taxa `X` themselves.
* `RootedNetwork.semidirected`, `RootedNetwork.semidirectedMetric`: the semidirected network `N⁻`
  of a binary phylogenetic network and its numerical parameters.
* `RootedNetwork.lsaNetwork_outdegree_root`: the root of the part below the LSA of a binary network
  has outdegree two.

## References

* H. Baños, *Identifying species network features from gene tree quartets under the coalescent
  model*, Bull. Math. Biol. 81 (2019), 494–534, Definitions 5 and 6.
* E. S. Allman, H. Baños, J. D. Mitchell, J. A. Rhodes, *The tree of blobs of a species network:
  identifiability under the coalescent*, J. Math. Biol. 86 (2023), 10, Definition 5.
-/

@[expose] public noncomputable section

open scoped Classical

namespace Phylogenetics

/-- A *semidirected network*. Every edge has two ends, given in some order. For the edges with
`IsDirected`, the hybrid edges, that order is the direction; for the others it has no meaning: walks,
cut edges and blobs of `graph` forget it. -/
structure SemidirectedNetwork (V E X : Type*) where
  graph : DirectedMultigraph V E
  IsDirected : E → Prop
  leaf : X → V

namespace RootedNetwork

variable {V E X : Type*} {N : RootedNetwork V E X}

/-! ### The outdegree of the LSA -/

section Below

variable {l : V} {Y : Set X} {hl : l ∈ N.ancestralVertices Y}
  {hleaf : ∀ x ∈ Y, N.graph.Reaches l (N.leaf x)}

/-- Arcs below a vertex leave a vertex with at most its outdegree in the network. -/
theorem belowNetwork_outdegree_le [Finite E] (v : N.belowVertices l Y) :
    (N.belowNetwork l Y hl hleaf).graph.outdegree v ≤ N.graph.outdegree v.1 :=
  Set.ncard_le_ncard_of_injOn (fun e => e.1) (fun _ he => congrArg Subtype.val he)
    (fun _ _ _ _ h => Subtype.ext h) (Set.toFinite _)

end Below

/-- The part from `w` on of a path avoiding `c`, when the path cannot avoid `w`. -/
theorem HasPathAvoiding.suffix_of_not_hasPathAvoiding {u t c w : V} (h : N.HasPathAvoiding u t c)
    (hw : ¬ N.HasPathAvoiding u t w) : N.HasPathAvoiding w t c := by
  obtain ⟨-, ht, hp⟩ := h
  induction hp using Relation.ReflTransGen.head_induction_on with
  | refl =>
    have : t = w := by
      by_contra hne
      exact hw ⟨hne, hne, .refl⟩
    subst this
    exact ⟨ht, ht, .refl⟩
  | @head a b hab hbt ih =>
    by_cases ha : a = w
    · subst ha
      exact ⟨hab.2.1, ht, hbt.head hab⟩
    · exact ih fun h => hw (hasPathAvoiding_head hab.1 ha h)

/-- **The unique child of a stable ancestor is a stable ancestor**: below `l`, the paths to the taxa start
with the arc to it, when no other arc leaving `l` is ancestral to the taxa. -/
theorem IsStableAncestor.target_of_unique (hN : N.IsPhylogenetic) {Y : Set X} (hY : Y.Nontrivial)
    {l : V} (hst : N.IsStableAncestor Y l) {e : E}
    (huniq : ∀ f, N.graph.source f = l → f ∈ N.ancestralArcs Y → f = e) :
    N.IsStableAncestor Y (N.graph.target e) := by
  intro x hx hp
  obtain ⟨-, -, hq⟩ := hp.suffix_of_not_hasPathAvoiding (hst x hx)
  rcases Relation.ReflTransGen.cases_head hq with h | ⟨a, ⟨⟨f, hfs, hft⟩, -, ha⟩, hat⟩
  · exact hst.leaf_ne hN hY x h.symm
  · have hfa : f ∈ N.ancestralArcs Y := by
      refine ⟨x, hx, ?_⟩
      rw [hft]
      exact Relation.ReflTransGen.mono (fun _ _ h => h.1) _ _ hat
    rw [huniq f hfs hfa] at hft
    exact ha hft.symm

/-- **The LSA does not have just one child below it**, else that child would be a lower stable ancestor. -/
theorem lsaNetwork_outdegree_root_ne_one (hN : N.IsPhylogenetic) {Y : Set X} (hY : Y.Nontrivial) :
    (lsaNetwork hN Y hY.nonempty).graph.outdegree (lsaNetwork hN Y hY.nonempty).root ≠ 1 := by
  intro h
  obtain ⟨e, he⟩ := (DirectedMultigraph.outdegree_eq_one_iff _ _).mp h
  obtain ⟨hst, hleast⟩ := lsa_spec hN Y hY.nonempty
  have hes : N.graph.source e.1 = lsa hN Y hY.nonempty := congrArg Subtype.val ((he e).mpr rfl)
  have hc := hleast _ (hst.target_of_unique hN hY (e := e.1) fun f hfs hfa => by
    have hf : f ∈ N.belowArcs (lsa hN Y hY.nonempty) Y := ⟨by rw [hfs]; exact .refl, hfa⟩
    exact congrArg Subtype.val ((he ⟨f, hf⟩).mp (Subtype.ext hfs)))
  refine hN.acyclic _ (Relation.TransGen.head' ⟨e.1, hes, rfl⟩ hc)

/-- The root of the part below the LSA has outdegree two. -/
theorem lsaNetwork_outdegree_root (hN : N.IsPhylogenetic) (hBin : N.IsBinary) {Y : Set X}
    (hY : Y.Nontrivial) :
    (lsaNetwork hN Y hY.nonempty).graph.outdegree (lsaNetwork hN Y hY.nonempty).root = 2 := by
  have : Finite E := hN.finite_arcs
  have hne := lsaNetwork_outdegree_root_ne_one hN hY
  have hst := (lsa_spec hN Y hY.nonempty).1
  have h0 : (lsaNetwork hN Y hY.nonempty).graph.outdegree (lsaNetwork hN Y hY.nonempty).root ≠ 0 := by
    intro h
    obtain ⟨x, hx⟩ := ((lsaNetwork_isPhylogenetic hN hY).leaves _).mp h
    exact hst.leaf_ne hN hY x.1 (congrArg Subtype.val hx)
  have hle : (lsaNetwork hN Y hY.nonempty).graph.outdegree (lsaNetwork hN Y hY.nonempty).root ≤
      N.graph.outdegree (lsa hN Y hY.nonempty) :=
    belowNetwork_outdegree_le _
  have hle2 : N.graph.outdegree (lsa hN Y hY.nonempty) ≤ 2 := by
    by_cases hr : lsa hN Y hY.nonempty = N.root
    · rw [hr, hBin.1]
    · have h₁ := hN.nonroot_indegree _ hr
      have h₂ := hBin.2 _ hr (by omega)
      omega
  omega

/-! ### Renaming the taxa -/

/-- The same network, with its taxa renamed by `f`. -/
def renameTaxa {X' : Type*} (M : RootedNetwork V E X) (f : X' ≃ X) : RootedNetwork V E X' where
  graph := M.graph
  root := M.root
  leaf x := M.leaf (f x)

theorem renameTaxa_isPhylogenetic {X' : Type*} {M : RootedNetwork V E X} (hM : M.IsPhylogenetic)
    (f : X' ≃ X) : (renameTaxa M f).IsPhylogenetic where
  finite_vertices := hM.finite_vertices
  finite_arcs := hM.finite_arcs
  finite_taxa :=
    have := hM.finite_taxa
    Finite.of_equiv _ f.symm
  acyclic := hM.acyclic
  root_reaches := hM.root_reaches
  root_indegree := hM.root_indegree
  nonroot_indegree := hM.nonroot_indegree
  leaf_injective := hM.leaf_injective.comp f.injective
  leaf_indegree x := hM.leaf_indegree (f x)
  leaves v := by
    refine (hM.leaves v).trans ⟨?_, ?_⟩
    · rintro ⟨x, hx⟩
      exact ⟨f.symm x, by simpa [renameTaxa] using hx⟩
    · rintro ⟨x, hx⟩
      exact ⟨f x, hx⟩

/-! ### Suppressing the root -/

/-- No arc of a phylogenetic network enters its root. -/
theorem IsPhylogenetic.target_ne_root {M : RootedNetwork V E X} (hM : M.IsPhylogenetic) (e : E) :
    M.graph.target e ≠ M.root :=
  have := hM.finite_arcs
  (M.graph.indegree_eq_zero_iff _).mp hM.root_indegree e

/-- Suppressing the root of a rooted network, undirecting its tree edges and retaining the directions of
its hybrid edges. The root's edge `e₀` and its other edge become one edge, from the child of `e₀` to the
child of the other edge. If `e₀` is a tree edge and the other edge is hybrid, the merged edge is hybrid,
directed as the other edge; if both are tree edges, the order has no meaning. -/
def unrootAt (M : RootedNetwork V E X) (hM : M.IsPhylogenetic) (e₀ : E) :
    SemidirectedNetwork {v // v ≠ M.root} {e // e ≠ e₀} X where
  graph :=
    { source := fun e =>
        if h : M.graph.source e.1 = M.root then ⟨M.graph.target e₀, hM.target_ne_root e₀⟩
        else ⟨M.graph.source e.1, h⟩
      target := fun e => ⟨M.graph.target e.1, hM.target_ne_root e.1⟩ }
  IsDirected e := M.IsHybridArc e.1
  leaf x := ⟨M.leaf x, M.leaf_ne_root hM x⟩

/-- **The two out-edges of the root are not both hybrid**, when the root has outdegree two and every
stable ancestor of the taxa is above it. A highest node other than the root has all its parents at the
root, so if it were hybrid, it would take both edges of the root, and would be a stable ancestor below
the root. -/
theorem exists_isTreeArc_root {M : RootedNetwork V E X} (hM : M.IsPhylogenetic) [Nonempty X]
    (hout : M.graph.outdegree M.root = 2)
    (hlsa : ∀ w, M.IsStableAncestor Set.univ w → M.graph.Reaches w M.root) :
    ∃ e, M.graph.source e = M.root ∧ M.IsTreeArc e := by
  have := hM.finite_vertices
  have := hM.finite_arcs
  let r : V → V → Prop := fun a b => Relation.TransGen M.graph.Adj a b
  have : IsTrans V r := ⟨fun _ _ _ h h' => h.trans h'⟩
  have : Std.Irrefl r := ⟨fun a h => hM.acyclic a h⟩
  have hwf : WellFounded r := Finite.wellFounded_of_trans_of_irrefl r
  obtain ⟨x₀⟩ := ‹Nonempty X›
  obtain ⟨w, hw, hmin⟩ := hwf.has_min {v | v ≠ M.root} ⟨M.leaf x₀, M.leaf_ne_root hM x₀⟩
  have hparent : ∀ f, M.graph.target f = w → M.graph.source f = M.root := fun f hf => by
    by_contra hs
    exact hmin _ hs (.single ⟨f, rfl, hf⟩)
  obtain ⟨e, he⟩ := (M.graph.one_le_indegree_iff w).mp (hM.nonroot_indegree w hw)
  by_cases h1 : M.graph.indegree w = 1
  · exact ⟨e, hparent e he, by unfold IsTreeArc; rwa [he]⟩
  exfalso
  have h2 : 2 ≤ M.graph.indegree w := by
    have := hM.nonroot_indegree w hw
    omega
  have hsub : {f | M.graph.target f = w} ⊆ {f | M.graph.source f = M.root} := fun f hf => hparent f hf
  have heq : {f | M.graph.target f = w} = {f | M.graph.source f = M.root} := by
    refine Set.eq_of_subset_of_ncard_le hsub ?_ (Set.toFinite _)
    change M.graph.outdegree M.root ≤ M.graph.indegree w
    omega
  have hall : ∀ f, M.graph.source f = M.root → M.graph.target f = w := fun f hf =>
    (Set.ext_iff.mp heq f).mpr hf
  have hst : M.IsStableAncestor Set.univ w := by
    rintro x - ⟨-, -, hp⟩
    rcases Relation.ReflTransGen.cases_head hp with h | ⟨a, ⟨⟨f, hfs, hft⟩, -, ha⟩, -⟩
    · exact M.leaf_ne_root hM x h.symm
    · exact ha (hft ▸ hall f hfs)
  exact hw (eq_of_reaches_of_reaches hM.acyclic (hlsa w hst) (hM.root_reaches w))

/-! ### The semidirected network of a binary network -/

/-- The part of `N` below the LSA of all the taxa, rooted at the LSA, on the taxa `X` themselves: the
LSA network `𝒩⊕` (Baños 2019, Definition 8, on all the taxa; Allman et al. 2023, Definition 5). -/
def lsaPlus (hN : N.IsPhylogenetic) (hX : Nontrivial X) :
    RootedNetwork (N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ)
      (N.belowArcs (lsa hN Set.univ Set.univ_nonempty) Set.univ) X :=
  renameTaxa (lsaNetwork hN Set.univ Set.univ_nonempty) (Equiv.Set.univ X).symm

theorem lsaPlus_isPhylogenetic (hN : N.IsPhylogenetic) (hX : Nontrivial X) :
    (lsaPlus hN hX).IsPhylogenetic :=
  renameTaxa_isPhylogenetic (lsaNetwork_isPhylogenetic hN Set.nontrivial_univ) _

/-- Every node is above a taxon, so every node is ancestral to the taxa. -/
theorem mem_ancestralVertices_univ (hN : N.IsPhylogenetic) (v : V) :
    v ∈ N.ancestralVertices Set.univ := by
  obtain ⟨x, hx⟩ := exists_reaches_leaf hN v
  exact ⟨x, Set.mem_univ x, hx⟩

/-- A stable ancestor of `𝒩⊕` is one of `N`: so the root of `𝒩⊕` is its own LSA. -/
theorem lsaPlus_reaches_root_of_isStableAncestor (hN : N.IsPhylogenetic) (hX : Nontrivial X)
    {w : N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ}
    (hw : (lsaPlus hN hX).IsStableAncestor Set.univ w) :
    (lsaPlus hN hX).graph.Reaches w (lsaPlus hN hX).root := by
  obtain ⟨hst, hleast⟩ := lsa_spec hN Set.univ Set.univ_nonempty
  by_cases hwl : w.1 = lsa hN Set.univ Set.univ_nonempty
  · have : w = (lsaPlus hN hX).root := Subtype.ext hwl
    rw [this]
    exact .refl
  exfalso
  -- a path of `N` below the LSA avoiding `w` is a path of `𝒩⊕`
  have hlift : ∀ t, Relation.ReflTransGen (fun a b => N.graph.Adj a b ∧ a ≠ w.1 ∧ b ≠ w.1)
      (lsa hN Set.univ Set.univ_nonempty) t →
      ∀ ht : t ∈ N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ,
      Relation.ReflTransGen (fun a b => (lsaPlus hN hX).graph.Adj a b ∧ a ≠ w ∧ b ≠ w)
        (lsaPlus hN hX).root ⟨t, ht⟩ := by
    intro t ht
    induction ht with
    | refl => exact fun _ => .refl
    | @tail a b hab hs ih =>
      intro hb
      have ha : a ∈ N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ :=
        ⟨Relation.ReflTransGen.mono (fun _ _ h => h.1) _ _ hab, mem_ancestralVertices_univ hN a⟩
      obtain ⟨⟨f, hfs, hft⟩, hsa, hsb⟩ := hs
      refine (ih ha).tail ⟨⟨⟨f, hfs ▸ ha.1, mem_ancestralVertices_univ hN _⟩, Subtype.ext hfs,
        Subtype.ext hft⟩, fun h => hsa (congrArg Subtype.val h), fun h => hsb (congrArg Subtype.val h)⟩
  have hreach : ∀ x, ¬ N.HasPathAvoiding N.root (N.leaf x) w.1 := by
    intro x hp
    have hs := hp.suffix_of_not_hasPathAvoiding (hst x (Set.mem_univ x))
    have hxb : N.leaf x ∈ N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ :=
      ⟨hst.reaches_leaf hN (Set.mem_univ x), mem_ancestralVertices_univ hN _⟩
    refine hw x (Set.mem_univ x) ⟨fun h => hwl (congrArg Subtype.val h).symm,
      fun h => hs.2.1 (congrArg Subtype.val h), ?_⟩
    exact hlift _ hs.2.2 hxb
  exact hwl (eq_of_reaches_of_reaches hN.acyclic (hleast w.1 fun x _ => hreach x) w.2.1)

/-- The root of `𝒩⊕` has outdegree two. -/
theorem lsaPlus_outdegree_root (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X) :
    (lsaPlus hN hX).graph.outdegree (lsaPlus hN hX).root = 2 :=
  lsaNetwork_outdegree_root hN hB Set.nontrivial_univ

/-- The edge out of the root of `𝒩⊕` that is merged into the other when the root is suppressed: a tree
edge. -/
def rootTreeArc (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X) :
    N.belowArcs (lsa hN Set.univ Set.univ_nonempty) Set.univ :=
  Classical.choose (exists_isTreeArc_root (M := lsaPlus hN hX) (lsaPlus_isPhylogenetic hN hX)
    (lsaPlus_outdegree_root hN hB hX) fun _ hw => lsaPlus_reaches_root_of_isStableAncestor hN hX hw)

theorem rootTreeArc_spec (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X) :
    (lsaPlus hN hX).graph.source (rootTreeArc hN hB hX) = (lsaPlus hN hX).root ∧
      (lsaPlus hN hX).IsTreeArc (rootTreeArc hN hB hX) :=
  Classical.choose_spec (exists_isTreeArc_root (M := lsaPlus hN hX) (lsaPlus_isPhylogenetic hN hX)
    (lsaPlus_outdegree_root hN hB hX) fun _ hw => lsaPlus_reaches_root_of_isStableAncestor hN hX hw)

/-- The nodes of `N⁻`: those of `𝒩⊕` other than its root. -/
abbrev SemidirectedVertex (hN : N.IsPhylogenetic) (hX : Nontrivial X) :=
  {v : N.belowVertices (lsa hN Set.univ Set.univ_nonempty) Set.univ // v ≠ (lsaPlus hN hX).root}

/-- The edges of `N⁻`: those of `𝒩⊕` other than `rootTreeArc`, which is merged into the other edge of
the root. -/
abbrev SemidirectedArc (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X) :=
  {e : N.belowArcs (lsa hN Set.univ Set.univ_nonempty) Set.univ // e ≠ rootTreeArc hN hB hX}

/-- **The semidirected network `N⁻`** of a binary phylogenetic network (Baños 2019, Definition 5;
Allman et al. 2023, Definition 5): from the LSA network `𝒩⊕`, undirect the tree edges and suppress the
root, retaining the directions of the hybrid edges. -/
def semidirected (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X) :
    SemidirectedNetwork (SemidirectedVertex hN hX) (SemidirectedArc hN hB hX) X :=
  unrootAt (lsaPlus hN hX) (lsaPlus_isPhylogenetic hN hX) (rootTreeArc hN hB hX)

/-- The lengths and inheritance probabilities of `N⁻` (Baños 2019, Definition 6): the edge merged at the
root has the sum of the lengths of the two edges it replaces and the inheritance probability of the
root's other edge, which is the hybrid one if either is; the other edges keep their parameters. -/
def semidirectedMetric (hN : N.IsPhylogenetic) (hB : N.IsBinary) (hX : Nontrivial X)
    (θ : MetricData E) : MetricData (SemidirectedArc hN hB hX) where
  length e :=
    if (lsaPlus hN hX).graph.source e.1 = (lsaPlus hN hX).root then
      θ.length e.1.1 + θ.length (rootTreeArc hN hB hX).1
    else θ.length e.1.1
  inheritance e := θ.inheritance e.1.1

end RootedNetwork

end Phylogenetics
