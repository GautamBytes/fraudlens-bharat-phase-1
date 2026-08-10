import { fraudlensRequest } from "@/lib/server/fraudlens";

export async function GET(): Promise<Response> {
  return fraudlensRequest("/cases?limit=100", { method: "GET" });
}

export async function DELETE(): Promise<Response> {
  return fraudlensRequest("/cases?confirm=true", { method: "DELETE" });
}
