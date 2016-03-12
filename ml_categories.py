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
filename_alphabetical_csv = filename(work_dir, filename_base + '_alphabetical', 'csv')
filename_categorised_csv = filename(work_dir, filename_base + '_categories', 'csv')
filename_grouped_csv = filename(work_dir, filename_base + '_grouped', 'csv')

# Fetch pdf and write to file
ml_pdf_url = 'http://www.belastingdienst.nl/bibliotheek/handboeken/html/boeken/HVGEM/images/ati_628772970.pdf'
pdf_bytes = urllib.request.urlopen(ml_pdf_url).read()
pdf_file = open(filename_pdf, 'wb')
pdf_file.write(pdf_bytes)

# Convert PDF to TXT using shell util `pdftotext`
print("Converting PDF to TXT")
pdf_to_text_cmd = "pdftotext {0} {1}".format(filename_pdf, filename_txt)
os.system(pdf_to_text_cmd)

# Parse categories and store in dictionaries
txt_file = open(filename_txt, 'r')
regex = re.compile("([^.]+) \.+\s*ML([0-9]+)")

ml_cats_grouped = defaultdict(list)
ml_cats = list()

for n, line in enumerate(txt_file):
    match = regex.match(line)
    if(match is not None):
        ml_number = int(match.group(2))
        ml_item = match.group(1)
        ml_cats_grouped[ml_number].append(ml_item)
        ml_cats.append( (ml_number, ml_item) )

# Write alphabetically ordered CSV
ml_cats_alphabetical = sorted(ml_cats, key=lambda x: (x[1], x[0]))
csv_file = open(filename_alphabetical_csv, 'w')
csv_file.write("ML category;ML number;Item\n")
for item in ml_cats_alphabetical:
    csv_file.write("ML{1}{0}{1}{0}{2}{0}\n".format(csv_separator, item[0], item[1]))

# Write category ordered CSV
ml_cats_categorised = sorted(ml_cats, key=lambda x: (x[0], x[1]))
csv_file = open(filename_categorised_csv, 'w')
csv_file.write("ML category;ML number;Item\n")
for item in ml_cats_categorised:
    csv_file.write("ML{1}{0}{1}{0}{2}{0}\n".format(csv_separator, item[0], item[1]))

# Write CSV with items grouped by category
csv_file = open(filename_grouped_csv, 'w')
csv_file.writelines("ML category;\n")
for key in ml_cats_grouped.keys():
    csv_file.writelines("ML{1}{0}{2}\n".format(csv_separator, key, csv_separator.join(ml_cats_grouped[key])))

print("Found {0} items in {1} categories in the ML list".format(len(ml_cats), len(ml_cats_grouped.keys())))