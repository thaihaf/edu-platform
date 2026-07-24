import http from "k6/http";
import { check, sleep } from "k6";

export const options = { vus: 5, duration: "30s", thresholds: { http_req_failed: ["rate<0.01"] } };

export default function () {
  const response = http.get(`${__ENV.BASE_URL || "http://localhost:8000"}/health/live`);
  check(response, { "live endpoint is healthy": (value) => value.status === 200 });
  sleep(1);
}
