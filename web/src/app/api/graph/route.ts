import { fraudlensRequest } from "@/lib/server/fraudlens";

function boundedInteger(value: string | null, fallback: number, minimum: number, maximum: number): number {
  if (value === null || !/^\d+$/.test(value)) return fallback;
  const parsed = Number(value);
  return Math.min(maximum, Math.max(minimum, parsed));
}

export async function GET(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const minimumCaseCount = boundedInteger(url.searchParams.get("minimum_case_count"), 2, 2, 20);
  const caseLimit = boundedInteger(url.searchParams.get("case_limit"), 100, 1, 100);
  return fraudlensRequest(
    `/graph?minimum_case_count=${minimumCaseCount}&case_limit=${caseLimit}`,
    { method: "GET" },
  );
}
