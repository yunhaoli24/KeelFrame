import type { NavigationGuard, RouteLocationNormalized, Router } from "vue-router";

import { beforeEach, describe, expect, it } from "vite-plus/test";

import pinia from "@/plugins/pinia/setup";
import { useAuthStore } from "@/stores/auth";
import { authGuard } from "./auth-guard";

function createRoute(path: string, fullPath = path): RouteLocationNormalized {
  return { path, fullPath } as RouteLocationNormalized;
}

function createGuardRouter(): NavigationGuard {
  let guard: NavigationGuard | undefined;
  const router = {
    beforeEach(callback: NavigationGuard) {
      guard = callback as typeof guard;
      return () => undefined;
    },
  } as Pick<Router, "beforeEach">;

  authGuard(router as Router);

  if (!guard) {
    throw new Error("auth guard was not registered");
  }

  return guard;
}

describe("authGuard", () => {
  beforeEach(() => {
    useAuthStore(pinia).clearAuthInfo();
  });

  it("redirects anonymous users from protected routes to sign in", () => {
    const guard = createGuardRouter();

    const result = guard(createRoute("/dashboard", "/dashboard?tab=workbench"), createRoute("/"));

    expect(result).toEqual({
      name: "/auth/sign-in",
      query: { redirect: "/dashboard?tab=workbench" },
    });
  });

  it("allows public auth and error routes without login", () => {
    const guard = createGuardRouter();

    expect(guard(createRoute("/auth/sign-in"), createRoute("/"))).toBeUndefined();
    expect(guard(createRoute("/errors/404"), createRoute("/"))).toBeUndefined();
  });

  it("allows protected routes after login", () => {
    useAuthStore(pinia).setAuthInfo("token-1", "session-1", { id: 1 });
    const guard = createGuardRouter();

    const result = guard(createRoute("/dashboard"), createRoute("/"));

    expect(result).toBeUndefined();
  });
});
