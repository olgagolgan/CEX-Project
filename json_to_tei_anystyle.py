import json as JS
from lxml.etree import QName
from lxml import etree
import os.path
from generate_new_xml import generate_xml, get_time, add_to_xml
from retrieve_jats_metadata import create_standard_reference
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askdirectory
import pathlib




def create_citation(metadata_list, analyt_node, mono_node, imprint_node, series_node):
    title = venue = year = volume = issue = page_range = publisher = pubplace = uri = doi = series = 0
    for coupled_meta in metadata_list:
        if analyt_node is None:
            analyt_node = mono_node
# CHECK PER PARTICLE
        if (coupled_meta[0] == 'author' or coupled_meta[0] == 'editor') and 'others' not in coupled_meta[1].keys():
            if coupled_meta[0] == 'author':
                node = analyt_node
            else:
                node = mono_node
            author_node = etree.SubElement(node, coupled_meta[0])
            if 'family' in coupled_meta[1].keys() or 'given' in coupled_meta[1].keys():
                persname_element = etree.SubElement(author_node, 'persName')
            else:  # in case the key is 'literal'
                persname_element = author_node

            for key in coupled_meta[1].keys():
                if key == 'family':
                    new_node = 'surname'
                    etree.SubElement(persname_element, new_node).text = coupled_meta[1][key]
                else:
                    new_node = 'forename'
                    fnames = coupled_meta[1][key].replace(".", " ").split()
                    for ind, fname in enumerate(fnames):
                        node = etree.SubElement(persname_element, new_node)
                        node.text = fname
                        if ind == 0 and len(fnames) > 1:
                            node.attrib["type"] = "first"
                        elif ind == len(fnames)-1 and len(fnames) > 2:
                            node.attrib["type"] = "last"
                        elif len(fnames) > 1:
                            node.attrib["type"] = "middle"


        elif coupled_meta[0] == 'title':
            if analyt_node == mono_node:
                analyt_node, title = create_standard_reference(analyt_node, 'title', None, None, coupled_meta[1], title)
            else:
                analyt_node, title = create_standard_reference(analyt_node, 'title', ['level'], ['a'], coupled_meta[1], title)

        elif coupled_meta[0] == 'container-title':
            mono_node, source = create_standard_reference(mono_node, 'title', None, None, coupled_meta[1], venue)

        elif coupled_meta[0] == 'collection-title':
            series_node, series = create_standard_reference(series_node, 'title', ['level'], ['s'], coupled_meta[1], series)

        elif coupled_meta[0] == 'date':
            imprint_node, year = create_standard_reference(imprint_node, 'date', ['when'], [get_time(str(coupled_meta[1]))], str(coupled_meta[1]), year)

        elif coupled_meta[0] == 'volume':
            if series_node is None:
                imprint_node, volume = create_standard_reference(imprint_node, 'biblScope', ['unit'], ['volume'],
                                                                 coupled_meta[1], volume)
            else:
                series_node, volume = create_standard_reference(series_node, 'biblScope', ['unit'], ['volume'],
                                                                 coupled_meta[1], volume)

        elif coupled_meta[0] == 'issue':
            imprint_node, issue = create_standard_reference(imprint_node, 'biblScope', ['unit'], ['issue'], coupled_meta[1], issue)

        elif coupled_meta[0] == 'publisher':
            imprint_node, publisher = create_standard_reference(imprint_node, 'publisher', None, None, coupled_meta[1], publisher)

        elif coupled_meta[0] == 'location':
            imprint_node, pubplace = create_standard_reference(imprint_node, 'pubPlace', None, None, coupled_meta[1], pubplace)

        elif coupled_meta[0] == 'pages':
            if "–" in coupled_meta[1]:
                node = imprint_node
                page_node = etree.SubElement(node, "biblScope")
                prange = coupled_meta[1].split("–")
                print(prange)
                page_node.attrib["unit"] = "page"
                page_node.attrib["from"] = prange[0]
                page_node.attrib["to"] = prange[1]
            else:
                imprint_node, page_range = create_standard_reference(imprint_node, 'biblScope', ['unit'], ['page'], coupled_meta[1], page_range)

        elif coupled_meta[0] == 'doi':
            analyt_node, doi = create_standard_reference(analyt_node, 'idno', ['type'], ['DOI'], coupled_meta[1], doi)

        elif coupled_meta[0] == 'url':
            mono_node, uri = create_standard_reference(mono_node, 'ref', ['target'], [coupled_meta[1]], coupled_meta[1], uri)

        elif coupled_meta[0] == 'genre' or coupled_meta[0] == 'note':
            mono_node, uri = create_standard_reference(mono_node, 'note', None, None, coupled_meta[1], uri)

        else:
            print(coupled_meta)


def add_listbibl(tree, cit_id, metadata_list, analytic_var, series_var):
    root = tree.getroot()

    # create listBibl with respective id
    listbibl_element = etree.SubElement(root[0][0], 'biblStruct')
    listbibl_element.attrib[QName("http://www.w3.org/XML/1998/namespace", "id")] = "b"+str(cit_id)
    # create sections analytic and/or monograph
    analyt_node, series_node = None, None
    if analytic_var:
        analyt_node = etree.SubElement(listbibl_element, 'analytic')
    mono_node = etree.SubElement(listbibl_element, 'monogr')
    imprint_node = etree.SubElement(mono_node, 'imprint')
    if series_var:
        series_node = etree.SubElement(listbibl_element, 'series')
    # call the function create_citations to fill the sections
    create_citation(metadata_list, analyt_node, mono_node, imprint_node, series_node)


def anystyle_parser(infile, outfile):
    try:
        generate_xml(outfile)
        pub_list = ['article-journal', 'chapter', 'paper-conference']  # cases in which analytitc node is created

        # load the file and check if there are references in list
        with open(infile, encoding="utf8") as json_file:
            data = JS.load(json_file)
            if len(data):
                pass

            else:
                sys.exit('Ops, no bibliographic section found!')

            # check and list the metadata present in the input json file
            outtree = etree.parse(outfile)
            for ref in data:
                all_meta = []
                analytic_var, series_var = False, False
                keys = ref.keys()
                for field in keys:
                    # check if the reference type allows to create the analytitc section or not
                    if field == 'type' and ref[field] in pub_list:
                        analytic_var = True
                    # separate the metadata so that in the creation phase they are ready to be analysed
                    elif field != 'type':
                        if field == 'collection-title':
                            series_var = True
                        if len(ref[field]):
                            for value in ref[field]:
                                all_meta.append((field, value))
                        # the fields, if not present should not be identified, else counted as an empty data
                        else:
                            all_meta.append((field, ""))


                add_listbibl(outtree, data.index(ref), all_meta, analytic_var, series_var)
        add_to_xml(outtree, outfile)

    except FileNotFoundError:
        sys.exit('No file found: {}'.format(infile)+'. Check if the filepath and the file name are correct.')


# Driver Code
if __name__ == "__main__":
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    in_path = askopenfilenames()  # show an "Open" dialog box and select the input folder and the files to process
    out_path = askdirectory()  # show an "Open" dialog box and select the output folder
    for file in in_path:
        filename = pathlib.PurePath(file).name  # takes only the last part of the path which is the name of the file
        only_name = os.path.splitext(filename)[0]  # separate the name from the extension
        # creates the new file with the right extension and saves it into the selected output folder
        anystyle_parser(file, out_path + '/' + only_name + "_tei.xml")

#