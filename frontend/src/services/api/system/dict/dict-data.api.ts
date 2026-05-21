import type { AxiosError } from "axios";

import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, toValue, type MaybeRefOrGetter } from "vue";

import { useAxios } from "@/composables/use-axios";

import type {
  BackendResponse,
  DictData,
  DictDataListParams,
  DictDataPayload,
  DictDataStatus,
  DictDataUpdatePayload,
  PageData,
} from "@/services/types";

export type {
  DictData,
  DictDataListParams,
  DictDataPayload,
  DictDataStatus,
  DictDataUpdatePayload,
};

export { DictDataStatus };

const DICT_DATA_QUERY_KEY = ["dict-data"];

function normalizeListParams(params: DictDataListParams): DictDataListParams {
  const normalized: DictDataListParams = {
    page: params.page,
    size: params.size,
  };

  if (params.type_code?.trim()) {
    normalized.type_code = params.type_code.trim();
  }

  if (params.label?.trim()) {
    normalized.label = params.label.trim();
  }

  if (params.value?.trim()) {
    normalized.value = params.value.trim();
  }

  if (params.status !== undefined) {
    normalized.status = params.status;
  }

  if (params.type_id !== undefined) {
    normalized.type_id = params.type_id;
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

export function useGetDictDataQuery(params: MaybeRefOrGetter<DictDataListParams>) {
  const { axiosInstance } = useAxios();
  const resolvedParams = computed(() => normalizeListParams({ ...toValue(params) }));

  return useQuery<BackendResponse<PageData<DictData>>, AxiosError>({
    queryKey: computed(() => [...DICT_DATA_QUERY_KEY, resolvedParams.value]),
    queryFn: async () => {
      const response = await axiosInstance.get<BackendResponse<PageData<DictData>>>(
        "/sys/dict-datas",
        { params: resolvedParams.value },
      );
      return ensureSuccess(response.data);
    },
  });
}

export function useGetDictDataByTypeCode(typeCode: MaybeRefOrGetter<string | undefined>) {
  const { axiosInstance } = useAxios();
  const resolvedTypeCode = computed(() => toValue(typeCode));

  return useQuery<BackendResponse<DictData[]>, AxiosError>({
    queryKey: computed(() => ["dict-data-by-type", resolvedTypeCode.value]),
    queryFn: async () => {
      if (!resolvedTypeCode.value) {
        throw new Error("Type code is required");
      }
      const response = await axiosInstance.get<BackendResponse<DictData[]>>(
        `/sys/dict-datas/type-codes/${resolvedTypeCode.value}`,
      );
      return ensureSuccess(response.data);
    },
    enabled: computed(() => !!resolvedTypeCode.value),
  });
}

export function useCreateDictDataMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, DictDataPayload>({
    mutationKey: ["create-dict-data"],
    mutationFn: async (payload: DictDataPayload) => {
      const response = await axiosInstance.post<BackendResponse<null>>("/sys/dict-datas", payload);
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_DATA_QUERY_KEY });
    },
  });
}

export function useUpdateDictDataMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, DictDataUpdatePayload>({
    mutationKey: ["update-dict-data"],
    mutationFn: async ({ id, payload }: DictDataUpdatePayload) => {
      const response = await axiosInstance.put<BackendResponse<null>>(
        `/sys/dict-datas/${id}`,
        payload,
      );
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_DATA_QUERY_KEY });
    },
  });
}

export function useDeleteDictDataMutation() {
  const { axiosInstance } = useAxios();
  const queryClient = useQueryClient();

  return useMutation<BackendResponse<null>, AxiosError, number[]>({
    mutationKey: ["delete-dict-data"],
    mutationFn: async (ids: number[]) => {
      const response = await axiosInstance.delete<BackendResponse<null>>("/sys/dict-datas", {
        data: { pks: ids },
      });
      return ensureSuccess(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DICT_DATA_QUERY_KEY });
    },
  });
}
