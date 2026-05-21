<script setup lang="ts">
import { isAxiosError } from "axios";
import { Plus, RefreshCcw } from "lucide-vue-next";
import { toast } from "vue-sonner";

import type { ServerPagination } from "@/components/data-table/types";
import ConfirmDialog from "@/components/confirm-dialog.vue";
import { BasicPage } from "@/components/global-layout";
import { DEFAULT_PAGE_SIZE } from "@/constants/pagination";
import {
  useCreateDictTypeMutation,
  useDeleteDictTypeMutation,
  useGetDictTypesQuery,
  useUpdateDictTypeMutation,
  type DictType,
  type DictTypePayload,
} from "@/services/api/system/dict/dict-types.api";

import DictTypeForm from "./components/dict-type-form.vue";
import { createDictTypeColumns } from "./components/dict-type-columns";
import DictTypeDataTable from "./components/dict-type-data-table.vue";

const activeTab = ref<"types" | "data">("types");

const page = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const filters = reactive({
  name: "",
  code: "",
});
const appliedFilters = reactive({
  name: "",
  code: "",
});

const queryParams = computed(() => ({
  page: page.value,
  size: pageSize.value,
  name: appliedFilters.name || undefined,
  code: appliedFilters.code || undefined,
}));

const query = useGetDictTypesQuery(queryParams);

const dictTypes = computed(() => query.data.value?.data?.items ?? []);
const total = computed(() => query.data.value?.data?.total ?? 0);
const isLoading = computed(() => query.isLoading.value);
const isFetching = computed(() => query.isFetching.value);
const isError = computed(() => query.isError.value);

const serverPagination = computed<ServerPagination>(() => ({
  page: page.value,
  pageSize: pageSize.value,
  total: total.value,
  onPageChange: (nextPage) => {
    page.value = nextPage;
  },
  onPageSizeChange: (nextSize) => {
    pageSize.value = nextSize;
    page.value = 1;
  },
}));

const dialogOpen = ref(false);
const editingDictType = ref<DictType | null>(null);

const deleteDialogOpen = ref(false);
const deleteTarget = ref<DictType | null>(null);

const createMutation = useCreateDictTypeMutation();
const updateMutation = useUpdateDictTypeMutation();
const deleteMutation = useDeleteDictTypeMutation();

const isSaving = computed(() => createMutation.isPending.value || updateMutation.isPending.value);
const isDeleting = computed(() => deleteMutation.isPending.value);

const columns = computed(() =>
  createDictTypeColumns({
    onEdit: (dictType) => openEdit(dictType),
    onDelete: (dictType) => requestDelete(dictType),
  }),
);

const deleteTargetName = computed(() => deleteTarget.value?.name ?? "");

const listErrorMessage = computed(() => {
  if (!query.error.value) {
    return "";
  }
  return getErrorMessage(query.error.value);
});

function applyFilters() {
  appliedFilters.name = filters.name.trim();
  appliedFilters.code = filters.code.trim();
  page.value = 1;
}

function resetFilters() {
  filters.name = "";
  filters.code = "";
  applyFilters();
}

function refreshList() {
  void query.refetch();
}

function openCreate() {
  editingDictType.value = null;
  dialogOpen.value = true;
}

function openEdit(dictType: DictType) {
  editingDictType.value = dictType;
  dialogOpen.value = true;
}

function requestDelete(dictType: DictType) {
  deleteTarget.value = dictType;
  deleteDialogOpen.value = true;
}

function getErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    return error.response?.data?.msg || error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

watch(dialogOpen, (open) => {
  if (!open) {
    editingDictType.value = null;
  }
});

watch(deleteDialogOpen, (open) => {
  if (!open) {
    deleteTarget.value = null;
  }
});

watch(activeTab, (newTab) => {
  if (newTab === "data") {
    // TODO: Load dict data
  }
});

