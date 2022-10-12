**CASBERT (Composite Annotation Search Using)**

An interface to search for cellml, variables, images, and sedml.

### Installation
```pip install git+https://github.com/napakalas/casbert.git```

### Using
  ```python
  from casbert import Searcher
  searcher = Searcher()
  
  query = 'basolateral plasma membrane'
  
  # searching variables
  searcher.searchVariables(query=query, top=10, minSim=0.1)
  
  # searching images
  searcher.searchImages(query=query, top=10, minSim=0.1)
  
  # searching components
  searcher.searchComponents(query=query, top=10, minSim=0.1)
  
  # searching cellml
  searcher.searchCellmls(query=query, top=10, minSim=0.1)
  
  # searching plots
  searcher.searchPlots(query=query, top=10, minSim=0.1)
  
  # searching sedml
  searcher.searchSedmls(query=query, top=10, minSim=0.1)
  ```
  
### Description
This package is used to search for variables, maths, biosimulation models, images, etc, in the Physiome Model Repository (PMR). The approach is named Compsite Annotation Search using BERT (CASBERT) which implements SentenceTransformer to represent entities and queries as embeddings. An entity is annotated with composite annotation to provide copmplete description. 

### Related repositories
[CASBERT experiment](https://github.com/napakalas/casbert-experiment.git)

[CASBERT index development](https://github.com/napakalas/casbert-indexer.git)

[Search Engine Implementation](https://github.com/napakalas/bmse.git)

### Search Engine Demo
BMSE: [http://search.bm-se.cloud.edu.au/](http://search.bm-se.cloud.edu.au/)
  