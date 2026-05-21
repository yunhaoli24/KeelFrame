import { beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { useCreateMenuMutation, useGetSidebarMenuQuery } from "./menus.api";

const get = vi.fn();
const post = vi.fn();
const invalidateQueries = vi.fn();

vi.mock("@/composables/use-axios", () => ({
  useAxios: () => ({
    axiosInstance: {
      get,
      post,
    },
  }),
}));

vi.mock("@tanstack/vue-query", () => ({
  useQuery: <TOptions>(options: TOptions) => options,
  useMutation: <TOptions>(options: TOptions) => options,
  useQueryClient: () => ({
    invalidateQueries,
  }),
}));

describe("menu API hooks", () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
    invalidateQueries.mockReset();
  });

  it("fetches sidebar menus and respects the enabled flag", async () => {
    const response = { code: 200, msg: "success", data: [] };
    get.mockResolvedValue({ data: response });

    const query = useGetSidebarMenuQuery(false);

    expect(query.queryKey).toEqual(["menu-sidebar"]);
    expect(query.enabled.value).toBe(false);
    await expect(query.queryFn()).resolves.toBe(response);
    expect(get).toHaveBeenCalledWith("/sys/menus/sidebar");
  });

  it("creates menus and invalidates menu caches on success", async () => {
    const response = { code: 200, msg: "success", data: null };
    const payload = {
      title: "Dashboard",
      name: "dashboard",
      sort: 1,
      type: 1,
      status: 1,
      display: 1,
      cache: 0,
    };
    post.mockResolvedValue({ data: response });

    const mutation = useCreateMenuMutation();

    await expect(mutation.mutationFn(payload)).resolves.toBe(response);
    mutation.onSuccess();

    expect(post).toHaveBeenCalledWith("/sys/menus", payload);
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["menu-tree"] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["menu-sidebar"] });
  });
});
