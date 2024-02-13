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

def is_utf8(filename):
    with open(filename, 'rb') as f:
        try:
            f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

def is_large_file(filename, size_limit):
    return os.path.getsize(filename) > size_limit
        
def split_xml(input_files, output_dir, max_file_size, split_file_size):
    for input_file in input_files:
        namespace, release = extract_namespace_and_release(input_file)
        version = release.replace('.', '_')
        if release == "3.0" and is_utf8(input_file) and is_large_file(input_file, max_file_size):
            output_dir_archive = os.path.join(os.path.dirname(input_file), "archive")
            os.makedirs(output_dir_archive, exist_ok=True)

            with open(input_file, 'r') as f:
                context = ET.iterparse(f, events=("start",))
                _, root = next(context)
                header = root[0]

                # Initialize variables
                onix_message = ET.Element('ONIXmessage', {'xmlns': namespace, 'release': release})
                onix_message.append(header)
                current_file_size = len(ET.tostring(onix_message, encoding='utf-8'))
                i = 1

                for event, elem in context:
                    if elem.tag.endswith('}product'):
                        onix_message.append(elem)
                        elem_string = ET.tostring(elem, encoding='utf-8')
                        current_file_size += len(elem_string)

                        # Check if the file size limit is exceeded
                        if current_file_size >= split_file_size:
                            clean_onix_message(onix_message)
                            output_filename = f"Orig_{version}_{os.path.splitext(os.path.basename(input_file))[0]}_{i}.xml"
                            output_file = os.path.join(output_dir, output_filename)
                            with open(output_file, 'wb') as out_f:
                                out_f.write(ET.tostring(onix_message, encoding='utf-8'))
                            i += 1  # Increment output filename
                            onix_message.clear()
                            onix_message = ET.Element('ONIXmessage', {'xmlns': namespace, 'release': release})  # Add namespace and release
                            onix_message.append(header)
                            current_file_size = len(ET.tostring(onix_message, encoding='utf-8'))

                # Write remaining products if any
                if len(onix_message) > 1:  # Check if there are products in the message
                    clean_onix_message(onix_message)
                    output_filename = f"Orig_{version}_{os.path.splitext(os.path.basename(input_file))[0]}_{i}.xml"
                    output_file = os.path.join(output_dir, output_filename)
                    with open(output_file, 'wb') as out_f:
                        out_f.write(ET.tostring(onix_message, encoding='utf-8'))

            shutil.move(input_file, os.path.join(output_dir_archive, os.path.basename(input_file)))

        else:
            output_filename = f"Orig_{version}_{os.path.splitext(os.path.basename(input_file))[0]}.xml"
            shutil.move(input_file, os.path.join(output_dir, output_filename))

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script_name.py input_path output_path max_file_size split_file_size")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    max_file_size = int(sys.argv[3])
    split_file_size = int(sys.argv[4])

    os.makedirs(output_path, exist_ok=True)

    while True:
        input_files = glob.glob(os.path.join(input_path, "*.xml"))
        if input_files:
            split_xml(input_files, output_path, max_file_size, split_file_size)
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
#     max_file_size = 500 * 1024 * 1024
#     split_file_size = 200 * 1024 * 1024
#     os.makedirs(output_dir, exist_ok=True)
#     split_xml(input_files, output_dir)



#Debug --> python3 fs.py data/IN/ data/OUT/ $((500*1024*1024)) $((200*1024*1024))
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