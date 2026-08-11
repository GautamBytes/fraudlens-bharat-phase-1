import { fraudlensRequest } from "@/lib/server/fraudlens";

export async function DELETE(): Promise<Response> {
  return fraudlensRequest("/cases?confirm=true", { method: "DELETE" });
}
