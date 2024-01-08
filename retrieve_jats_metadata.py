from lxml import etree
from generate_new_xml import generate_xml
import os


def check_ref_existence(input_xml, output_xml, is_struct_ref):
    # check the existence of the xml
    if os.path.exists(input_xml):

        # call the function which creates the output xml
        generate_xml(output_xml)

        # check if the input xml file is not empty
        if os.stat(input_xml).st_size > 0:
            parser = etree.XMLParser(recover=True)
            tree = etree.parse(input_xml, parser)


            if is_struct_ref:
                sect_list = ['back', 'ref-list']
                for sect in sect_list:
                    if len(tree.xpath('//'+sect)) > 0:
                        pass
                    else:

                        return None, 'No <'+sect+'> section found. The current file does not have a reference list.'

            return tree, None

        else:

            return None, 'File is empty'
    else:

        return None, 'No file found: {}'.format(input_xml)


def create_standard_reference(node, node_name, attr_key, attr_value, node_text, cur_counter):
    element = etree.SubElement(node, node_name)
    if attr_key and attr_value:
        n = 0
        while n < len(attr_key):
            element.attrib[attr_key[n]] = attr_value[n]
            n += 1
    if node_text:
        element.text = node_text
    cur_counter = cur_counter + 1
    return node, cur_counter
