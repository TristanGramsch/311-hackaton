const response = await fetch("https://311.boston.gov/open311/v2/services.json");
if (!response.ok) {
  return { error: true, message: "Unable to reach Boston 311 services." };
}
const services = await response.json();
const grouped: Record<string, Array<{name: string, code: string}>> = {};
for (const svc of services) {
  const group = svc.group || "Other";
  if (!grouped[group]) grouped[group] = [];
  grouped[group].push({ name: svc.service_name, code: svc.service_code });
}
const lines: string[] = [];
for (const [group, items] of Object.entries(grouped)) {
  lines.push(`${group}: ${items.map(i => i.name).join(", ")}`);
}
return { services: lines.join("\n"), count: services.length };
