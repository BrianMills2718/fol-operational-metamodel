# Standards-derived metamodel layers

This project does not treat its own taxonomy as the authority for the anatomy of first-order logic.

## 1. Common Logic / ODM abstract syntax

ISO Common Logic defines an abstract syntax and model-theoretic semantics for a first-order-logic framework. The 2007 edition explicitly includes a UML metamodel of the abstract syntax. OMG ODM 1.1 publishes a normative machine-readable XMI metamodel synchronized with Common Logic.

The importer reads the ODM `CL` package directly. The current snapshot contains 29 UML classes and 27 associations, including `Sentence`, `Term`, `Name`, `AtomicSentence`, `QuantifiedSentence`, `UniversalQuantification`, `ExistentialQuantification`, `FunctionalTerm`, `Module`, and `Text`.

This layer is the preferred source for the syntax-side categories we previously discussed. It is not a project-authored FOL ontology.

## 2. Common Logic model-theoretic semantics

Common Logic separately standardizes semantic notions including interpretation, individual, universe/domain of discourse, universe of reference, denotation, semantic values of terms and sentences, satisfaction, validity, and entailment.

Those concepts are not assumed to be encoded by the ODM `CL` XMI package merely because they occur in the Common Logic standard. Until a machine-readable semantic metamodel is imported, semantic concepts must retain their normative-source provenance rather than being presented as ODM-XMI facts.

## 3. DOL / institution-level structure

OMG DOL provides a normative MOF metamodel for heterogeneous ontologies, models, specifications, and mappings. Institution theory supplies the more abstract logic interface: signatures, sentences, models, and satisfaction, with translations/reducts respecting the satisfaction condition.

The checked-in DOL `oms` package snapshot is a first standards-derived view of this layer. Additional DOL packages should be imported as needed rather than collapsed into one hand-designed hierarchy.

## 4. MMT / LATIN2 instances

MMT/LATIN2 remains the formal corpus. Its theories, declarations, includes, views, types, definitions, archivegraph, OMDoc, and relational indexes are instances/formal artifacts to be connected to the standards-derived metamodel layers.

## Bridge policy

A bridge such as “this LATIN2 declaration realizes Common Logic UniversalQuantification” is not automatically true merely because names look similar. Bridge mappings must be one of:

1. explicit in an upstream formal mapping;
2. mechanically derivable from formal structure with a documented rule; or
3. a project annotation clearly marked as such.

The visualization should therefore distinguish imported standard facts, imported formal-corpus facts, and bridge annotations.
