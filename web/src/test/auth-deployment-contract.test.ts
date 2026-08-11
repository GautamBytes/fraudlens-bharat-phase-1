import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const WEB = resolve(import.meta.dirname, "../..");
const ROOT = resolve(WEB, "..");
const read = (path: string) => readFileSync(resolve(ROOT, path), "utf8");

describe("Better Auth deployment contract", () => {
  it("pins stable auth dependencies and exposes repeatable migration and provisioning commands", () => {
    const packageJson = JSON.parse(read("web/package.json"));

    expect(packageJson.dependencies["better-auth"]).toBe("1.6.26");
    expect(packageJson.dependencies.pg).toBe("8.16.3");
    expect(packageJson.scripts["auth:migrate"]).toContain("@better-auth/cli@1.4.21 migrate");
    expect(packageJson.scripts["auth:create-professor"]).toContain("scripts/create-professor.ts");
  });

  it("documents durable secrets and gives Docker a health-checked PostgreSQL service", () => {
    const webEnv = read("web/.env.example");
    const compose = read("compose.yaml");
    const guide = read("docs/professor_testing_guide.md");

    for (const name of ["DATABASE_URL", "BETTER_AUTH_SECRET", "BETTER_AUTH_URL"]) {
      expect(webEnv).toContain(`${name}=`);
      expect(compose).toContain(name);
      expect(guide).toContain(name);
    }
    expect(compose).toContain("auth-db:");
    expect(compose).toContain("pg_isready");
    expect(compose).toContain("condition: service_healthy");
    expect(guide).toContain("npm run auth:migrate");
    expect(guide).toContain("npm run auth:create-professor");
    expect(guide).toContain("Public sign-up is disabled");
  });
});
