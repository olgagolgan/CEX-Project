from lxml import etree
import os
import json
from meta_eval import compare_meta, compare_single
import sys


# instructions
# name the input data folders as in the following example (e.g. with the name of the tool)
#       input_data = ['Grobid', 'Anystyle', etc.]
# path_to_gs corresponds to the path to the gold standard files, to which the input files will be compared
# path_to_output corresponds to the parent folder in which the input_data folders can be found. Remember to add a / to the end of the path!

input_data = ['anystyle_grobid_ref_xmlOUT']
text_file = input_data[0]

path_to_gs = '/Users/olga/My Drive (olgagolgan99@gmail.com)/2ndYear/tesi/goldStand_parsed/boh'
path_to_output = '/Users/olga/My Drive (olgagolgan99@gmail.com)/2ndYear/tesi/goldStand_parsed/parsed_output_files/'
types_l = [(['article', 'newspaper'], ['date', 'monogr-title', 'analytic-title', 'biblScope_unit_volume', 'biblScope_unit_page']),
           (['chapter', 'ebook-chapter', 'technical-report-chapter', 'proceeding', 'conference'], ['date', 'analytic-title', 'monogr-title']),
           (['book', 'ebook', 'manual', 'data-sheet', 'database', 'online-database', 'preprint', 'technical-report', 'software', 'standard', 'preprint'], ['date', 'monogr-title']),
           (['forthcoming-article', 'unpublished', 'grey-literature'], ['date', 'monogr-title', 'note']),
           (['patent'], ['date', 'monogr-title', 'idno_type_docNumber']),
           (['series'], ['date', 'series-title', 'monogr-title']),
           (['webpage'], ['date', 'ref'])
           ]
pars_except = {'Cermine': ['note', 'idno_type_docNumber', 'ref'],
               'Pdfssa4met': ['analytic-title', 'note', 'idno_type_docNumber', 'ref'],
               'ScienceParse': ['note', 'idno_type_docNumber', 'ref']}


