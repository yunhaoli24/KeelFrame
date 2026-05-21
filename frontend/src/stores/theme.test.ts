import { beforeEach, describe, expect, it } from "vite-plus/test";
import { createPinia, setActivePinia } from "pinia";

import { useThemeStore } from "./theme";

describe("useThemeStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("uses the default visual preferences", () => {
    const themeStore = useThemeStore();

    expect(themeStore.theme).toBe("zinc");
    expect(themeStore.radius).toBe(0.5);
    expect(themeStore.contentLayout).toBe("centered");
  });

  it("updates theme, radius, and content layout", () => {
    const themeStore = useThemeStore();

    themeStore.setTheme("blue");
    themeStore.setRadius(1);
    themeStore.setContentLayout("full");

    expect(themeStore.theme).toBe("blue");
    expect(themeStore.radius).toBe(1);
    expect(themeStore.contentLayout).toBe("full");
  });
});
