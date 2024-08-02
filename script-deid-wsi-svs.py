"""Script to De Identify WSI images with .svs format"""
import argparse
import io
import logging
import shutil
import struct
import sys
import traceback
import uuid
from datetime import datetime
import os
import tifffile
import logging
import tiffparser


def main():
    """
    1. Read WSI .svs file from ./svs_image_files_to_deid folder
        1.1 Sample file -> ./svs_image_files_to_deid/sample.svs
    2. Create new name: 'W' + UUID4 + 'T' + Timestamp ISO format + Original file extension
        2.1 Sample new name -> W123e4567-e89b-12d3-a456-426614174000T2024-07-29121126547122.svs
    3. Create a copy of the image with the new name in ./svs_image_files_deid
    4. Logic if do not remove the label image from the WSI file
        4.1 Remove the label image
    5. Logic if do not update the image name and metadata
        5.1 Update file with new name.
        5.2 Update the metadata filename with Deid_Filename_Metadata in the image
    6. Move the image to the final location ./svs_image_files_deided

    Args:
        --filename: The name of the file to be de-identified (sample.svs)
        --remove_label_image: Remove the label image from the WSI file (Default: True)
        --update_image_name_and_metadata: Update the image name and metadata (Default: True)
        --verbose: Increase output verbosity

    Raises:
        err: The error occurred during the excution of the function
    """
    folder_path = "./svs_image_files_to_deid"
    final_location = "./svs_image_files_deided"
    actions_performed = 'Actions Performed: \n'
    parser = argparse.ArgumentParser(description='De Identify WSI images with .svs format')
    parser.add_argument('--filename', type=str, help='filename', required=True)
    parser.add_argument('--remove_label_image', type=str, choices=['True', 'False'], help='remove_label_image', default='True')
    parser.add_argument('--update_image_name_and_metadata', type=str,  choices=['True', 'False'], help='update_image_name_and_metadata', default='True')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.info(f"Start: Script to De Identify WSI images with .svs format for file: {args.filename}")

    try:
        deid_filename, deid_filename_metadata = generate_deid_filename(args.filename)
        logging.info("deid_filename and deid_filename_metadata are: %s, %s ", deid_filename, deid_filename_metadata)

        original_file_path = os.path.join(folder_path, args.filename)
        copy_file_path = os.path.join(folder_path, deid_filename)
        image_final_path = os.path.join(final_location, args.filename)

        copy_image_with_deid_filename(original_file_path, copy_file_path)
        logging.info("Image is copied to %s", copy_file_path)

        if eval(args.remove_label_image.lower().capitalize()):
            delete_label_image(copy_file_path)
            logging.info("Label is removed from the image %s\n", args.filename)
            actions_performed += '- Label removed from the image\n'

        if eval(args.update_image_name_and_metadata.lower().capitalize()):
            image_final_path = os.path.join(final_location, deid_filename)
            update_metadata_image_name(copy_file_path, deid_filename_metadata)

            with open(copy_file_path, 'rb') as stream:
                metadata = extract_metadata_from_stream(stream, deid_filename)
                logging.info("Metadata of the new image %s is\n\n %s \n\n", deid_filename, metadata)

            actions_performed += '- Metadata updated in the image\n'
            actions_performed += '- Image name updated in the metadata\n'

        move_image_to_final_location(copy_file_path, image_final_path)
        logging.info(f"Image is moved to {image_final_path}\n")
        logging.info(actions_performed)

    except Exception as err:
        logging.error("Couldn't process file: %s", args.filename)
        logging.error(err)
        logging.error(traceback.format_exc())
        raise err 

    finally:
        pass


def copy_image_with_deid_filename(original_file_path:str, copy_file_path:str)-> None:
    """
    Copy an image from the original file path to the copy file path.

    Args:
        original_file_path (str): The path of the original image file.
        copy_file_path (str): The path where the copied image file will be saved.
    """

    logging.info("Copying image from %s to %s", original_file_path, copy_file_path)
    os.makedirs(os.path.dirname(copy_file_path), exist_ok=True)
    shutil.copy(original_file_path, copy_file_path)


