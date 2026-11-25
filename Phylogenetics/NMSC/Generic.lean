module

public import Phylogenetics.ForMathlib.Analysis.AnalyticZeroSet
public import Phylogenetics.NMSC.Analytic
public import Phylogenetics.NMSC.History

/-!
# Null sets of parameters

A property holds for generic numerical parameters of a network when it fails only on a null set of
parameters, `RootedNetwork.IsGenericNull`: null in the coordinates of all edge lengths and, at each
reticulation, the inheritance probabilities of all parents but one. This module proves that the null
sets of parameters are closed under subsets and countable unions, and gives the analytic argument of
Allman et al. (2023): a function of the parameters that is analytic in these coordinates and nonzero at
some parameters vanishes only on a null set. Two concordance factors that differ at some parameters
therefore differ at generic parameters.

## Main results

* `RootedNetwork.IsGenericNull.mono`, `RootedNetwork.IsGenericNull.union`,
  `RootedNetwork.IsGenericNull.iUnion`, `RootedNetwork.isGenericNull_empty`: null sets of parameters
  are closed under subsets and countable unions, and the empty set is null.
* `coordMetric_self`: every normalized parameter is `coordMetric` at its own coordinates, for every
  choice of the left-out parents.
* `RootedNetwork.isGenericNull_of_analyticOnNhd`: the analytic argument.
* `RootedNetwork.isGenericNull_nmscCF_eq`: two concordance factors that differ at some normalized
  parameters differ at generic parameters.

## Sources

The closure properties come from lean4-tob (`TreeOfBlobs/General.lean`) and lean4-banos2019
(`isGenericNull_empty`), and the analytic argument from lean4-allman2023
(`Allman2023/FourTaxa/GenericCF.lean`), <https://github.com/vltanh>.

## References

* E. S. Allman, H. Baños, J. D. Mitchell, J. A. Rhodes, *The tree of blobs of a species network:
  identifiability under the coalescent*, J. Math. Biol. 86 (2023), 10, proof of Theorem 1.
-/

@[expose] public noncomputable section

open Finset MeasureTheory Phylogenetics.RootedNetwork
open scoped Classical

namespace Phylogenetics

variable {V E X : Type*} [Fintype E] {N : RootedNetwork V E X}

namespace RootedNetwork

/-- A subset of a null set of parameters is null. -/
theorem IsGenericNull.mono {A B : Set (MetricData E)} (hB : IsGenericNull N B) (h : A ⊆ B) :
    IsGenericNull N A := by
  intro d hd
  refine measure_mono_null ?_ (hB d hd)
  rintro x ⟨θ, hθ, rest⟩
  exact ⟨θ, h hθ, rest⟩

/-- A countable union of null sets of parameters is null. -/
theorem IsGenericNull.iUnion {ι : Type*} [Countable ι] {A : ι → Set (MetricData E)}
    (h : ∀ i, IsGenericNull N (A i)) : IsGenericNull N (⋃ i, A i) := by
  intro d hd
  refine measure_mono_null ?_ (measure_iUnion_null fun i => h i d hd)
  rintro x ⟨θ, hθ, rest⟩
  obtain ⟨i, hi⟩ := Set.mem_iUnion.1 hθ
  exact Set.mem_iUnion.2 ⟨i, θ, hi, rest⟩

/-- The union of two null sets of parameters is null. -/
theorem IsGenericNull.union {A B : Set (MetricData E)} (hA : IsGenericNull N A)
    (hB : IsGenericNull N B) : IsGenericNull N (A ∪ B) := by
  rw [Set.union_eq_iUnion]
  exact IsGenericNull.iUnion fun b => by cases b <;> assumption

/-- The empty set of parameters is null. -/
theorem isGenericNull_empty : IsGenericNull N ∅ := by
  intro d _
  have : {x : (E → ℝ) × (E → ℝ) | ∃ θ ∈ (∅ : Set (MetricData E)), N.IsMetric θ ∧ θ.length = x.1 ∧
      ∀ e, N.IsHybridArc e → e ≠ d (N.graph.target e) → θ.inheritance e = x.2 e} = ∅ := by
    ext x
    simp
  rw [this, measure_empty]

end RootedNetwork

