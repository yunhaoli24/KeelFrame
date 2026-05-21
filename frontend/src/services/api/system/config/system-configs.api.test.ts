import { beforeEach, describe, expect, it, vi } from "vite-plus/test";
import { ref } from "vue";

import { useGetSystemConfigsQuery } from "./system-configs.api";

const get = vi.fn();

vi.mock("@/composables/use-axios", () => ({
  useAxios: () => ({
    axiosInstance: {
      get,
    },
  }),
}));

vi.mock("@tanstack/vue-query", () => ({
  useQuery: <TOptions>(options: TOptions) => options,
  useMutation: <TOptions>(options: TOptions) => options,
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

describe("useGetSystemConfigsQuery", () => {
  beforeEach(() => {
    get.mockReset();
  });

  it("normalizes list params before querying system configs", async () => {
    const params = ref({
      page: 1,
      size: 20,
      name: "  site title  ",
      type: "   ",
    });
    const response = {
      code: 200,
      msg: "success",
      data: { items: [], total: 0, page: 1, size: 20, total_pages: 0, links: {} },
    };
    get.mockResolvedValue({ data: response });

    const query = useGetSystemConfigsQuery(params);

    expect(query.queryKey.value).toEqual([
      "system-configs",
      { page: 1, size: 20, name: "site title" },
    ]);
    await expect(query.queryFn()).resolves.toBe(response);
    expect(get).toHaveBeenCalledWith("/sys/configs", {
      params: { page: 1, size: 20, name: "site title" },
    });
  });

  it("rejects non-success backend responses", async () => {
    get.mockResolvedValue({ data: { code: 400, msg: "invalid params", data: null } });

    const query = useGetSystemConfigsQuery({ page: 1, size: 20 });

    await expect(query.queryFn()).rejects.toThrow("invalid params");
  });
});
