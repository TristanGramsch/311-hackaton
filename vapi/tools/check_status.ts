const { service_request_id } = args;

const response = await fetch(
  `https://311.boston.gov/open311/v2/requests/${encodeURIComponent(service_request_id)}.json`
);
if (!response.ok) {
  return { error: true, message: `Could not find a request with ID ${service_request_id}. Please double-check the number.` };
}
const data = await response.json();
const req = data[0] || data;
return {
  service_request_id: req.service_request_id,
  status: req.status,
  service_name: req.service_name,
  description: req.description,
  address: req.address,
  requested_datetime: req.requested_datetime,
  updated_datetime: req.updated_datetime,
  status_notes: req.status_notes || null,
};
