# CEX Project

This repository contains the code used for my Master's final project. 
Some scritps, get_evaluation_metrics.py, generate_new_xml.py, meta_eval.py, retrieve_jats_metadata.py and json_to_tei_anystyle.py have been reused from a previous research (Alessia Cioffi. (2022). Code for converting different formats to TEI XML and evaluating results (1.0). Zenodo. https://doi.org/10.5281/zenodo.6182128), but have been modified and corrected for the present research purposes.

Other scripts, get_evaluation_metrics_outcite.py, json_to_tei_outcite.py and refobjs_to_xml.py, have been newly created. 

The files can be used as follows:
- requirements.txt is used to set the work environment.
- get_evaluation_metrics.py is the evaluation code. It can be run after having extracted the references with one reference extraction tool (e.g. Grobid or Anystyle). It makes use of other two files, generate_new_xml.py and retrieve_jats_metadata.py.
- meta_eval.py is called by get_evaluation_metrics.py with the purpose of comparing the values of the output and the ones of the gold standard.
- get_evaluation_metrics_outcite is the evaluation code for the output files obtained using Outcite.
- json_to_tei_anystyle.py is used to translate the output files of Anystyle from JSON format to XML.
- json_to_tei_outcite.py is used to translate the output files of Outcite from JSON format to XML.
- refobjs_to_xml.py is used to crawl the Outcite Index (ad hoc created on the Outcite servers for the present research) and obtain as output a JSON file per file processed.
