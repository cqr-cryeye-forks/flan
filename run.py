import json
import os
import subprocess
import datetime
import shutil


# Function to upload files to cloud storage
def upload_file(filepath):
    global upload
    if not upload:
        return
    elif upload == "aws":
        subprocess.run(['python', '/aws_push.py', filepath])
    elif upload == "gcp":
        subprocess.run(['python', '/gcp_push.py', filepath])


# Function to get a filename-safe version of a string
def get_filename(input_str):
    return input_str.replace('/', '-')


def main():
    global upload
    # Get the current time formatted as "YYYY.MM.DD-HH.MM"
    current_time = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M")

    # Set root directory based on the upload variable
    upload = os.getenv('upload')
    if not upload:
        root_dir = "shared/"
    else:
        root_dir = "/"
        os.makedirs("/xml_files", exist_ok=True)
        os.makedirs("/reports", exist_ok=True)

    # Set report extension, default to "tex" if format is not specified
    report_extension = os.getenv('format', 'tex')

    # Define directories and report file
    xml_dir = f"xml_files/{current_time}"
    report_file = "reports/output.json"

    DIR_XML = os.path.join(root_dir, xml_dir)
    OUTPUT_JSON = os.path.join(root_dir, report_file)

    # Create necessary directories
    os.makedirs(DIR_XML, exist_ok=True)

    # Read lines from the input file and process each IP
    with open('shared/ips.txt') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            filename = f"{get_filename(line)}.xml"
            filepath = os.path.join(DIR_XML, filename)
            subprocess.run([
                'nmap', '-sV', '-oX', filepath, '-oN', '-', '-v1',
                '--script=vulners/vulners.nse', line
            ])
            upload_file(filepath)

    # Generate the output report
    subprocess.run([
        'python', 'output_report.py',
        DIR_XML,
        OUTPUT_JSON,
        'shared/ips.txt'
    ])

    # Apply text replacements for LaTeX if the report extension is "tex"
    if report_extension == 'tex':
        replacements = {
            '_': '\\_',
            '$': '\\$',
            '#': '\\#',
            '%': '\\%'
        }
        if report_file:
            with open(OUTPUT_JSON, 'r') as jf1:
                content = jf1.read()
            for old, new in replacements.items():
                content = content.replace(old, new)
            with open(OUTPUT_JSON, 'w') as jf2:
                json.dump(content, jf2, indent=2)
    # Upload the final report file
    # upload_file(OUTPUT_JSON)


if __name__ == '__main__':
    main()
