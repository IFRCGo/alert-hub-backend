import json
import csv

# ## Transform data to a csv file
# # id: districtName (GID_1)
# # name: name of administrative level (NAME_1)
# # country: foreign key (country iso3)
# # polygon: polygon string

# INPUT_FILE_PATH = '../TestData/world.geojson'
INPUT_FILE_PATH = "../TestData/countries/AFG/afg.geojson"

# Load JSON data from the file
with open(INPUT_FILE_PATH, "r") as input_file:
    data = json.load(input_file)

admin1_data = []
for item in data['features']:
    admin1_item = {'id': item['properties']['GID_1'], 'name': item['properties']['NAME_1'],
                   'country': item['properties']['GID_0'],
                   'polygon': item['geometry']['coordinates']}
    admin1_data.append(admin1_item)

OUTPUT_FILE_PATH = "../TestData/countries/AFG/afg.csv"
with open(OUTPUT_FILE_PATH, "x", newline="") as output_file:
    fieldnames = ["id", "name", "country", "polygon"]
    writer = csv.DictWriter(output_file,
                            fieldnames=fieldnames)

    # Write the header (field names)
    writer.writeheader()

    # Write the data rows
    for row in admin1_data:
        writer.writerow(row)
