import os
import shutil
import glob
import xml.etree.ElementTree as ET
import sys

def remove_namespace_prefixes(xml_string):
    root = ET.fromstring(xml_string)
    for elem in root.iter():
        local_name = elem.tag.split('}')[-1]
        elem.tag = local_name
    return ET.tostring(root, encoding='unicode')

def extract_namespace_and_release(input_file):
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip().startswith('<ONIXmessage'):
                namespace = line.split('xmlns="')[1].split('"')[0]
                release = line.split('release="')[1].split('"')[0]
                return namespace, release

def split_xml(input_files, output_dir):
    for input_file in input_files:
        namespace, release = extract_namespace_and_release(input_file)

        tree = ET.parse(input_file)
        root = tree.getroot()
        child = root[1]

        for i, product in enumerate(root.findall(child.tag), start=1):
            # Create a new ONIXmessage element for each product
            onix_message = ET.Element('ONIXmessage')
            onix_message.set('xmlns', namespace)
            onix_message.set('release', release)

            # Append the current product to the ONIXmessage tree
            onix_message.append(root[0])  # Append header
            onix_message.append(product)

            # Convert the onix_message to string and remove namespace prefixes
            onix_message_str = remove_namespace_prefixes(ET.tostring(onix_message))

            # Generate a unique identifier for the output file name
            output_filename = f"{os.path.basename(input_file)}_{i}.xml"

            # Write the product XML to a file
            output_file = os.path.join(output_dir, output_filename)
            with open(output_file, 'w') as f:
                f.write(onix_message_str)

        # Move the input file to the archive directory
        archive_dir = os.path.join(os.path.dirname(input_file), "archive")
        os.makedirs(archive_dir, exist_ok=True)
        shutil.move(input_file, os.path.join(archive_dir, os.path.basename(input_file)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script_name.py input_path output_path")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    input_files = glob.glob(os.path.join(input_path, "*.xml"))

    os.makedirs(output_path, exist_ok=True)
    split_xml(input_files, output_path)




# if __name__ == "__main__":
#     input_files = glob.glob("data/IN/*.xml")
#     output_dir = "data/OUT"
#     os.makedirs(output_dir, exist_ok=True)
#     split_xml(input_files, output_dir)



#Test
    # if __name__ == "__main__":
    # if len(sys.argv) != 3:
    #     print("Usage: python script_name.py input_path output_path")
    #     sys.exit(1)

    # input_path = sys.argv[1]
    # output_path = sys.argv[2]

    # input_files = glob.glob(os.path.join(input_path, "*.xml"))
    # for input_file in input_files:
    #         tree = ET.parse(input_file)
    #         root = tree.getroot()
    #         child = root[1]
    #         items = root.findall(child.tag)[0].tag
    #         print(items)