async function handleSubmit(payload: DictTypePayload, close?: () => void) {
  try {
    if (editingDictType.value) {
      await updateMutation.mutateAsync({ id: editingDictType.value.id, payload });
      toast.success("Dict type updated");
    } else {
      await createMutation.mutateAsync(payload);
      toast.success("Dict type created");
    }
    if (close) {
      close();
    } else {
      dialogOpen.value = false;
    }
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) {
    return;
  }

  try {
    await deleteMutation.mutateAsync([deleteTarget.value.id]);
    toast.success("Dict type deleted");
    deleteDialogOpen.value = false;
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
}
</script>

<template>
  <BasicPage title="Dictionary Management" sticky>
    <template #actions>
      <UiButton variant="outline" :disabled="isFetching" @click="refreshList">
        <RefreshCcw class="mr-2 size-4" />
        Refresh
      </UiButton>
      <UiButton @click="openCreate">
        <Plus class="mr-2 size-4" />
        New Dict Type
      </UiButton>
    </template>

    <div class="space-y-4">
      <UiTabs v-model="activeTab" class="w-full">
        <UiTabsList class="grid w-full grid-cols-2">
          <UiTabsTrigger value="types"> Dict Types </UiTabsTrigger>
          <UiTabsTrigger value="data"> Dict Data </UiTabsTrigger>
        </UiTabsList>

        <UiTabsContent value="types" class="space-y-4 mt-4">
          <UiCard>
            <UiCardContent class="py-4">
              <div class="grid gap-4 md:grid-cols-[1fr_1fr_auto] md:items-end">
                <div class="space-y-2">
                  <UiLabel for="dict-type-name">Name</UiLabel>
                  <UiInput
                    id="dict-type-name"
                    v-model="filters.name"
                    placeholder="Search by name"
                  />
                </div>
                <div class="space-y-2">
                  <UiLabel for="dict-type-code">Code</UiLabel>
                  <UiInput
                    id="dict-type-code"
                    v-model="filters.code"
                    placeholder="Search by code"
                  />
                </div>
                <div class="flex gap-2">
                  <UiButton variant="secondary" @click="applyFilters"> Search </UiButton>
                  <UiButton variant="ghost" @click="resetFilters"> Reset </UiButton>
                </div>
              </div>
            </UiCardContent>
          </UiCard>

          <UiAlert v-if="isError" variant="destructive">
            <UiAlertTitle>Failed to load dict types</UiAlertTitle>
            <UiAlertDescription>
              {{ listErrorMessage }}
            </UiAlertDescription>
          </UiAlert>

          <div class="overflow-x-auto">
            <DictTypeDataTable
              :data="dictTypes"
              :columns="columns"
              :loading="isLoading"
              :server-pagination="serverPagination"
            />
          </div>
        </UiTabsContent>

        <UiTabsContent value="data" class="space-y-4 mt-4">
          <UiCard>
            <UiCardContent class="py-8">
              <div class="flex flex-col items-center justify-center gap-2 text-center">
                <p class="text-lg font-medium">Dictionary Data Management</p>
                <p class="text-sm text-muted-foreground max-w-md">
                  Select a dictionary type to view and manage its data entries. This feature will be
                  available soon.
                </p>
              </div>
            </UiCardContent>
          </UiCard>
        </UiTabsContent>
      </UiTabs>
    </div>

    <UiDialog v-model:open="dialogOpen" v-slot="{ close }">
      <UiDialogContent class="max-h-[90vh] overflow-y-auto">
        <UiDialogHeader>
          <UiDialogTitle>
            {{ editingDictType ? "Edit Dict Type" : "New Dict Type" }}
          </UiDialogTitle>
          <UiDialogDescription>
            {{
              editingDictType
                ? "Update dictionary type information."
                : "Create a new dictionary type."
            }}
          </UiDialogDescription>
        </UiDialogHeader>
        <DictTypeForm
          class="mt-4"
          :dict-type="editingDictType"
          :loading="isSaving"
          @submit="(payload) => handleSubmit(payload, close)"
        />
      </UiDialogContent>
    </UiDialog>

    <ConfirmDialog
      v-model:open="deleteDialogOpen"
      confirm-button-text="Delete"
      destructive
      :disabled="!deleteTarget"
      :is-loading="isDeleting"
      @confirm="handleDeleteConfirm"
    >
      <template #title> Delete dict type? </template>
      <template #description>
        This will permanently remove "{{ deleteTargetName }}". This action cannot be undone.
      </template>
    </ConfirmDialog>
  </BasicPage>
</template>
