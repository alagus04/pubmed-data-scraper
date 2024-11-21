import requests
import xml.etree.ElementTree as ET
import csv

# Search for PMIDs
search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
search_params = {
    "db": "pubmed",
    "term": "cardiology machine learning",  # Query term
    "retmax": 100,        # Number of results to retrieve
    "retmode": "json",    # Return data in JSON format
}
response = requests.get(search_url, params=search_params)
search_results = response.json()
pmids = search_results["esearchresult"]["idlist"]  # Extract PMIDs
print("PMIDs:", pmids)

# Step 2: Fetch detailed metadata
fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
fetch_params = {
    "db": "pubmed",
    "id": ",".join(pmids),  # Comma-separated PMIDs
    "retmode": "xml",       # Return data in XML format
}
response = requests.get(fetch_url, params=fetch_params)
xml_data = response.text  # XML data as a string

# Step 3: Parse XML data
root = ET.fromstring(xml_data)

# Create a CSV file
csv_file = "trial2_pubmed_data.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow([
        "PMID", "Title", "Abstract", "Authors", "Journal", "Publication Year",
        "Keywords", "DOI", "Affiliations", "MeSH Terms", "Grant Support", "Publication Types"
    ])

    # Process each article
    for article, pmid in zip(root.findall(".//PubmedArticle"), pmids):
        # Title
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "N/A"

        # Abstract
        abstract_elem = article.find(".//AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else "N/A"

        # Authors
        authors = []
        for author in article.findall(".//Author"):
            firstname_elem = author.find("ForeName")
            lastname_elem = author.find("LastName")
            firstname = firstname_elem.text if firstname_elem is not None else ""
            lastname = lastname_elem.text if lastname_elem is not None else ""
            if firstname or lastname:  # Include only if there's at least one name part
                authors.append(f"{firstname} {lastname}".strip())

        # Journal Name
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else "N/A"

        # Publication Year
        pub_year_elem = article.find(".//PubDate/Year")
        pub_year = pub_year_elem.text if pub_year_elem is not None else "N/A"

        # Keywords
        keywords = [kw.text for kw in article.findall(".//Keyword")]
        keywords_str = "; ".join(keywords) if keywords else "N/A"

        # DOI
        doi_elem = article.find(".//ELocationID[@EIdType='doi']")
        doi = doi_elem.text if doi_elem is not None else "N/A"

        # Affiliations
        affiliations = []
        for author in article.findall(".//Author"):
            affiliation_elem = author.find(".//Affiliation")
            if affiliation_elem is not None:
                affiliations.append(affiliation_elem.text)
        affiliations_str = "; ".join(affiliations) if affiliations else "N/A"

        # MeSH Terms
        mesh_terms = [mesh.text for mesh in article.findall(".//MeshHeading/DescriptorName")]
        mesh_terms_str = "; ".join(mesh_terms) if mesh_terms else "N/A"

        # Grant Support
        grants = []
        for grant in article.findall(".//Grant"):
            grant_id_elem = grant.find("GrantID")
            agency_elem = grant.find("Agency")
            if grant_id_elem is not None and agency_elem is not None:
                grants.append(f"{grant_id_elem.text} ({agency_elem.text})")
        grants_str = "; ".join(grants) if grants else "N/A"

        # Publication Types
        publication_types = [ptype.text for ptype in article.findall(".//PublicationType")]
        publication_types_str = "; ".join(publication_types) if publication_types else "N/A"

        # Write to CSV
        writer.writerow([
            pmid, title, abstract, ", ".join(authors), journal, pub_year,
            keywords_str, doi, affiliations_str, mesh_terms_str, grants_str, publication_types_str
        ])

print(f"Data successfully written to {csv_file}")
