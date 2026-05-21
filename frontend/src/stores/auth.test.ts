import { beforeEach, describe, expect, it } from "vite-plus/test";
import { createPinia, setActivePinia } from "pinia";

import { useAuthStore } from "./auth";

describe("useAuthStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("stores login state and user session data", () => {
    const authStore = useAuthStore();
    const user = { id: 1, username: "admin" };

    authStore.setAuthInfo("token-1", "session-1", user);

    expect(authStore.isLogin).toBe(true);
    expect(authStore.accessToken).toBe("token-1");
    expect(authStore.sessionUuid).toBe("session-1");
    expect(authStore.userInfo).toEqual(user);
  });

  it("clears all auth state", () => {
    const authStore = useAuthStore();
    authStore.setAuthInfo("token-1", "session-1", { id: 1 });

    authStore.clearAuthInfo();

    expect(authStore.isLogin).toBe(false);
    expect(authStore.accessToken).toBe("");
    expect(authStore.sessionUuid).toBe("");
    expect(authStore.userInfo).toBeNull();
  });
});
