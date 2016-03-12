from collections import defaultdict
import urllib.request
import os
import re

# Helper for making filenames in work dir
def filename(work_path, filename, extension):
    return os.path.join(work_dir, "{0}.{1}".format(filename,extension))

csv_separator = ";"

# Create work dir
script_dir = os.path.dirname(os.path.realpath(__file__))
work_dir = os.path.join(script_dir, 'work')
if not os.path.exists(work_dir):
    os.makedirs(work_dir)

# Set filenames
filename_base = 'ml_categories'
filename_pdf = filename(work_dir, filename_base, 'pdf')
filename_txt = filename(work_dir, filename_base, 'txt')
filename_alphabetical_csv = filename(work_dir, filename_base + 'alphabetical', 'csv')
filename_grouped_csv = filename(work_dir, filename_base + '_grouped', 'csv')

# Fetch pdf and write to file
ml_pdf_url = 'http://www.belastingdienst.nl/bibliotheek/handboeken/html/boeken/HVGEM/images/ati_628772970.pdf'
pdf_bytes = urllib.request.urlopen(ml_pdf_url).read()
pdf_file = open(filename_pdf, 'wb')
pdf_file.write(pdf_bytes)

# Convert PDF to TXT using shell util `pdftotext`
pdf_to_text_cmd = "pdftotext {0} {1}".format(filename_pdf, filename_txt)
print("Executing '{0}'".format(pdf_to_text_cmd))
os.system(pdf_to_text_cmd)

# Parse categories and write to alphabetical 
txt_file = open(filename_txt, 'r')
csv_file = open(filename_alphabetical_csv, 'w')
regex = re.compile("([^.]+) \.+\s*ML([0-9]+)")

csv_file.write("ML category; ML number; Item")
ml_cats = defaultdict(list)

for n, line in enumerate(txt_file):
    match = regex.match(line)
    if(match is not None):
        ml_number = match.group(2)
        ml_item = match.group(1)
        print("Line {0} matches: ML {1} has {2}".format(n, ml_number, ml_item))
        csv_file.write("ML{1}{0}{1}{0}{2}{0}".format(csv_separator, ml_number, ml_item))
        ml_cats[ml_number].append(ml_item)

for key in ml_cats.keys():
    print("ML{1}{0}{2}".format(csv_separator, key, csv_separator.join(ml_cats[key])))