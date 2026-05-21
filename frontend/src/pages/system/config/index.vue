<script setup lang="ts">
import { isAxiosError } from "axios";
import { Plus, RefreshCcw } from "lucide-vue-next";
import { toast } from "vue-sonner";

import type { ServerPagination } from "@/components/data-table/types";
import ConfirmDialog from "@/components/confirm-dialog.vue";
import { BasicPage } from "@/components/global-layout";
import { DEFAULT_PAGE_SIZE } from "@/constants/pagination";
import {
  useCreateSystemConfigMutation,
  useDeleteSystemConfigMutation,
  useGetSystemConfigsQuery,
  useUpdateSystemConfigMutation,
  type SystemConfig,
  type SystemConfigPayload,
} from "@/services/api/system/config/system-configs.api";

import ConfigForm from "./components/config-form.vue";
import { createColumns } from "./components/columns";
import ConfigDataTable from "./components/data-table.vue";

const page = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const filters = reactive({
  name: "",
  type: "",
});
const appliedFilters = reactive({
  name: "",
  type: "",
});

const queryParams = computed(() => ({
  page: page.value,
  size: pageSize.value,
  name: appliedFilters.name || undefined,
  type: appliedFilters.type || undefined,
}));

const query = useGetSystemConfigsQuery(queryParams);

const configs = computed(() => query.data.value?.data?.items ?? []);
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
const editingConfig = ref<SystemConfig | null>(null);

const deleteDialogOpen = ref(false);
const deleteTarget = ref<SystemConfig | null>(null);

const createMutation = useCreateSystemConfigMutation();
const updateMutation = useUpdateSystemConfigMutation();
const deleteMutation = useDeleteSystemConfigMutation();

const isSaving = computed(() => createMutation.isPending.value || updateMutation.isPending.value);
const isDeleting = computed(() => deleteMutation.isPending.value);

const columns = computed(() =>
  createColumns({
    onEdit: (config) => openEdit(config),
    onDelete: (config) => requestDelete(config),
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
  appliedFilters.type = filters.type.trim();
  page.value = 1;
}

function resetFilters() {
  filters.name = "";
  filters.type = "";
  applyFilters();
}

function refreshList() {
  void query.refetch();
}

function openCreate() {
  editingConfig.value = null;
  dialogOpen.value = true;
}

function openEdit(config: SystemConfig) {
  editingConfig.value = config;
  dialogOpen.value = true;
}

function requestDelete(config: SystemConfig) {
  deleteTarget.value = config;
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
    editingConfig.value = null;
  }
});

watch(deleteDialogOpen, (open) => {
  if (!open) {
    deleteTarget.value = null;
  }
});

async function handleSubmit(payload: SystemConfigPayload, close?: () => void) {
  try {
    if (editingConfig.value) {
      await updateMutation.mutateAsync({ id: editingConfig.value.id, payload });
      toast.success("Config updated");
    } else {
      await createMutation.mutateAsync(payload);
      toast.success("Config created");
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
    toast.success("Config deleted");
    deleteDialogOpen.value = false;
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
}
</script>

<template>
  <BasicPage title="System Configs" sticky>
    <template #actions>
      <UiButton variant="outline" :disabled="isFetching" @click="refreshList">
        <RefreshCcw class="mr-2 size-4" />
        Refresh
      </UiButton>
      <UiButton @click="openCreate">
        <Plus class="mr-2 size-4" />
        New Config
      </UiButton>
    </template>

    <div class="space-y-4">
      <UiCard>
        <UiCardContent class="py-4">
          <div class="grid gap-4 md:grid-cols-[1fr_1fr_auto] md:items-end">
            <div class="space-y-2">
              <UiLabel for="config-name">Name</UiLabel>
              <UiInput id="config-name" v-model="filters.name" placeholder="Search by name" />
            </div>
            <div class="space-y-2">
              <UiLabel for="config-type">Type</UiLabel>
              <UiInput id="config-type" v-model="filters.type" placeholder="Search by type" />
            </div>
            <div class="flex gap-2">
              <UiButton variant="secondary" @click="applyFilters"> Search </UiButton>
              <UiButton variant="ghost" @click="resetFilters"> Reset </UiButton>
            </div>
          </div>
        </UiCardContent>
      </UiCard>

      <UiAlert v-if="isError" variant="destructive">
        <UiAlertTitle>Failed to load configs</UiAlertTitle>
        <UiAlertDescription>
          {{ listErrorMessage }}
        </UiAlertDescription>
      </UiAlert>

      <div class="overflow-x-auto">
        <ConfigDataTable
          :data="configs"
          :columns="columns"
          :loading="isLoading"
          :server-pagination="serverPagination"
        />
      </div>
    </div>

    <UiDialog v-model:open="dialogOpen" v-slot="{ close }">
      <UiDialogContent class="max-h-[90vh] overflow-y-auto">
        <UiDialogHeader>
          <UiDialogTitle>
            {{ editingConfig ? "Edit Config" : "New Config" }}
          </UiDialogTitle>
          <UiDialogDescription>
            {{ editingConfig ? "Update system parameter values." : "Add a new system parameter." }}
          </UiDialogDescription>
        </UiDialogHeader>
        <ConfigForm
          class="mt-4"
          :config="editingConfig"
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
      <template #title> Delete config? </template>
      <template #description>
        This will permanently remove "{{ deleteTargetName }}". This action cannot be undone.
      </template>
    </ConfirmDialog>
  </BasicPage>
</template>
