import { describe, expect, it } from "vite-plus/test";
import { ref } from "vue";

import { cn, valueUpdater } from "./utils";

describe("cn", () => {
  it("merges conditional classes and resolves Tailwind conflicts", () => {
    const isHidden = "visible" === "hidden";

    expect(cn("px-2 text-sm", isHidden && "hidden", "px-4", ["font-medium"])).toBe(
      "text-sm px-4 font-medium",
    );
  });
});

describe("valueUpdater", () => {
  it("assigns plain values to refs", () => {
    const value = ref("pending");

    valueUpdater("done", value);

    expect(value.value).toBe("done");
  });

  it("applies updater functions to the current ref value", () => {
    const value = ref(2);

    valueUpdater((current: number) => current * 3, value);

    expect(value.value).toBe(6);
  });
});
