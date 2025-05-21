# LIDA_Portfolio
# HCMA York - Loading data

Home Cage Monitoring Algorithm Project - MRC Harwell - GenerationResearch.

## Running DeepLabCut on Viking

## Installation

Install miniconda3 in viking environment:

```bash
module load Miniconda3
```

Download DeepLabCut yaml file to 'resources' folder: 
```bash 
wget https://raw.githubusercontent.com/DeepLabCut/DeepLabCut/refs/heads/main/conda-environments/DEEPLABCUT.yaml -O ./resources/DEEPLABCUT.yaml
``` 

Create conda environment: 
```bash 
conda env create -f ./resources/DEEPLABCUT.yaml
```

## Using DeepLabCut (training) on Viking

Activate deeplabcut:

```bash
conda activate DEEPLABCUT
```

Load the DeepLabCut project folder onto viking (including config.yaml file) and change the directory of config file to new directory

 ```bash
 cd ../dlc-projects/
```

Move to scripts folder:

```bash
cd ./scripts
```

Run script:

```bash
./submit-training.sh [project ID] (e.g. Standardisation3-Heather-2025-02-28) [number of epochs]
```

# Formatting the CollectedData.csv file to account for various scorers (find_collected_data_files & format_user)

## find_collected_data_files
The script requires the full path to the DLC project and the output path for the txt file. 

To run: 

```bash 
./find_collected_data_files </full/path/to/your/DLC_project> </full/path/to/your/[file_name].txt> 
``` 

## format_user 
The script requires a scorer name and the txt file of CollectedData_[Scorer].csv paths 

To run:

```bash
./format_user <name> </full/path/to/your/[file_name].txt> 
```

# Formating the config.yaml file to account for various scorers (best_import_labels)

The script requires a scorer name, an input path (current project folder), and an output path (the new project folder name).

To run: 

```bash 
./best_import_labels <new_name> <current_project_folder> <new_project_folder_name>
``` 

When all scripts (find_collected_data_files & format_user & best_import_labels) are completed, run: 

```bash 
conda activate DEEPLABCUT
``` 
```
import deeplabcut 
```
```
deeplabcut.convertcsv2h5('path_to_config.yaml', scorer= 'experimenter')
``` 
