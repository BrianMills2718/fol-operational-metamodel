# Concept notes and references

The model follows the standard model-theoretic separation of syntax (signature, terms, formulas, formation) and semantics (structures, assignments, satisfaction). The semantic consequence clause quantifies over all structures and should not be confused with derivability in a proof calculus. The finite evaluator in this repository demonstrates satisfaction on one finite structure; it does not decide general semantic consequence, which ranges over arbitrary structures.

## Sources

- Herbert B. Enderton, *A Mathematical Introduction to Logic*, 2nd ed., Academic Press, 2001. Chapters 1–2 introduce first-order languages, interpretations, and truth.
- Wilfrid Hodges, *A Shorter Model Theory*, Cambridge University Press, 1997. Chapters 1–2 cover structures, satisfaction, and elementary notions of model theory.
- R. L. Constable et al., *Implementing Mathematics with the Nuprl Proof Development System*, Prentice-Hall, 1986. An influential account of logical frameworks and representing formal systems.
- Per Martin-Löf, *On the Meaning of the Logical Constants and the Justifications of the Logical Laws*, Nordic Journal of Philosophical Logic 1(1), 1996, pp. 11–60. A distinct proof-theoretic perspective on logical constants; included to clarify that this project specifies classical Tarskian semantics rather than adopting a type-theoretic foundation.

These sources motivate the concepts, not every field in the JSON schema. The `references` arrays express local metamodel dependencies for graphing and navigation.
