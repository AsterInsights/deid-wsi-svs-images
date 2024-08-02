## De-Identify WSI Images with .svs Format

This script is designed to de-identify Whole Slide Images (WSI) with the .svs format. It performs the following steps:

1. Reads the WSI .svs file from the `./svs_image_files_to_deid` folder.
2. Generates a new unique name for the image using a combination of a UUID, timestamp, and the original file extension.
3. Creates a copy of the image with the new name in the `./svs_image_files_to_deid` folder.
4. Removes the label image from the WSI file, if specified.
5. Updates the image name and metadata, if specified.
6. Moves the image to the final location in the `./svs_image_files_deided` folder with the specified name.

### How to Run

To run the script, follow these steps:

1. Make sure you have Python 3 installed on your system.
2. Open a terminal or command prompt.
3. Navigate to the directory where the script is located. In this case, it would be `./scripts/deid-wsi-svs-images/`.
4. Create a virtual environment by running the following command:

    ```
    python3 -m venv .venv
    ```

5. Activate the virtual environment. The command to activate the virtual environment depends on your operating system:

    - For Windows:

      ```
      .venv\Scripts\activate
      ```

    - For macOS/Linux:

      ```
      source .venv/bin/activate
      ```

6. Install any required dependencies by running:

    ```
    pip install -r requirements.txt
    ```

7. Place the WSI .svs file that you want to de-identify in the `svs_image_files_to_deid` folder.
8. Finally, run the script and pass the filename as an argument. The command would be:

```shell
python script-deid-wsi-svs.py --filename <filename> [--remove_label_image 'True'/'False'] [--update_image_name_and_metadata  'True'/'False'] [--verbose]
```

#### Possible Options -
To rename remove the label image and rename the image and update metadata to keep it in sync-

```python script-deid-wsi-svs.py --filename sample.svs ```

[or] 

```python script-deid-wsi-svs.py --filename sample.svs --remove_label_image True --update_image_name_and_metadata True```


To Remove Label Image only -

```python script-deid-wsi-svs.py --filename sample.svs --remove_label_image True --update_image_name_and_metadata False ```


To keep the Label Image and Rename the Image and update metadata to keep it in sync-

```python script-deid-wsi-svs.py --filename sample.svs --remove_label_image False --update_image_name_and_metadata True```


Replace `<filename>` with the name of the file you want to de-identify (e.g., `sample.svs`).

Optional arguments:
- `--remove_label_image`: Remove the label image from the WSI file. Options 'True' or 'False' (Default: 'True').
- `--update_image_name_and_metadata`: Do not update the image name and metadata. Options 'True' or 'False' (Default: 'True').
- `--verbose`: Increase output verbosity.

### Input/Output
The file should be in the folder `svs_image_files_to_deid` and the result will appear in `svs_image_files_deided` with the new name if specified:

W + UUID + T + Timestamp + Original file extension

(e.g., `W35784d32-299c-477e-a042-bfeffe790797T2023-04-18121126547122.svs`)

### Requirements

This script requires the following Python packages to be installed: See requirements.txt file.

### Note

The script assumes that the svs_image_files_to_deid, and svs_image_files_deided folders already exist in the same directory as the script. If they don't exist, please create them before running the script.

Please note that this script is specifically designed for de-identifying WSI images with the .svs format.
