import csv
import os

def save_csv(data, filename):
    '''
    Save a list of Dict objects to 
    a CSV file, specified by `filename
    '''
    if not os.path.splitext(filename)[-1] == ".csv":
        raise ValueError("Please provide a valid CSV path")
        
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()  # Write header row
        writer.writerows(data)  # Write data rows