/-- A sum over the arcs with the target of `e`, split at `e`. -/
private theorem sum_target_eq_add (γ : E → ℝ) (e : E) :
    (∑ f, if N.graph.target f = N.graph.target e then γ f else 0) =
      γ e + ∑ f ∈ univ.filter (fun f => N.graph.target f = N.graph.target e ∧ f ≠ e), γ f := by
  rw [← sum_filter, ← add_sum_erase _ _
    (mem_filter.2 ⟨mem_univ e, rfl⟩ : e ∈ univ.filter (fun f => N.graph.target f = N.graph.target e))]
  congr 1
  refine sum_congr ?_ fun _ _ => rfl
  ext f
  simp only [mem_erase, mem_filter, mem_univ, true_and]
  tauto

/-- **Every normalized parameter is reached by the coordinates**, for every choice `d` of the left-out
parents: at the coordinates given by its own lengths and inheritance. So a witness on the boundary is a
point of the coordinates of `IsGenericNull`. -/
theorem coordMetric_self {θ : MetricData E} (hθ : N.IsNormalized θ) (d : V → E) :
    coordMetric N d θ.length θ.inheritance = θ := by
  have hinh : (coordMetric N d θ.length θ.inheritance).inheritance = θ.inheritance := by
    funext e
    by_cases he : N.IsHybridArc e
    · by_cases hde : e = d (N.graph.target e)
      · rw [coordMetric_inheritance_of_eq he hde]
        have hs := hθ.2 _ he
        rw [sum_target_eq_add θ.inheritance e] at hs
        linarith
      · exact coordMetric_inheritance_of_ne he hde
    · rw [coordMetric_inheritance_of_not_isHybridArc he]
      refine (hθ.1 e ?_).symm
      have hpos : 0 < N.graph.indegree (N.graph.target e) :=
        (Set.ncard_pos (Set.toFinite _)).2 ⟨e, rfl⟩
      unfold IsHybridArc at he
      unfold IsTreeArc
      omega
  exact congrArg₂ MetricData.mk rfl hinh

namespace RootedNetwork

/-- **The analytic argument.** A function of the parameters that is analytic in the coordinates of
`IsGenericNull`, for every choice of the left-out parents, and nonzero at some normalized parameters,
vanishes only on a null set of valid parameters. -/
theorem isGenericNull_of_analyticOnNhd {F : MetricData E → ℝ}
    (hF : ∀ d : V → E, AnalyticOnNhd ℝ (fun x : (E → ℝ) × (E → ℝ) => F (coordMetric N d x.1 x.2))
      Set.univ) {θ₀ : MetricData E} (hθ₀ : N.IsNormalized θ₀) (h : F θ₀ ≠ 0) :
    IsGenericNull N {θ | N.IsMetric θ ∧ F θ = 0} := by
  intro d _
  have hw : F (coordMetric N d θ₀.length θ₀.inheritance) ≠ 0 := by
    rwa [coordMetric_self hθ₀ d]
  refine measure_mono_null ?_
    (AnalyticOnNhd.prod_pi_volume_setOf_eq_zero (hF d) ⟨(θ₀.length, θ₀.inheritance), hw⟩)
  rintro x ⟨θ, ⟨-, hzero⟩, hθ, hℓ, hg⟩
  rw [Set.mem_ofPred_eq, ← eq_coordMetric hθ hℓ hg]
  exact hzero

/-- Two concordance factors that differ at some normalized parameters differ at generic parameters. -/
theorem isGenericNull_nmscCF_eq [Fintype V] [Fintype X] [DecidableEq X] {r r' : QuartetTree X}
    {θ₀ : MetricData E} (hθ₀ : N.IsNormalized θ₀) (h : nmscCF N θ₀ 0 r ≠ nmscCF N θ₀ 0 r') :
    IsGenericNull N {θ | N.IsMetric θ ∧ nmscCF N θ 0 r = nmscCF N θ 0 r'} :=
  (isGenericNull_of_analyticOnNhd (F := fun θ => nmscCF N θ 0 r - nmscCF N θ 0 r')
    (fun d => (analyticOnNhd_nmscCF_coordMetric N d 0 r).sub
      (analyticOnNhd_nmscCF_coordMetric N d 0 r')) hθ₀ (sub_ne_zero.2 h)).mono
    fun _ hθ => ⟨hθ.1, sub_eq_zero.2 hθ.2⟩

end RootedNetwork

end Phylogenetics