def count_meta_per_ref(input_l, reference, meta_counter, limitation_list, grobid, max_aut):
    # create basic structures
    out_list = []
    cur_meta, count_aut = 0, 0
    equal = [('a', 'analytic'), ('m', 'monogr'), ('j', 'monogr'), ('s', 'series')]
    # enter each occurrence in the input structure
    for struct in input_l:
        # attribute the correct tag on the basis of the limitation list and grobid factors
        if limitation_list and not grobid:
            tag = './/'
        else:
            tag = './/{http://www.tei-c.org/ns/1.0}'
        subsect = reference.find(tag + struct)  # find the current structure
        # check all the elements of each section
        for child in subsect.getchildren():
            aut = False
            add_s = ''
            children_list = [child]
            if 'title' in child.tag:
                add_s += struct + '-'
            # retrieve the single elements which 'author' is composed of (forename and surname)
            elif 'author' in child.tag or 'editor' in child.tag:
                aut = True
                if child.find(tag + 'forename') is not None or child.find(tag + 'surname') is not None:
                    if child.find(tag + 'persName') is not None:
                        children_list = [a for a in child[0].getchildren()]
                        to_delete = []
                        for check in children_list:
                            if ('forename' in check.tag and check.get('type') is not None
                                    and check.get('type') != 'first') or 'genName' in check.tag:
                                to_delete.append(check)
                        for element in to_delete:
                            children_list.remove(element)
                    else:
                        children_list = [a for a in child.getchildren()]
                else:
                    children_list = [a for a in child.getchildren()]
                count_aut += len(children_list)
            if aut:
                temp = []
            else:
                temp = None
            for subchild in children_list:
                # if the child is inprint the focus must be moved to the subchildren of this node
                if 'imprint' in subchild.tag:
                    impr_n = 0  # counter for correct metadata in imprint
                    try:
                        imprint = subsect.find(tag + 'imprint')
                        for child2 in imprint.getchildren():  # iterate the analysis over the imprint node children
                            if not (child2.get('unit') == 'page' or 'date' in child2.tag):
                                t = child2.text
                            else:
                                if 'date' in child2.tag and child2.get('when') is not None:
                                    t = [child2.get('when'), child2.text]
                                else:
                                    if not child2.text or ('date' in child2.tag and child2.get('when') is None):
                                        t = [child2.get('from'), child2.get('to')]
                                    else:
                                        t = [child2.text]
                            add_s = ''
                            if 'biblScope' in child2.tag:
                                add_s += '_unit_' + child2.attrib['unit']
                            elif 'idno' in child2.tag:
                                add_s += '_type_' + child2.attrib['type']
                            if limitation_list is not None:
                                for name in limitation_list:
                                    if 'title' in subchild.tag:
                                        if 'level' in child2.attrib:
                                            tag_full = [d[1] for d in equal if child2.attrib['level'] == d[0]][
                                                       0] + '-title'
                                        else:
                                            tag_full = 'monogr-title'
                                    else:
                                        if not grobid:
                                            tag_full = child2.tag + add_s
                                        else:
                                            tag_full = child2.tag.split('}')[1] + add_s
                                    # if the tag of the current element is equal to one of the names add it to out_list
                                    # normal case of output is ['persName', ['forename', 'Mario'], ['surname', 'Rossi']]
                                    # if a persName without forename/surname occurs: ['persName', 'Mario Rossi']
                                    if tag_full == name:
                                        # impr_n += 1
                                        out_list.append([tag_full, t])
                                        break
                            else:
                                out_list.append([child2.tag.split('}')[1] + add_s, t])

                        cur_meta += len(imprint.getchildren())
                        cur_meta += impr_n
                    except AttributeError:
                        pass
                else:
                    t = subchild.text
                    try:
                        for name in limitation_list:
                            if 'title' in subchild.tag:
                                if 'level' in subchild.attrib:
                                    tag_full = [d[1] for d in equal if subchild.attrib['level'] == d[0]][0]+'-title'
                                else:
                                    tag_full = 'monogr-title'
                            else:
                                if not grobid:
                                    tag_full = subchild.tag
                                else:
                                    tag_full = subchild.tag.split('}')[1]
                            if tag_full == name or (tag_full in ['persName', 'author'] and name in ['surname', 'forename']):

                                if temp is None:
                                    cur_list = out_list
                                else:
                                    cur_list = temp

                                if tag_full == 'persName':
                                    cur_list.append(t)
                                    cur_meta += 1
                                else:
                                    cur_list.append([tag_full, t])
                                    cur_meta += 1
                                break
                    except TypeError:
                        if temp is None:
                            cur_list = out_list
                        else:
                            cur_list = temp
                        cur_list.append([add_s + subchild.tag.split('}')[1], t])
                        cur_meta += 1
            if temp is not None and len(temp):
                out_list.append(['persName', temp])
    # check if there are more authors in the output than in the input
    if max_aut is not None:
        if count_aut > max_aut:
            cur_meta -= (count_aut-max_aut)
    meta_counter += cur_meta
    return meta_counter, out_list, cur_meta


def get_selected_elements(reference, el_list, prefix, grobid):
    output = []
    if prefix:
        pre = '/{http://www.tei-c.org/ns/1.0}'
    else:
        pre = '/'
    for el in el_list[0]:
        a = ''
        if el == 'date' or el == 'biblScope_unit_page':
            out = []
            a = el
        else:
            out = ''
        path = './'
        for field in el.split('-'):
            if '_' in field:
                field = field.split('_')[0]+"[@"+field.split('_')[1]+"='"+field.split('_')[2]+"']"
            elif field == 'ref' and grobid:
                field = 'ptr'
            path += pre+field
        node = [ref for ref in reference.iterfind(path)]
        sec_pos = []
        try:
            # add to the list the required metadata
            if len(a):
                for r in node:
                    out = []
                    if a == 'date' and r.get('when') is not None:
                        out.extend([r.get('when'), r.text])
                    else:
                        if not r.text or (a == 'date' and r.get('when') is None):
                            out.extend([r.get('from'), r.get('to')])
                        else:
                            out.extend([r.text])
                    sec_pos.append(out)
            else:
                for r in node:
                    if r.text:
                        out = r.text
                        sec_pos.append(out)
                    elif 'ptr' in r.tag:
                        out += r.get('target')
                        sec_pos.append(out)
        except AttributeError:
            pass
        if sec_pos:
            output.append((el, sec_pos))
    return output


def get_metadata(cur_ref, out_l, elem_l):
    for meta in cur_ref:
        for option in elem_l:
            if option in meta.tag:
                out_l.append(option)
    return out_l


