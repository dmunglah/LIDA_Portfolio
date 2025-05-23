#!/usr/bin/env bash
# This script takes a DLC project identifier and attempt to run training upon it
# using the GPU nodes.

# Give up if any command fails:
set -e

# Set the code that defines what kind of job this is:
PROJECT_TYPE_CODE="DLCTN" # DeepLabCut Training Normal

# Set the run IO:
PROJECT_ID=$1
EPOCHS=$2
PROJECT_SLUG="${PROJECT_TYPE_CODE}_${PROJECT_ID}"
USER_ID=$USER
SCRIPTS_DIR="/users/${USER_ID}/github/HCMA_York"
BASE_DIR="/mnt/scratch/projects/biol-tf-2018/projects/P2025-TFD-QBLY"
DLC_PROJECT_DIR="${BASE_DIR}/dlc-projects/${PROJECT_ID}"
DLC_CONFIG_FILE="${DLC_PROJECT_DIR}/config.yaml"

#Is this job already running? 
if [ $(squeue --nohead --me -o "%j" | grep -c ${PROJECT_SLUG}) -gt 0 ] 
then
    echo "ERROR: ${PROJECT_SLUG} is already running" 
    exit 1
fi 

# Check we can see the DLC config file:
if [ ! -e ${DLC_CONFIG_FILE} ]
then
    echo "ERROR: config file ${DLC_CONFIG_FILE} not found"
    exit 1
fi
echo "config file is ${DLC_CONFIG_FILE}"

# Set & create the output log directory:
DLC_LOG_DIR="${DLC_PROJECT_DIR}/viking-logs"
mkdir -p ${DLC_LOG_DIR}
echo "viking log directory is ${DLC_LOG_DIR}"

# Define the script we're going to run:
DLC_TRAINING_EXEC="${SCRIPTS_DIR}/scripts/train-model -e -n ${EPOCHS} ${DLC_CONFIG_FILE}"
echo "training command is '${DLC_TRAINING_EXEC}'"

# Create a job name for this run:
TIMESTAMP=$(date '+%Y%m%dT%H%M%S')
JOB_NAME="${PROJECT_SLUG}_${TIMESTAMP}"
echo "viking job name is '${JOB_NAME}'"

# Submit the job to the queue:
sbatch \
    --job-name="${JOB_NAME}" \
    --partition=gpu_short \
    --gres=gpu:1 \
    --time=00-00:30:00 \
    --ntasks=1 \
    --mem=8G \
    --account=biol-tf-2018 \
    --output=${DLC_LOG_DIR}/output-${JOB_NAME}.log \
    --error=${DLC_LOG_DIR}/error-${JOB_NAME}.log \
    --wrap "${DLC_TRAINING_EXEC}"
