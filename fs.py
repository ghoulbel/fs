import os
import shutil
import glob
import xml.etree.ElementTree as ET
import sys
import time

def extract_namespace_and_release(input_file):
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip().startswith('<ONIXmessage'):
                namespace = line.split('xmlns="')[1].split('"')[0]
                release = line.split('release="')[1].split('"')[0]
                return namespace, release

def clean_onix_message(element):
    element.tag = element.tag.split('}')[-1]
    for child in element:
        clean_onix_message(child)

def split_xml(input_files, output_dir):
    for input_file in input_files:
        namespace, release = extract_namespace_and_release(input_file)

        output_dir_archive = os.path.join(os.path.dirname(input_file), "archive")
        os.makedirs(output_dir_archive, exist_ok=True)

        with open(input_file, 'r') as f:
            context = ET.iterparse(f, events=("start",))
            _, root = next(context)
            header = root[0]
            child = root[1]

            i = 1
            for event, elem in context:
                local_name = elem.tag.split('}')[-1]
                elem.tag = local_name
                if local_name == child.tag:
                    onix_message = ET.Element('ONIXmessage', {'xmlns': namespace, 'release': release})

                    onix_message.append(header)
                    onix_message.append(elem)

                    clean_onix_message(onix_message)

                    output_filename = f"OnixSplit_{os.path.splitext(os.path.basename(input_file))[0]}_{i}.xml"

                    output_file = os.path.join(output_dir, output_filename)
                    with open(output_file, 'w') as out_f:
                        out_f.write(ET.tostring(onix_message, encoding='unicode'))

                    i += 1
                    elem.clear()
                    onix_message.clear()
                    out_f.close()

        shutil.move(input_file, os.path.join(output_dir_archive, os.path.basename(input_file)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script_name.py input_path output_path")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    os.makedirs(output_path, exist_ok=True)

    while True:
        input_files = glob.glob(os.path.join(input_path, "*.xml"))
        if input_files:
            split_xml(input_files, output_path)
        time.sleep(15)



# def remove_namespace_prefixes(xml_string):
#     root = ET.fromstring(xml_string)
#     for elem in root.iter():
#         local_name = elem.tag.split('}')[-1]
#         elem.tag = local_name
#     return ET.tostring(root, encoding='unicode')


# if __name__ == "__main__":
#     input_files = glob.glob("data/IN/*.xml")
#     output_dir = "data/OUT"
#     os.makedirs(output_dir, exist_ok=True)
#     split_xml(input_files, output_dir)



#Debug
# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python script_name.py input_path output_path")
#         sys.exit(1)

#     input_path = sys.argv[1]
#     output_path = sys.argv[2]

#     input_files = glob.glob(os.path.join(input_path, "*.xml"))
# for input_file in input_files:
#         namespace, release = extract_namespace_and_release(input_file)

#         context = ET.iterparse(input_file, events=("start",))
#         _, root = next(context)

#         for event, elem in context:
#             local_name = elem.tag.split('}')[-1]
#             elem.tag = local_name
#             if elem.tag == root[1].tag:
#                 print(elem.tag)