# in this function we go inside each specific file and extract its information
def get_single_data(out_file, gs_file, parser_name):
    print(gs_file)
    output = []
    # enter the gs and output xml with etree
    parser = etree.XMLParser(recover=True)
    gs_tree = etree.parse(gs_file, parser)
    out_tree = etree.parse(out_file, parser)
    gs_root = gs_tree.getroot()
    out_root = out_tree.getroot()
    # verify whether the output list is empty or not. For Grobid there is a different procedure (not only refs in file)
    refs = None
    if 'Grobid' in out_file:
        list_bibl_struct = out_root.find('.//{http://www.tei-c.org/ns/1.0}listBibl')
        refs = list(list_bibl_struct.getchildren())
        if len([child for child in refs]):
            iter_ref = [gs_root, out_root]
            # count total number of references in gs and in output and add it to output list (positions 0 and 1)
            for ref in iter_ref:
                if iter_ref.index(ref) == 0:
                    # total num of references is computed as the last reference id (only numeric part)
                    cur_id = ref[0][0][-1].attrib['{http://www.w3.org/XML/1998/namespace}id']
                    output.append(int(cur_id[1:]) + 1)
                else:
                    cur_id = refs[-1].attrib['{http://www.w3.org/XML/1998/namespace}id']
                    output.append(int(cur_id[1:]) + 1)
    else:
        if len([child for child in out_root[0][0]]):
            iter_ref = [gs_root, out_root]
            for f in iter_ref:
                # count total number of references in gs and in output and add it to output list (positions 0 and 1)
                cur_id = f[0][0][-1].attrib['{http://www.w3.org/XML/1998/namespace}id']
                output.append(int(cur_id[1:])+1)
        # if no reference is found: count only gs references and return the values to the calling function
        else:
            # return None in case no reference is retrieved its values are not counted in the total evaluation
            cur_id = gs_root[0][0][-1].attrib['{http://www.w3.org/XML/1998/namespace}id']
            output.append(int(cur_id[1:]) + 1)
            print('Get single data: (no ref found)', output)
            return output
    # looking for the number of correct references
    count_out = count_gs = 0  # references index in gs and output
    tot_gs_meta = tot_out_meta = corr_meta = tot_cor_ref = 0  # 4 out of 7 missing counters (meta + correct refs)
    tot_gs_texts = tot_out_texts = corr_texts = 0  # the last three missing counters (metadata content)
    compared = {}
    prev_type = ''
    last_found = 0  # index of the last identified correct reference in the gold standard
    while count_out < output[1] and count_gs < output[0]:  # funct continues until last reference in output is analysed
        cur_gs = gs_root[0][0][count_gs]  # current reference in gold standard
        if 'Grobid' in out_file:
            cur_out = refs[count_out]  # current reference in output file
        else:
            cur_out = out_root[0][0][count_out]  # current reference in output file
        cur_type = gs_root[0][0][count_gs].get('type')
        # we are inside one single function: check if the metadata exist
        # check if they both have the same macro sections
        gs_l = get_metadata(cur_gs, [], ['analytic', 'monogr', 'series'])
        out_l = get_metadata(cur_out, [], ['analytic', 'monogr', 'series'])
        if 'Grobid' in out_file:
            grobid = True
        else:
            grobid = False
        # check base metadata in gs (in ancillary function); output = dictionary with metadata:value
        vals = [t[1] for t in types_l if cur_type in t[0]]
        # on the basis of the parser, if some metadata cannot be identified exclude them from the list
        if parser_name in pars_except.keys():
            for val in pars_except[parser_name]:
                if val in vals:
                    vals[0].remove(val)
        # check necessary metadata and respective values in gs
        meta_to_compare = get_selected_elements(cur_gs, vals, True, False)
        # check if the respective metadata is present in the output file
        if len(meta_to_compare):
            keys = set([tup[0] for tup in meta_to_compare])
            compared = get_selected_elements(cur_out, [list(keys)], grobid, grobid)
            # compara values: do metadata coincide? Call an external function to verify it
            temporary_value, not_found = compare_meta(meta_to_compare, compared, cur_type)
        else:
            temporary_value, not_found = False, None
            print(cur_gs.get('{http://www.w3.org/XML/1998/namespace}id'))
        # we are inside the file: do necessary data coincide? In case it is so enter
        if temporary_value:
            tot_cor_ref += 1  # 1 point to correct references counter
            last_found += count_gs-last_found  # assign to the variable of last reference found the index of current ref
            count_gs += 1  # 1 point to gold standard references counter
            count_out += 1  # 1 point to output references counter
            # tot_gs_meta is summed with the number of metadata identified
            tot_gs_meta, gs_comp, cur_tot_gs = count_meta_per_ref(gs_l, cur_gs, tot_gs_meta, None, False, None)
            # tot_out_meta is summed with the number of metadata identified (max same metadata but may more occurrences)
            cur_keys = set([tup[0] for tup in gs_comp])
            for tup in gs_comp:
                if not 'forename' in cur_keys or not 'surname' in cur_keys:
                    if tup[0] == 'persName':
                        for sub in tup[1]:
                            cur_keys.add(sub[0])
                else:
                    break
            max_aut = []
            for element in gs_comp:
                if element[0] == 'persName':
                    max_aut.extend(element[1])
            tot_out_meta, out_comp, cur_tot_out = count_meta_per_ref(out_l, cur_out, tot_out_meta, cur_keys, grobid, len(max_aut))
            # intersection in order to get only the metadata that are in the gold standard
            comm = set([tup[0] for tup in gs_comp]).intersection(set([tup[0] for tup in out_comp]))
            # option in case persName in output (no deeper metadata) and forename and/or surname in gs
            persname = False
            if 'persName' in set([tup[0] for tup in out_comp]) and ('forename' in set([tup[0] for tup in gs_comp])
                                                                    or 'surname' in set([tup[0] for tup in gs_comp])):
                persname = True
                for name in ['forename', 'surname']:
                    if name in set([tup[0] for tup in gs_comp]):
                        comm.add(name)
            # in case the parser is able to identify persName and not name + surname it is counted as 1 missing data
            for com in comm:
                if com == 'forename' and persname:
                    com1 = 'forename'
                    com2 = 'persName'
                elif com == 'surname' and persname:
                    com1 = 'surname'
                    com2 = 'persName'
                else:
                    com1 = com
                    com2 = com
                # count the number of gs occurrences if there are more than in the output and vice versa
                if com1 == 'persName':
                    meta_num1, meta_num2 = 0, 0
                    lists = [gs_comp, out_comp]
                    for ll in lists:
                        for a in ll:
                            if a[0] == 'persName':
                                if isinstance(a[1], list):
                                    if lists.index(ll) == 0:
                                        meta_num1 += len(a[1])
                                    else:
                                        meta_num2 += len(a[1])
                                else:
                                    if lists.index(ll) == 0:
                                        meta_num1 += 1
                                    else:
                                        meta_num2 += 1
                    tot_meta_cur = meta_num1 - meta_num2
                else:
                    tot_meta_cur = [a[0] for a in gs_comp].count(com1) - [a[0] for a in out_comp].count(com2)
                if tot_meta_cur <= 0:
                    # Only the gs occurrences are counted, if there are more in the output they count for less precision
                    if com1 == 'persName':
                        for a in gs_comp:
                            if a[0] == 'persName':
                                if isinstance(a[1], list):
                                    corr_meta += len(a[1])
                                else:
                                    corr_meta += 1
                    else:
                        corr_meta += [a[0] for a in gs_comp].count(com1)
                else:
                    if com1 == 'persName':
                        for a in out_comp:
                            if a[0] == 'persName':
                                if isinstance(a[1], list):
                                    corr_meta += len(a[1])
                                else:
                                    corr_meta += 1
                    else:
                        corr_meta += [a[0] for a in out_comp].count(com2)
            # METADATA
            tot_gs_texts += cur_tot_gs  # the result should be identical to tot_gs_meta
            tot_out_texts += cur_tot_out  # the result should be identical to tot_gs_meta
            if not_found is None:  # if some data aren't found they shouldn't be considered correct here (only articles)
                corr_texts += len(compared)  # correctly found metadata in a previous passage
            else:
                corr_texts += len(compared)-len(not_found)  # correctly found metadata in a previous passage
            # find the remaining metadata for text metadata
            out = 0
            # loop to verify whether the metadata contents are the same
            while out < len(out_comp):  # counter for output reference
                gs = 0
                # if clause to check if that specific metadata has alreay been verified in a previous step
                if out_comp[out][0] not in set([tup[0] for tup in compared]):
                    while gs < len(gs_comp):  # counter for gold standard reference
                        # if the metadata texts are the same add one to correct texts
                        if gs_comp[gs][0] == 'persName' and out_comp[out][0] == 'persName':
                            both = 0
                            found = 0
                            if isinstance(out_comp[out][1][0], list):
                                for item1 in out_comp[out][1]:
                                    for item2 in gs_comp[gs][1]:
                                        # verify if surname and forename belong to same author, else it is not counted
                                        if item1[0] == item2[0]:
                                            if compare_single(item1[1], item2[1], item1[0], parser_name):
                                                found += 1
                                            else:
                                                both += 1
                                if both == 0:
                                    corr_texts += found
                                    gs += len(gs_comp)
                                else:
                                    gs += 1
                            else:  # handle the case in which only persName defines an author: ScienceParse, Scholarcy
                                for item1 in out_comp[out][1][0].split(' '):
                                    for item2 in gs_comp[gs][1]:
                                        if compare_single(item1, item2[1], item2[0], parser_name):
                                            found += 1
                                        else:
                                            both += 1
                                if both < 3:  # necessary since not known which are forename and surname, needed 4 tries
                                    corr_texts += 1  # in this case it can't be found: the out data counts as 1
                                    gs += len(gs_comp)
                                else:
                                    gs += 1
                        else:
                            if (gs_comp[gs][0] == out_comp[out][0] or (gs_comp[gs][0] in ['surname', 'forename'] and out_comp[out][0] == 'persName')) and \
                                    compare_single(gs_comp[gs][1], out_comp[out][1], gs_comp[gs][0], parser_name):
                                corr_texts += 1
                                gs += len(gs_comp)
                            else:
                                gs += 1
                out += 1

            compared = {}
            prev_type = ''
        # if the references are not the same
        else:
            count_gs += 1
            prev_type = cur_type
            if count_gs == output[0]:
                count_out += 1
                if last_found > 0:
                    count_gs = last_found + 1
                else:
                    count_gs = 0
                compared = {}
                prev_type = ''
    output.extend([tot_cor_ref, tot_gs_meta, tot_out_meta, corr_meta, tot_gs_texts, tot_out_texts, corr_texts])
    print('Get single data: ', output)
    return output


