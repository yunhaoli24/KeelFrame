import type { AxiosError } from "axios";

import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, toValue, type MaybeRefOrGetter } from "vue";

import { useAxios } from "@/composables/use-axios";

import type {
  BackendResponse,
  PageData,
  SystemConfig,
  SystemConfigListParams,
  SystemConfigPayload,
  SystemConfigUpdatePayload,
} from "@/services/types";

export type {
  SystemConfig,
  SystemConfigListParams,
  SystemConfigPayload,
  SystemConfigUpdatePayload,
};

const SYSTEM_CONFIG_QUERY_KEY = ["system-configs"];

function normalizeListParams(params: SystemConfigListParams): SystemConfigListParams {
  const normalized: SystemConfigListParams = {
    page: params.page,
    size: params.size,
  };

  if (params.name?.trim()) {
    normalized.name = params.name.trim();
  }

  if (params.type?.trim()) {
    normalized.type = params.type.trim();
  }

  return normalized;
}

function ensureSuccess<T>(response: BackendResponse<T>): BackendResponse<T> {
  const code = Number(response.code);
  if (!Number.isFinite(code) || code !== 200) {
    throw new Error(response.msg || "Request failed");
  }
  return response;
}

export function useGetSystemConfigsQuery(params: MaybeRefOrGetter<SystemConfigListParams>) {
  const { axiosInstance } = useAxios();
  const resolvedParams = computed(() => normalizeListParams({ ...toValue(params) }));

  return useQuery<BackendResponse<PageData<SystemConfig>>, AxiosError>({
    queryKey: computed(() => [...SYSTEM_CONFIG_QUERY_KEY, resolvedParams.value]),
    queryFn: async () => {
      const { type, ...params } = resolvedParams.value;
      const response = await axiosInstance.get<BackendResponse<PageData<SystemConfig>>>(
        "/sys/configs",
        {
          params: {
            ...params,
            config_type: type,
          },
        },
      );
      return ensureSuccess(response.data);
    },
  });
}

export function useCreateSystemConfigMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, SystemConfigPayload>({
    mutationKey: ["create-system-config"],
    mutationFn: async (payload: SystemConfigPayload) => {
      const response = await axiosInstance.post<BackendResponse<null>>("/sys/configs", payload);
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEY });
    },
  });
}

export function useUpdateSystemConfigMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, SystemConfigUpdatePayload>({
    mutationKey: ["update-system-config"],
    mutationFn: async ({ id, payload }: SystemConfigUpdatePayload) => {
      const response = await axiosInstance.put<BackendResponse<null>>(
        `/sys/configs/${id}`,
        payload,
      );
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEY });
    },
  });
}

export function useDeleteSystemConfigMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, number[]>({
    mutationKey: ["delete-system-config"],
    mutationFn: async (ids: number[]) => {
      const response = await axiosInstance.delete<BackendResponse<null>>("/sys/configs", {
        data: ids,
      });
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEY });
    },
  });
}
