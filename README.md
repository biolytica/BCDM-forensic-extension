# Barcode Core Data Model(BCDM)
<br>
This repository hosts the reference implementation of the Barcode Core Data Model, a standardized format aimed at significantly enhancing the organization, sharing, and utilization of DNA barcode data within the biodiversity science community. The model defines key terms and their definitions for describing crucial details about DNA barcodes, including sequences, specimens, taxonomic names, locations, dates, and related metadata. Furthermore, the repository includes mappings to other data standards commonly used in the biodiversity community. It serves as a basis for developing analytical tools, databases, and resources leveraging DNA barcode data, thus enabling new avenues for research and education.
<br>
The BCDM is based on the [Frictionless Data Framework](https://frictionlessdata.io), a FAIR compliant data packaging solution and lowers barriers to data uptake.


## Core Features
- Alignment with existing biodiversity data models and databases, including the Barcode of Life Data System (BOLD) and Darwin Core Data, streamlining data exchange.

- Comprehensive coverage of essential data elements related to DNA based species identification, including specimen collection, DNA sequences, and taxonomic classification.

- Establishment of a common vocabulary for data interpretation

- Serve as a foundation for the development of analytical tools, databases, and resources that utilize DNA barcode data, opening new avenues for research and education.


## Field Definitions 
The [definitions](field_definitions.tsv) format for the current supported fields included in the Barcode Core Data Model (BCDM) with data types and data formats specified.

  
  |**Column name** | **Definition**|
  | :----------|:---------|
  |field| Standardized/universal name for the data field.|
  |data_type|  Data type of the field. For example: integer, float,string, and string:date|
  |data_format| Additional formatting constraint for the data value. For example: a timestamp field may follow this format `%d-%b-%y`; default indicates no extra formatting constraint specified. | 
  |definition | Meaning of the term, including their controlled vocabulary when applicable. |
  | |
<br>
<br>


## Mappings To Other Data Models & Databases
 1. **mapping_BCDM_to_BOLD.tsv**: This document provides mapping of the BCDM data fields to the BOLD Relational Database. 

<br>

  |**Column name** | **Definition**|
  | :----------|:---------|
  |bcdm_field| Standardized/universal name for the data field.|
  |bold_db | The relational database to which the data of the universal field are residing, in the format: `server`:`database_name`.  Example: db1:newdb12 |
  |bold_db_table| The specific database table to which the universal field is mapped to.|
  |bold_db_field| The specific database field to which the universal field is mapped to.|
  |rules| Set of regex used for basic data validation.
  | |
<br>
<br>
 
 2. **mapping_BCDM_to_DWC.tsv**: This document provides the mapping of the BCDM to Darwin Core standard. Please notice that not all BCMD fields have an equivalent term in the Darwin Core standard and therefore they will not be part of the export. DarwinCore fields can be found in the following link: `[Darwin Reference Guide] (https://dwc.tdwg.org/terms/)`
 
<br>

  
  |**Column name** | **Definition**|
  | :----------|:---------|
  |bcdm_field | Standardized/universal name for the data field.|
  |dwc_field | Corresponding term in the Darwin Core glossary.|
  |bcdm_type|Data type of the field as in the BCDM. For example: integer, float,string, and string:date |
  |bcdm_format| Additional formatting constraint for the data value as in the BCDM. For example: a timestamp field may follow this format `%d-%b-%y`; default indicates no extra formatting constraint specified.  |
  |dwc_type|Data type of the field as in the Darwin Core standard.|
  |dwc_format| Additional formatting constraint for the data value as in the Darwin Core standard.|
  | |