# compute the values and add them to the dictionary that will create the json file
def create_json(file_name, js_dict, values, index, parser_name):
    keys = [('ref', 'references'), ('meta', 'metadata'), ('text', 'content')]
    # create new citation
    pos, iter = 0, 0
    temp = [{}]
    output = {}
    while pos < 7:
        precision = round(values[2 + pos][1] / values[1 + pos][1], 2) if values[1 + pos][1] else 0
        recall = round(values[2 + pos][1] / values[0 + pos][1], 2) if values[0 + pos][1] else 0
        f_score = round((2 * (precision * recall) / (precision + recall)), 2) if precision or recall else 0
        new_dict = [{'precision': precision, 'recall': recall, 'f-score': f_score}]
        temp[0].update({keys[iter][1]: new_dict})
        pos += 3
        iter += 1
    output.update({file_name: temp})
    js_dict.update(output)
    print(output)
    return js_dict


# the objective is to count the values of each file and return them as a list, for input to the prior function
# second aim is creating a json file for each parser, including all the single papers and topics
def get_file_data(path, parser_name):
    output = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # list that will contain the final values of all the files of the dataset
    missing = []
    to_json = {}
    n = 0
    files_list = list(os.listdir(path))
    # section to verify whether there are missing files in the output files directory
    if len(files_list) == len(list(os.listdir(path_to_gs))):
        out_list = files_list
        gs_list = list(os.listdir(path_to_gs))
    else:
        gs = list(os.listdir(path_to_gs))
        out_list, gs_list = [], []
        c = 1
        while c in range(1, 57):
            found = False
            for item in files_list:
                if parser_name == 'Scholarcy':
                    str_search = '_'+str(c)+'.pdf_tei'
                else:
                    str_search = '_'+str(c)+'_'
                if str_search in item or 'z_notes_test'+str(c-54) in item:
                    out_list.append(files_list[files_list.index(item)])
                    for item2 in gs:
                        if item2.split('_')[1] == str(c)+'.xml' or 'z_notes_test'+str(c-54) in item2:
                            gs_list.append(gs[gs.index(item2)])
                            found = True
                            break
                if found:
                    break
            if not found:
                for item2 in gs:
                    if item2.split('_')[1] == str(c) + '.xml' or 'z_notes_test' + str(c - 54) in item2:
                        missing.append(gs[gs.index(item2)])
                        break
            c += 1
    # starts the actual analysis, out_l is used as reference since there may be changes in the number of references
    while n < len(out_list):  # select one by one the papers in the specified parser's output directory
        values = [['ref_tot_gs', 0], ['ref_tot_out', 0], ['ref_tot_corr', 0], ['meta_tot_gs', 0], ['meta_tot_out', 0],
                  ['meta_tot_corr', 0], ['text_tot_gs', 0], ['text_tot_out', 0], ['text_tot_corr', 0]]
        vals_to_sum = get_single_data(path + '/' + out_list[n], path_to_gs + '/' + gs_list[n], parser_name)
        if vals_to_sum is not None:  # it is true only in case no reference is in the output file
            inner = 0
            while inner < len(vals_to_sum):  # add the values returned by get_single_data to the list of lists
                values[inner][1] += vals_to_sum[inner]  # update the current state for the json
                output[inner] += vals_to_sum[inner]  # update the output list for get_parsr_data
                inner += 1
            create_json(os.listdir(path)[n], to_json, values, n, parser_name)
        else:
            missing.append(out_list[n])
        n += 1
