import { fraudlensRequest } from "@/lib/server/fraudlens";

export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  return fraudlensRequest("/ready", { method: "GET" }, 55_000);
}
