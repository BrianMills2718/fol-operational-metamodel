use crate::{
    ExternalArchive, MathArchive,
    manifest::RepositoryData,
    utils::{AsyncEngine, errors::BackendError},
};
use ftml_ontology::{domain::modules::Module, narrative::documents::Document};
use ftml_uris::{ArchiveUri, Language, UriName, UriPath};
use std::path::{Path, PathBuf};

#[derive(Debug)]
pub struct MmtRdfArchive {
    uri: ArchiveUri,
    path: PathBuf,
    graphs: Vec<(ulo::rdf_types::NamedNode, Vec<ulo::rdf_types::Triple>)>,
}

fn read_graphs(root: &Path) -> Result<
    Vec<(ulo::rdf_types::NamedNode, Vec<ulo::rdf_types::Triple>)>,
    String,
> {
    let mut ret = Vec::new();
    if !root.is_dir() {
        return Err(format!("MMT RDF directory does not exist: {}", root.display()));
    }

    for entry in walkdir::WalkDir::new(root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.file_type().is_file())
        .filter(|e| e.path().extension().and_then(|e| e.to_str()) == Some("nq"))
    {
        let file = std::fs::File::open(entry.path())
            .map_err(|e| format!("{}: {e}", entry.path().display()))?;
        let parser = oxigraph::io::RdfParser::from_format(oxigraph::io::RdfFormat::NQuads)
            .for_reader(std::io::BufReader::new(file));

        let mut graph = None;
        let mut triples = Vec::new();
        for quad in parser {
            let quad = quad.map_err(|e| format!("{}: {e}", entry.path().display()))?;
            let current = match quad.graph_name {
                ulo::rdf_types::GraphName::NamedNode(n) => n,
                ulo::rdf_types::GraphName::DefaultGraph => {
                    return Err(format!(
                        "{} contains a default-graph statement; MMT graph identity is required",
                        entry.path().display()
                    ));
                }
                ulo::rdf_types::GraphName::BlankNode(_) => {
                    return Err(format!(
                        "{} contains a blank-node graph name",
                        entry.path().display()
                    ));
                }
            };
            if let Some(expected) = &graph {
                if expected != &current {
                    return Err(format!(
                        "{} contains more than one named graph",
                        entry.path().display()
                    ));
                }
            } else {
                graph = Some(current);
            }
            triples.push(ulo::rdf_types::Triple {
                subject: quad.subject,
                predicate: quad.predicate,
                object: quad.object,
            });
        }
        if let Some(graph) = graph {
            ret.push((graph, triples));
        }
    }

    if ret.is_empty() {
        return Err(format!("no .nq files found below {}", root.display()));
    }
    Ok(ret)
}

fn make_new(data: RepositoryData, top_dir: &Path) -> Result<Box<dyn ExternalArchive>, String> {
    let relative = data
        .attributes
        .iter()
        .find(|(k, _)| k.as_ref() == "mmt-rdf-dir")
        .map(|(_, v)| v.as_ref())
        .unwrap_or("mmt-rdf");
    let rdf_dir = top_dir.join(relative);
    let graphs = read_graphs(&rdf_dir)?;
    Ok(Box::new(MmtRdfArchive {
        uri: data.uri,
        path: top_dir.to_path_buf(),
        graphs,
    }))
}

crate::archive_kind! { MMT_RDF {
    name: "mmt-rdf",
    make_new: make_new
}}

impl MathArchive for MmtRdfArchive {
    fn uri(&self) -> &ArchiveUri {
        &self.uri
    }

    fn path(&self) -> &Path {
        &self.path
    }

    fn is_meta(&self) -> bool {
        false
    }

    fn load_module(
        &self,
        _path: Option<&UriPath>,
        _name: &UriName,
    ) -> Result<Module, BackendError> {
        Err(BackendError::ArchiveNotFound(self.uri.clone()))
    }

    fn load_module_async<A: AsyncEngine>(
        &self,
        _path: Option<&UriPath>,
        _name: &UriName,
    ) -> impl Future<Output = Result<Module, BackendError>> + 'static + use<A> {
        let uri = self.uri.clone();
        async move { Err(BackendError::ArchiveNotFound(uri)) }
    }
}

impl ExternalArchive for MmtRdfArchive {
    fn load_document(
        &self,
        _path: Option<&UriPath>,
        _name: &str,
        _language: Language,
    ) -> Option<Document> {
        None
    }

    fn relational_graphs(
        &self,
    ) -> Box<
        dyn Iterator<
                Item = (
                    ulo::rdf_types::NamedNode,
                    Box<dyn Iterator<Item = ulo::rdf_types::Triple>>,
                ),
            > + '_,
    > {
        Box::new(self.graphs.iter().map(|(graph, triples)| {
            (
                graph.clone(),
                Box::new(triples.clone().into_iter()) as Box<dyn Iterator<Item = _>>,
            )
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mmt_rdf_archive_kind_loads_real_fol_graph_into_sparql_store() {
        use crate::{
            Archive, ArchiveKind,
            triple_store::{RDFStore, sparql::QueryResults},
            utils::AllSyncEngine,
        };
        use ftml_uris::{ArchiveId, BaseUri};

        assert!(ArchiveKind::get("mmt-rdf").is_some());

        let root = std::env::var("MMT_FOL_NQUADS_DIR")
            .expect("set MMT_FOL_NQUADS_DIR for integration test");
        let root = Path::new(&root);
        let id: ArchiveId = "MMT/LATIN2".parse().expect("archive id");
        let base: BaseUri = "https://mathhub.info/".parse().expect("base URI");
        let data = RepositoryData {
            uri: base & id,
            attributes: vec![
                ("mmt-rdf-dir".into(), ".".into()),
            ],
            formats: smallvec::SmallVec::new(),
        };
        let ext = make_new(data, root).expect("construct mmt-rdf archive");
        let archive = Archive::Ext(&MMT_RDF, ext);

        let store = RDFStore::default();
        store.load_archives(&[archive]);

        let result = store
            .query_str::<AllSyncEngine>(
                r#"ASK WHERE {
                    GRAPH <latin:/source/logic/fol_like/fol.mmt> {
                        <latin:/?UniversalQuantification#>
                        <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
                        <http://mathhub.info/ulo#theory>
                    }
                }"#,
            )
            .expect("query FLAMS RDF store");
        assert!(matches!(&*result, QueryResults::Boolean(true)));
    }

    #[test]
    fn current_mmt_fol_nquads_preserve_authoritative_graph() {
        let path = std::env::var("MMT_FOL_NQUADS")
            .expect("set MMT_FOL_NQUADS for integration test");
        let root = Path::new(&path).parent().expect("fixture parent");
        let graphs = read_graphs(root).expect("read MMT N-Quads");
        let fol = graphs
            .iter()
            .find(|(g, _)| g.as_str() == "latin:/source/logic/fol_like/fol.mmt")
            .expect("FOL graph");
        assert_eq!(fol.1.len(), 423);
    }
}
