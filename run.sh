#!/bin/bash

# Get the current time formatted as "YYYY.MM.DD-HH.MM"
current_time=$(date "+%Y.%m.%d-%H.%M")

# Set root directory based on the upload variable
if [ -z "$upload" ]; then
    root_dir=/shared/
else
    root_dir=/
    mkdir -p /xml_files
    mkdir -p /reports
fi

# Set report extension, default to "tex" if format is not specified
report_extension="${format:-tex}"

# Define directories and report file
xml_dir="/xml_files/$current_time"
report_file="/reports/output.json"

# Function to upload files to cloud storage
upload() {
    if [ -z "$upload" ]; then
        return
    elif [ "$upload" = "aws" ]; then
        python /aws_push.py "$1"
    elif [ "$upload" = "gcp" ]; then
        python /gcp_push.py "$1"
    fi
}

# Function to get a filename-safe version of a string
get_filename() {
    echo "$1" | tr / -
}

# Create necessary directories
mkdir -p "$root_dir$xml_dir"

# Read lines from the input file and process each IP
while IFS= read -r line; do
    current_time=$(date "+%Y.%m.%d-%H.%M.%S")
    filename=$(get_filename "$line").xml
    nmap -sV -oX "$root_dir$xml_dir/$filename" -oN - -v1 "$@" --script=vulners/vulners.nse "$line"
    upload "$xml_dir/$filename"
done < /shared/ips.txt

# Generate the output report
python /output_report.py "$root_dir$xml_dir" "$root_dir$report_file" /shared/ips.txt

# Apply text replacements for LaTeX if the report extension is "tex"
if [ "$report_extension" = "tex" ]; then
    sed -i 's/_/\\_/g' "$root_dir$report_file"
    sed -i 's/\$/\\\$/g' "$root_dir$report_file"
    sed -i 's/#/\\#/g' "$root_dir$report_file"
    sed -i 's/%/\\%/g' "$root_dir$report_file"
fi

# Upload the final report file
upload "$report_file"
