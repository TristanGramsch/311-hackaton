# MCP Data Query Guide — Boston Open Data

## Overview
The agent has access to an MCP server that provides tools for querying the Boston Open Data portal (data.boston.gov). This guide documents available tools, key datasets, and query workflows.

## MCP Endpoint
`https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws/mcp`

## Available Tools

### 1. search_datasets(query, limit=10)
Search for datasets by keyword. Use when a citizen asks about specific data topics.

### 2. list_all_datasets(limit=20)
Browse all available datasets without filtering.

### 3. get_dataset_info(dataset_id)
Get metadata and list of resources (files/tables) for a dataset. Returns resource IDs needed for querying.

### 4. get_datastore_schema(resource_id)
Get field names and data types for a queryable resource. **Must call this before query_datastore** to get exact field names.

### 5. query_datastore(resource_id, limit, offset, search_text, filters, sort, fields, date_range)
Fetch actual data records. Supports:
- **Exact match filters**: `{"case_status": "Open"}`
- **Full-text search**: `search_text="pothole"`
- **Sorting**: `sort="open_date desc"`
- **Field selection**: `fields=["case_id", "case_status"]`
- **Date ranges**: `date_range={"field": "open_date", "start_date": "2026-01-01", "end_date": "2026-03-31"}`

**Note**: Only exact-match filters are supported. For date ranges, use the `date_range` parameter which does client-side filtering.

## Standard Query Workflow
1. `search_datasets("311")` → find dataset ID
2. `get_dataset_info("311-service-requests")` → find resource IDs
3. `get_datastore_schema(resource_id)` → get exact field names
4. `query_datastore(resource_id, ...)` → fetch records

## Key Resource IDs

### 311 Service Requests
| Resource | ID | Schema Type |
|---|---|---|
| NEW SYSTEM (Oct 2025+) | `254adca6-64ab-4c5c-9fc0-a6da622be185` | New |
| 2026 | `1a0b420d-99f1-4887-9851-990b2a5a6e17` | Legacy |
| 2025 | `9d7c2214-4709-478a-a2e8-fb2020a5bb94` | Legacy |
| 2024 | `dff4d804-5031-443a-8409-8344efd0e5c8` | Legacy |
| 2023 | `e6013a93-1321-4f2a-bf91-8d8a02f1e62f` | Legacy |

### Schema: New System
Fields: case_id, open_date, case_topic, service_name, assigned_department, assigned_team, case_status, closure_reason, closure_comments, close_date, target_close_date, on_time, report_source, full_address, street_number, street_name, zip_code, neighborhood, public_works_district, city_council_district, fire_district, police_district, ward, precinct, submitted_photo, closed_photo, longitude, latitude

### Schema: Legacy System
Fields: case_enquiry_id, open_dt, sla_target_dt, closed_dt, on_time, case_status, closure_reason, case_title, subject, reason, type, queue, department, submitted_photo, closed_photo, location, fire_district, pwd_district, city_council_district, police_district, neighborhood, neighborhood_services_district, ward, precinct, location_street_name, location_zipcode, latitude, longitude, source

## Other Useful Datasets
- `trash-collection-days` — PWD trash collection days
- `trash-schedules-by-address` — Trash and recycling schedule by address
- `approved-building-permits` — Building permits
- `building-and-property-violations1` — Building/property violations
- `public-works-violations` — PWD code enforcement citations
- `crime-incident-reports-august-2015-to-date-source-new-system` — BPD crime data
- `parking-meters` — Parking meter locations
- `streetlight-locations` — Streetlight inventory
- `active-food-establishment-licenses` — Food establishment licenses
- `bprd-trees` — City trees
- `park-features` — Park features/amenities
- `blue-bikes-system-data` — BlueBikes rideshare data
- `blue-bike-stations` — BlueBikes station locations
