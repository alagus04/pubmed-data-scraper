import requests
import xml.etree.ElementTree as ET
import csv

# Step 1: Search for PMIDs
search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
search_params = {
    "db": "pubmed",
    "term": "immunization in health",
    "retmax": 1000,
    "retmode": "json",
    "api_key": "8b5ab4797f030e74eb1a9cc6456e0381a008"
}
response = requests.get(search_url, params=search_params)
if response.status_code != 200:
    print("HTTP Error:", response.status_code)
    print("Response:", response.text)
    exit()

search_results = response.json()
pmids = search_results.get("esearchresult", {}).get("idlist", [])
if not pmids:
    print("No PMIDs found.")
    exit()

print(f"Total PMIDs retrieved: {len(pmids)}")

# Step 2: Fetch metadata in chunks
fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
csv_file = "1pubmed_data_chunked.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow([
        "PMID", "Title", "Abstract", "Authors", "Journal", "Publication Year",
        "Keywords", "DOI", "Affiliations", "MeSH Terms", "Grant Support", "Publication Types"
    ])

    # Process PMIDs in chunks of 200
    chunk_size = 200
    for i in range(0, len(pmids), chunk_size):
        chunk_pmids = pmids[i:i+chunk_size]
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(chunk_pmids),
            "retmode": "xml",
            "api_key": "8b5ab4797f030e74eb1a9cc6456e0381a008"
        }
        response = requests.get(fetch_url, params=fetch_params)
        if response.status_code != 200:
            print(f"HTTP Error for chunk {i//chunk_size + 1}: {response.status_code}")
            print("Response:", response.text)
            continue

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            print(f"XML Parsing Error for chunk {i//chunk_size + 1}: {e}")
            continue

        for article, pmid in zip(root.findall(".//PubmedArticle"), chunk_pmids):
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
                if firstname or lastname:
                    authors.append(f"{firstname} {lastname}".strip())

            # Journal
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "N/A"

            # Publication Year
            pub_year_elem = article.find(".//PubDate/Year")
            pub_year = pub_year_elem.text if pub_year_elem is not None else "N/A"

            # Keywords
            keywords = [kw.text for kw in article.findall(".//Keyword")]
            # Filter out None values
            keywords_str = "; ".join([kw for kw in keywords if kw is not None]) if keywords else "N/A"


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