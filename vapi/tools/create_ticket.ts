const { service_code, address, description, first_name, last_name, email, phone } = args;
const { OPEN311_API_KEY } = env;

if (OPEN311_API_KEY) {
  // Real submission
  const params = new URLSearchParams();
  params.append("api_key", OPEN311_API_KEY);
  params.append("service_code", service_code);
  params.append("address_string", address);
  params.append("description", description);
  if (first_name) params.append("first_name", first_name);
  if (last_name) params.append("last_name", last_name);
  if (email) params.append("email", email);
  if (phone) params.append("phone", phone);

  const response = await fetch("https://311.boston.gov/open311/v2/requests.json", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded; charset=utf-8" },
    body: params.toString(),
  });
  if (!response.ok) {
    return { error: true, message: "Failed to submit the service request. Please try again or call 311 directly." };
  }
  const data = await response.json();
  const req = data[0] || {};
  return {
    success: true,
    service_request_id: req.service_request_id || null,
    token: req.token || null,
    service_notice: req.service_notice || "Your request has been submitted.",
  };
} else {
  // Simulated submission
  const mockToken = "BCS-MOCK-" + Math.floor(100000 + Math.random() * 900000);
  return {
    success: true,
    simulated: true,
    token: mockToken,
    service_notice: `Your request for "${service_code}" at "${address}" has been submitted. Reference: ${mockToken}. Note: this is a simulated submission for demo purposes.`,
  };
}
