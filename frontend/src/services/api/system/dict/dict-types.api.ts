import type { AxiosError } from "axios";

import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, toValue, type MaybeRefOrGetter } from "vue";

import { useAxios } from "@/composables/use-axios";

import type {
  BackendResponse,
  DictType,
  DictTypeListParams,
  DictTypePayload,
  DictTypeUpdatePayload,
  PageData,
} from "@/services/types";

export type { DictType, DictTypeListParams, DictTypePayload, DictTypeUpdatePayload };

const DICT_TYPE_QUERY_KEY = ["dict-types"];

function normalizeListParams(params: DictTypeListParams): DictTypeListParams {
  const normalized: DictTypeListParams = {
    page: params.page,
    size: params.size,
  };

  if (params.name?.trim()) {
    normalized.name = params.name.trim();
  }

  if (params.code?.trim()) {
    normalized.code = params.code.trim();
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

export function useGetDictTypesQuery(params: MaybeRefOrGetter<DictTypeListParams>) {
  const { axiosInstance } = useAxios();
  const resolvedParams = computed(() => normalizeListParams({ ...toValue(params) }));

  return useQuery<BackendResponse<PageData<DictType>>, AxiosError>({
    queryKey: computed(() => [...DICT_TYPE_QUERY_KEY, resolvedParams.value]),
    queryFn: async () => {
      const response = await axiosInstance.get<BackendResponse<PageData<DictType>>>(
        "/sys/dict-types",
        { params: resolvedParams.value },
      );
      return ensureSuccess(response.data);
    },
  });
}

export function useGetAllDictTypesQuery() {
  const { axiosInstance } = useAxios();

  return useQuery<BackendResponse<DictType[]>, AxiosError>({
    queryKey: ["all-dict-types"],
    queryFn: async () => {
      const response = await axiosInstance.get<BackendResponse<DictType[]>>("/sys/dict-types/all");
      return ensureSuccess(response.data);
    },
  });
}

export function useCreateDictTypeMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, DictTypePayload>({
    mutationKey: ["create-dict-type"],
    mutationFn: async (payload: DictTypePayload) => {
      const response = await axiosInstance.post<BackendResponse<null>>("/sys/dict-types", payload);
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_TYPE_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["all-dict-types"] });
    },
  });
}

export function useUpdateDictTypeMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, DictTypeUpdatePayload>({
    mutationKey: ["update-dict-type"],
    mutationFn: async ({ id, payload }: DictTypeUpdatePayload) => {
      const response = await axiosInstance.put<BackendResponse<null>>(
        `/sys/dict-types/${id}`,
        payload,
      );
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_TYPE_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["all-dict-types"] });
    },
  });
}

export function useDeleteDictTypeMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, number[]>({
    mutationKey: ["delete-dict-type"],
    mutationFn: async (ids: number[]) => {
      const response = await axiosInstance.delete<BackendResponse<null>>("/sys/dict-types", {
        data: { pks: ids },
      });
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_TYPE_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["all-dict-types"] });
    },
  });
}