# Compute Missing Files
    for file in missing:
        values = [['ref_tot_gs', 0], ['ref_tot_out', 0], ['ref_tot_corr', 0], ['meta_tot_gs', 0],
                  ['meta_tot_out', 0],
                  ['meta_tot_corr', 0], ['text_tot_gs', 0], ['text_tot_out', 0], ['text_tot_corr', 0]]
        parser = etree.XMLParser(recover=True)
        gs_tree = etree.parse(path_to_gs + '/' + file, parser)
        gs_root = gs_tree.getroot()
        cur_id = gs_root[0][0][-1].attrib['{http://www.w3.org/XML/1998/namespace}id']
        output[0] += int(cur_id[1:]) + 1  # adding this value to output in order to count the
        values[0][1] += int(cur_id[1:]) + 1
        create_json(file, to_json, values, n, parser_name)
        print('Get single data: ', [l[1] for l in values])
        n += 1
    print('Get file data: ', to_json, file=open(text_file + '_files.log', 'w'))
    if len(missing):
        print('Missing files: ', missing)
    print(output)
    return output


def get_parsr_data():
    output = []
    for tup in input_data:
        temp_out = [tup, {}]
        key_l = ['ref_tot_gs', 'ref_tot_out', 'ref_tot_corr', 'meta_tot_gs', 'meta_tot_out', 'meta_tot_corr',
                 'text_tot_gs', 'text_tot_out', 'text_tot_corr']
        # the output of the get_file_data funct is a list of the values to associate to the keys
        value_l = get_file_data(path_to_output+tup, tup)
        # while loop to associate the keys to the respective values
        n = 0
        while n < len(key_l):
            temp_out[1].update({key_l[n]: value_l[n]})
            n += 1
            # append the current final list to the comprehensive major list
        output.append(temp_out)
    return output


# compute precison, recall and f-score for each parser + print out a json file with the results
def compute_values():
    final_data = get_parsr_data()
    keys = [('ref', 'references'), ('meta', 'metadata'), ('text', 'content')]
    output = {}

    for parser in final_data:
        total_comput = [{}]
        for key in keys:
            precision = round(parser[1][key[0]+'_tot_corr'] / parser[1][key[0]+'_tot_out'], 2) if parser[1][key[0]+'_tot_out'] else 0
            recall = round(parser[1][key[0]+'_tot_corr'] / parser[1][key[0]+'_tot_gs'], 2) if parser[1][key[0]+'_tot_gs'] else 0
            f_score = round((2 * (precision * recall) / (precision + recall)), 2) if precision or recall else 0
            total_comput[0].update({key[1]: [{'precision': precision, 'recall': recall, 'f-score': f_score}]})
        output.update({parser[0]: total_comput})
    print('Compare values: ', output, file=open(text_file + '_overall.log', 'w'))


if __name__ == "__main__":
    compute_values()