def move_image_to_final_location(copy_file_path:str, image_final_path:str)-> None:
    """
    Move the image copy from the copy file path to the final file path.

    Args:
        copy_file_path (str): The path of the copied image file.
        image_final_path (str): The path where the image file will be moved to.

    Returns:
        None
    """

    logging.info("Moving image from %s to %s\n", copy_file_path, image_final_path)
    os.makedirs(os.path.dirname(copy_file_path), exist_ok=True)
    os.makedirs(os.path.dirname(image_final_path), exist_ok=True)
    shutil.move(copy_file_path, image_final_path)


def extract_metadata_from_stream(stream: io.BufferedReader, stream_name: str)->dict:
    """
    Extracts metadata from a stream of TIFF images.

    Args:
        stream: The stream of TIFF images.
        stream_name: The name of the stream.

    Returns:
        A dictionary containing the extracted metadata.
    """

    metadata = {}

    with tifffile.TiffFile(stream, name=stream_name) as tif:
        page_metadatas = []
        for page in tif.pages:
            page_metadata = {}
            for tag in page.tags.values():
                name, value = tag.name, tag.value                   
                if not(len(str(value)) > 200 and name != "ImageDescription"):
                    page_metadata[name] = str(value)
            page_metadatas.append(page_metadata)
        metadata["pages"] = page_metadatas

    return metadata


def update_metadata_image_name(copy_file_path: str, deid_filename_metadata: str)-> None:
    """
    Updates the metadata of an image with the new image name.

    Args:
        copy_file_path: The path of the image file.
        deid_filename_metadata: The new image name in metadata

    Returns:
        None
    """

    fp = open(copy_file_path, 'r+b')
    logging.info(f"Able to open the local image: {copy_file_path} for editing metadata")
    t = tifffile.TiffFile(fp)

    org_description = t.pages[0].description
    str1 = org_description.split("|Filename = ", 1)

    f_name = str1[1].split("|", 1)
    t.pages[0].tags['ImageDescription'].overwrite(t.pages[0].description.replace(f_name[0], deid_filename_metadata))
    t.pages[1].tags['ImageDescription'].overwrite(t.pages[1].description.replace(f_name[0], deid_filename_metadata))
    fp.close()

    logging.info(f"Metadata update on the local image {copy_file_path} is complete.")


def generate_deid_filename(original_file_name: str)-> str:
    """Generates a unique file name for DeIdentified images.

    Args:
        original_file_extension (str): Original file extension of the image.

    Returns:
        str: DeIdentified file name as
        'W' + UUID4 + 'T' + Timestamp ISO format + Original file extension

    """
    unique_id = uuid.uuid4()
    now = datetime.now()
    time_string = now.strftime("%Y-%m-%d%H%M%S%f")

    deid_filename_in_metadata = 'W' + str(unique_id) + 'T' + time_string
    deid_filename = deid_filename_in_metadata + extract_file_extension(original_file_name)

    return deid_filename, deid_filename_in_metadata


def extract_file_extension(file_path: str)-> str:
    """This function takes a file path as an argument and returns the 
    file extension.

    Args:
        file_path (str): The entire file path with extension.

    Returns:
        str: The file extension like '.xyz'.
    """
    extension = file_path.split('.')[-1]

    return '.' + extension


