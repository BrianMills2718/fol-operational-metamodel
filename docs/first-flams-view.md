# First FLAMS view query: Universal Quantification

This is the first actual **view** in the project that is defined as a query over the shared MMT/FLAMS ULO substrate rather than as a hand-authored graph.

The query is in `queries/universal-quantification-neighborhood.sparql`.

## Semantics of the view

Focus:

`latin:/?UniversalQuantification#`

Projection:

- every outgoing RDF relation from the focus;
- every incoming RDF relation to the focus;
- the RDF type(s) of neighboring resources when available;
- the authoritative named graph in which each statement occurs.

This is deliberately a one-hop semantic projection. Layout is not part of the query.

## Expected current LATIN2 relations

Against current MMT v27 / LATIN2 revision `48d8ce4d6d1bccbee8d746a3a519f07625ea2c5e`, the real `fol.brf` / `fol.nq` data includes at least these focus relations:

Outgoing:

- `UniversalQuantification rdf:type ulo:theory`
- `UniversalQuantification ulo:has-meta-theory LF`
- `UniversalQuantification ulo:include UntypedLogic`
- `UniversalQuantification ulo:specifies uforall`

Incoming:

- `UniversalQuantificationNDE ulo:include UniversalQuantification`
- `UniversalQuantificationNDI ulo:include UniversalQuantification`
- `IFOL ulo:include UniversalQuantification`
- `fol.omdoc ulo:specifies UniversalQuantification`

All of these statements occur in the MMT named graph:

`latin:/source/logic/fol_like/fol.mmt`

The declaration `latin:/?UniversalQuantification?uforall#` is itself typed as both `ulo:function` and `ulo:constant` in the current ULO export, so a renderer must support multiple types rather than forcing one node class.

## Architectural point

This query defines **what is in the view**. A layout engine can render the returned projection hierarchically, radially, as a DAG, or otherwise without changing the view definition.

The next query layer can parameterize the focus URI rather than hard-code Universal Quantification, then add reusable projections such as:

- theory construction (`ulo:include`, `ulo:has-meta-theory`);
- declarations (`ulo:specifies`);
- dependencies (`ulo:uses`);
- morphisms (`ulo:domain`, `ulo:codomain`);
- source/document provenance.
