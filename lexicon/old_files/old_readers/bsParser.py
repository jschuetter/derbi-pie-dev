from bs4 import BeautifulSoup

# Open the XML file and parse it with BeautifulSoup
with open('lewis.xml', 'r') as file:
    soup = BeautifulSoup(file, 'xml')

# Find and print all tags
print(soup)
for tag in soup.find_all():
    print(tag)