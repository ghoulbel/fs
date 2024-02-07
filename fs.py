import os
import shutil
import glob
import xml.etree.ElementTree as ET

def split_xml(input_files, output_dir):
    for input_file in input_files:
        tree = ET.parse(input_file)
        root = tree.getroot()
        child = root[0]
        items = root.findall(child.tag)

        for i, item in enumerate(items, start=1):
            output_file = os.path.join(output_dir, f"{os.path.basename(input_file)}_{i}.xml")
            with open(output_file, 'wb') as f:
                f.write(ET.tostring(item))

        archive_dir = os.path.join(os.path.dirname(input_file), "archive")
        os.makedirs(archive_dir, exist_ok=True)
        shutil.move(input_file, os.path.join(archive_dir, os.path.basename(input_file)))

if __name__ == "__main__":
    input_files = glob.glob("data/IN/*.xml")
    output_dir = "data/OUT"
    os.makedirs(output_dir, exist_ok=True)
    split_xml(input_files, output_dir)