def delete_label_image(slide_path: str)-> None:
    """
    Deletes the label image from a Whole Slide Image (WSI) file.

    Args:
        slide_path (str): The path to the WSI file.

    Raises:
        Exception: If the SVS format contains duplicate associated label images.

    Returns:
        None
    """

    image_type = 'label'

    fp = open(slide_path, 'r+b')
    t = tiffparser.TiffFile(fp)

    # logic here will depend on file type. AT2 and older SVS files have "label" and "macro"
    # strings in the page descriptions, which identifies the relevant pages to modify.
    # in contrast, the GT450 scanner creates svs files which do not have this, but the label
    # The header of the first page will contain a description that indicates which file type it is
    first_page=t.pages[0]
    filtered_pages=[]

    if 'Aperio Image Library' in first_page.description:
        filtered_pages = [page for page in t.pages if image_type in page.description]
        logging.info('Aperio Image Library')
    elif 'Aperio Leica Biosystems GT450' in first_page.description:
        logging.info('Aperio Leica Biosystems GT450')
        if image_type=='label':
            filtered_pages=[t.pages[-2]]
        else:
            filtered_pages=[t.pages[-1]]
    else:
        logging.info('Old-style labeled pages')
        filtered_pages = [page for page in t.pages if image_type in page.description]

    num_results = len(filtered_pages)

    if num_results > 1:
        raise Exception(f'Invalid SVS format: duplicate associated {image_type} images found')
    if num_results == 0:
        logging.info(f"No image of {image_type} in the WSI file; no need to delete it")
        return

    logging.info(f"1 image {image_type} has been identified to remove")
    page = filtered_pages[0]

    # get the list of IFDs for the various pages
    offsetformat = t.tiff.ifdoffsetformat
    offsetsize = t.tiff.ifdoffsetsize
    tagnoformat = t.tiff.tagnoformat
    tagnosize = t.tiff.tagnosize
    tagsize = t.tiff.tagsize
    unpack = struct.unpack

    logging.info('Finding IFD offsets')
    ifds = [{'this': p.offset} for p in t.pages]

    logging.info('Finding next IFD offsets')
    for p in ifds:
        logging.info(f"Finding next IFD offset for page at {p['this']}")
        fp.seek(p['this'])
        (num_tags,) = unpack(tagnoformat, fp.read(tagnosize))
        logging.info(f"Found {num_tags} tags in the image")

        fp.seek(num_tags*tagsize, 1)
        logging.info(f"Move forward to past tag definitions - Current offset is {fp.tell()}")

        p['next_ifd_offset'] = fp.tell()
        logging.info(f"Add the current location as the offset to the IFD of the next page - Next IFD offset is {p['next_ifd_offset']}")

        (p['next_ifd_value'],) = unpack(offsetformat, fp.read(offsetsize))
        logging.info(f"Read and save the value of the offset to the next page - Next IFD offset is {p['next_ifd_value']}")

    logging.info('Finding page to delete')
    pageifd = [i for i in ifds if i['this'] == page.offset][0]
    logging.info('Finding previous page')
    previfd = [i for i in ifds if i['next_ifd_value'] == page.offset]

    logging.info('Checking for errors')
    if(len(previfd) == 0):
        raise Exception('No page points to this one')
    else:
        previfd = previfd[0]

    offsets = page.tags['StripOffsets'].value
    bytecounts = page.tags['StripByteCounts'].value
    logging.info(f"Found {len(offsets)} strips in the image")
    logging.info(f"Found {len(bytecounts)} byte counts in the image")

    logging.info('Deleting pixel data from image strips')
    for (o, b) in zip(offsets, bytecounts):
        fp.seek(o)
        fp.write(b'\0'*b)

    logging.info('Deleting tag values')
    for key, tag in page.tags.items():
        fp.seek(tag.valueoffset)
        fp.write(b'\0'*tag.count)

    offsetsize = t.tiff.ifdoffsetsize
    offsetformat = t.tiff.ifdoffsetformat
    pagebytes = (pageifd['next_ifd_offset']-pageifd['this'])+offsetsize

    logging.info('Deleting page header')
    fp.seek(pageifd['this'])
    fp.write(b'\0'*pagebytes)

    logging.info('Updating previous page to point to next page')
    fp.seek(previfd['next_ifd_offset'])
    fp.write(struct.pack(offsetformat, pageifd['next_ifd_value']))

    fp.close()


if __name__ == '__main__':
    sys.exit(main())
