# K-SNACS Dataset and Guidelines
**Korean Semantic Network of Adposition and Case Supersense**

## Work in progress
This is a work in progress. Our goal is to add to the
[currently publicly available dataset](https://github.com/jenahwang/k-snacs)
and publish as an addition to Universal Dependencies in the CoNLL-U format, 
as well as to [Xposition](http://flat.nert.georgetown.edu/) in the augmented CoNLL-U-Lex
format complete with adposition annotation.

## Codebase
In addition to the dataset, as described below, we also share publicly code that results in the published dataset,
starting from our previously published dataset. 
In the code, we rely on Stanza parsers (Qi et al. 2020) to generate much of the syntactic and morphological analyses.
We share the code so that our dataset is replicable, flexible to new models, and transparent with linguistic decisions.

Running `run.sh` will produce `little_prince_ko.conllu` as well as all other byproducts:

`little_prince_ko.tsv` is our previously published dataset.
`little_prince_ko.json` is the same content, in json format.
`little_prince_raw_sentences.json` is a list of sentences, as inputs to Stanza parsers.
`little_prince_stanza.json` holds analyses from Stanza parsers.
`little_prince_merged.json` is the result of alignment between tokens from original annotations and Stanza tokens.
`little_prince_annotation_ready.json` is the UD-compliant version of k-SNACS, and
`little_prince_ko.conllu` is the same dataset in CoNLL-U form.

The UD-Compliant version is "annotation-ready" for multi-word-expression annotations, which we plan to release in
the CoNLL-U-LEX format.



## Dataset
**File:** [little_prince_ko.conllu](./little_prince_ko.conllu)

**Data Version:**  
* Current: 1.1
* Compatible with K-SNACS Guidelines v0.9

**Data Info:** 
* Title: 어린 왕자 (erin wangca) "The Little Prince"
* Author: Atoine de Saint-Exupéry 
* Original Language: French (Le Petit Prince)
* Genre: Childrens literature, Novella

**Column Description:**
Follows [CoNLL-U format](https://universaldependencies.org/format.html)
* ID: Word index, integer starting at 1 for each new sentence; may be a range for multiword tokens; may be a decimal number for empty nodes (decimal numbers can be lower than 1 but must be greater than 0).
* FORM: Word form or punctuation symbol.
* LEMMA: Lemma or stem of word form.
* UPOS: Universal part-of-speech tag.
* XPOS: Optional language-specific (or treebank-specific) part-of-speech / morphological tag; underscore if not available.
* FEATS: List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
* HEAD: Head of the current word, which is either a value of ID or zero (0).
* DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
* DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
* MISC: Any other annotation.

**License:**
This dataset's supersense annotations are licensed under CC BY 4.0 ([Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by/4.0/legalcode)).

## K-SNACS Guidelines

**File:** [k-snacs-guideline-appendix-v0.9.pdf](k-snacs-guideline-appendix-v0.9.pdf)

**Guideline Version:**
* Current: 0.9
* Compatible with [English SNACS v2.5](https://arxiv.org/abs/1704.02134)
* Please note that this document is an appendix to the above English SNACS guidelines, including only language-specific information that merits further detailing. For full definitions of labels and use cases, please refer to [English guidelines](https://arxiv.org/abs/1704.02134).

Here, we note that while UD datasets in Japanese and Hindi (where adpositions add to head words to form orthographic word)
separate adposition as separate, free-standing tokens, we annotate them under a special node in the enhance graph.
Each node is a separate line, so can receive annotations, and is consistent (adpositions receive ADP). This is due to
the highly agglutinative nature of Korean, and the consequent agreement among Korean linguists that we will not separate
adpositions (or other meaning-carrying sub-orthographic-word elements) as free-standing tokens for UD and similar projects.

## Citing this work
When using this data, please cite the following as appropriate:

Original k-SNACS annotations
[Hwang et al., 2020](https://www.aclweb.org/anthology/2020.dmr-1.6/):
> Hwang, Jena D., Hanwool Choe, Na-Rae Han, and Nathan Schneider. "K-SNACS: Annotating Korean adposition semantics." In Proceedings of the Second International Workshop on Designing Meaning Representations. 2020.

## K-SNACS Team

### Key Collaborators:

* [Jena Hwang](https://jdch00.github.io/) - Allen Institute for AI
* [Na-Rae Han](http://www.pitt.edu/~naraehan/) - University Pittsburgh 
* [Hanwool Choe](https://english.hku.hk/people/Faculty/258/Dr_Hanwool_Choe) - Hong Kong University
* [Hyun Min](https://aatlantise.science/georgetown/) - Georgetown University
* [Nathan Schneider](http://people.cs.georgetown.edu/nschneid/) - Georgetown University
* [Elli Ahn](https://rsea.fas.harvard.edu/people/elli-ahn) - Harvard University

### Special Thanks to:

* [Vivek Srikumar](https://svivek.com/) - University of Utah
* [Austin Blodgett](https://www.austinblodgett.org/) - Georgetown University


### This research was supported in part by:

* NSF award IIS-1812778
* BSF grant 2016375
