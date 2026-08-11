import { fraudlensRequest } from "@/lib/server/fraudlens";
import { requireProfessorSession } from "@/lib/server/authorization";

export async function DELETE(request: Request): Promise<Response> {
  const unauthorized = await requireProfessorSession(request);
  if (unauthorized) return unauthorized;
  return fraudlensRequest("/cases?confirm=true", { method: "DELETE" });
}
