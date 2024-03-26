import os
import xml.etree.ElementTree as ET
import sys
import time
import argparse
import shutil
import logging

# config

# logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S%z',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to stdout
    ]
)


# functions
# go through xml and read xml declaration identified by '?>'
def extract_xml_declaration(xml_file):
    with open(xml_file, 'r') as f:
        declaration = f.readline().strip()
    return declaration

#get namespace and release
def extract_namespace_and_release(xml_file):
    with open(xml_file, 'r') as f:
        for line in f:
            if line.strip().startswith('<ONIXmessage'):
                namespace = line.split('xmlns="')[1].split('"')[0]
                release = line.split('release="')[1].split('"')[0]
                return namespace, release

            
# check if it's utf-8 decoded
def is_utf8(filename):
    with open(filename, 'rb') as f:
        try:
            f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
        
#check filesize
def is_large_file(filename, size_limit):
    return os.path.getsize(filename) > size_limit

# check whether the file has a different size when checking the size after half a second
def is_file_being_written(file_path):
    
    file_size_1 = os.path.getsize(file_path)
    time.sleep(0.5)
    file_size_2 = os.path.getsize(file_path)
    
    if file_size_1 != file_size_2:
        print(f"assuming file: {file_path} still in transition since file of the file has changed in the last 0.2 seconds. Ignoring this file for this iteration.")
        return True
    return False

#clean namespace
def clean_onix_message(element):
    element.tag = element.tag.split('}')[-1]
    for child in element:
        clean_onix_message(child)


def split_xml(input_file_path, output_folder, max_file_size, split_file_size):
    namespace, release = extract_namespace_and_release(input_file_path)
    version = release.replace('.', '_')
    file_name = os.path.basename(input_file_path)
    file_name_no_extension = os.path.splitext(file_name)[0]
    xml_declaration = extract_xml_declaration(input_file_path)


    if not is_utf8(input_file_path):
        # Move to failed folder
        failed_folder = os.path.join(os.path.dirname(input_file_path), 'failed')
        os.makedirs(failed_folder, exist_ok=True)
        shutil.move(input_file_path, os.path.join(failed_folder, os.path.basename(input_file_path)))
        logging.info(f"Failed to process file: {os.path.join(failed_folder, os.path.basename(input_file_path))}")
        return False

    if not (is_large_file(input_file_path, max_file_size) or release == "3.0"):
        output_file_name = f"{output_folder}/Orig_{version}_{file_name}"
        shutil.copy(input_file_path, output_file_name)
        logging.info(f"File is small or not Version 3.0, just moved: {output_file_name}")
        return True
        
    if is_file_being_written(input_file_path):
        logging.info(f"File {input_file_path} is still being processed by another entity. Skipping it for splitting...")
        return False
    

    context = ET.iterparse(input_file_path, events=('start', 'end'))
    _, root = next(context)
    header = root[0]
    child = root[1]

    file_count = 0
    current_size = 0
    onix_message = ET.Element('ONIXmessage', {'xmlns': namespace, 'release': release})
    onix_message.append(header)
    clean_onix_message(onix_message)
    
    logging.info(f"Processing file: {input_file_path}...")

    for event, element in context:
        if event == 'end' and element.tag.endswith('}' + child.tag.split('}')[-1]):
            clean_onix_message(element)
            onix_message.append(element)
            current_size += sys.getsizeof(ET.tostring(element, encoding='utf-8'))
            
            if current_size >= split_file_size:
                output_file_name_tmp = f"{output_folder}/Orig_{version}_{file_name_no_extension}_{file_count}.xml.tmp"
                with open(output_file_name_tmp, 'wb') as output_file:
                    output_file.write((xml_declaration + '\n').encode('utf-8'))
                    output_file.write(ET.tostring(onix_message, encoding='utf-8'))
                output_file_name = output_file_name_tmp.split(".tmp")[0]
                shutil.move(output_file_name_tmp, output_file_name)

                logging.info(f"Saved file: {output_file_name_tmp}")

                onix_message.clear()
                onix_message = ET.Element('ONIXmessage', {'xmlns': namespace, 'release': release})
                onix_message.append(header)
                clean_onix_message(onix_message)
                file_count += 1
                current_size = 0

    if len(onix_message) > 0:  # Write the remaining elements to a file
        output_file_name_tmp = f"{output_folder}/Orig_{version}_{file_name_no_extension}_{file_count}.xml.tmp"
        with open(output_file_name_tmp, 'wb') as output_file:
            output_file.write((xml_declaration + '\n').encode('utf-8'))
            output_file.write(ET.tostring(onix_message, encoding='utf-8'))
        output_file_name = output_file_name_tmp.split(".tmp")[0]
        shutil.move(output_file_name_tmp, output_file_name)
    
    logging.info(f"Finished processing file: {input_file_path}")
    return True
    
# main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split XML file by element")
    parser.add_argument("input_folder", help="Path to the input files")
    parser.add_argument("output_folder", help="Folder to save the split XML files")
    parser.add_argument("max_file_size", type=int, help="Maximum file size in MB")
    parser.add_argument("split_file_size", type=int, help="Size at which to split the file in MB")

    args = parser.parse_args()

    # Check if all arguments are provided
    if not all((args.input_folder, args.output_folder, args.max_file_size, args.split_file_size)):
        parser.error("Please provide all four arguments: input-file, output-folder, max_file_size and split_file_size")
    # Check if there are more arguments
    if len(vars(args)) > 4:
        parser.error("Unexpected arguments provided. Please provide only input-file, output-folder, max_file_size and split_file_size.")
   

    # check input folder exists
    if not os.path.exists(args.input_folder):
        logging.error(f"input folder {args.input_folder} does not exists! Stopping execution...")
        sys.exit(1)
        
    # check output folder (<-- as this is intended to run in a container, fail if the output folder does not exists - otherwise the file will be written in the ephermal storage)
    if not os.path.exists(args.input_folder):
        print(f"output folder {args.output_folder} does not exists! Stopping execution...")
        sys.exit(1)


    logging.info(f"Started xml-splitter micro-service! Listening on folder: {args.input_folder}")

    # run the splitting execution
    while True:
        xml_files = [f for f in os.listdir(args.input_folder) if f.endswith(".xml")]
        
        for xml_file in xml_files:
            xml_file_path = f"{args.input_folder}/{xml_file}"
            file_is_split = split_xml(xml_file_path, args.output_folder, args.max_file_size * 1024 * 1024, args.split_file_size * 1024 * 1024)
            archive_path = os.path.join(os.path.dirname(xml_file_path), "archive")
            if file_is_split:
                os.makedirs(archive_path, exist_ok=True)
                shutil.move(xml_file_path, os.path.join(archive_path, xml_file))
        
        time.sleep(30)