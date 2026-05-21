<script setup lang="ts">
import { isAxiosError } from "axios";
import { Plus, RefreshCcw } from "lucide-vue-next";
import { toast } from "vue-sonner";

import type { ServerPagination } from "@/components/data-table/types";
import ConfirmDialog from "@/components/confirm-dialog.vue";
import { BasicPage } from "@/components/global-layout";
import { DEFAULT_PAGE_SIZE } from "@/constants/pagination";
import {
  useCreateNoticeMutation,
  useDeleteNoticeMutation,
  useGetNoticesQuery,
  useUpdateNoticeMutation,
  type Notice,
  type NoticePayload,
} from "@/services/api/system/notice/notices.api";

import NoticeForm from "./components/notice-form.vue";
import { createColumns } from "./components/columns";
import NoticeDataTable from "./components/data-table.vue";

const page = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const filters = reactive({
  title: "",
  type: undefined as number | undefined,
  status: undefined as number | undefined,
});
const appliedFilters = reactive({
  title: "",
  type: undefined as number | undefined,
  status: undefined as number | undefined,
});

const queryParams = computed(() => ({
  page: page.value,
  size: pageSize.value,
  title: appliedFilters.title || undefined,
  type: appliedFilters.type,
  status: appliedFilters.status,
}));

const query = useGetNoticesQuery(queryParams);

const notices = computed(() => query.data.value?.data?.items ?? []);
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
const editingNotice = ref<Notice | null>(null);

const deleteDialogOpen = ref(false);
const deleteTarget = ref<Notice | null>(null);

const createMutation = useCreateNoticeMutation();
const updateMutation = useUpdateNoticeMutation();
const deleteMutation = useDeleteNoticeMutation();

const isSaving = computed(() => createMutation.isPending.value || updateMutation.isPending.value);
const isDeleting = computed(() => deleteMutation.isPending.value);

const columns = computed(() =>
  createColumns({
    onEdit: (notice) => openEdit(notice),
    onDelete: (notice) => requestDelete(notice),
  }),
);

const deleteTargetTitle = computed(() => deleteTarget.value?.title ?? "");

const listErrorMessage = computed(() => {
  if (!query.error.value) {
    return "";
  }
  return getErrorMessage(query.error.value);
});

function applyFilters() {
  appliedFilters.title = filters.title.trim();
  appliedFilters.type = filters.type;
  appliedFilters.status = filters.status;
  page.value = 1;
}

function resetFilters() {
  filters.title = "";
  filters.type = undefined;
  filters.status = undefined;
  applyFilters();
}

function refreshList() {
  void query.refetch();
}

function openCreate() {
  editingNotice.value = null;
  dialogOpen.value = true;
}

function openEdit(notice: Notice) {
  editingNotice.value = notice;
  dialogOpen.value = true;
}

function requestDelete(notice: Notice) {
  deleteTarget.value = notice;
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
    editingNotice.value = null;
  }
});

watch(deleteDialogOpen, (open) => {
  if (!open) {
    deleteTarget.value = null;
  }
});

async function handleSubmit(payload: NoticePayload, close?: () => void) {
  try {
    if (editingNotice.value) {
      await updateMutation.mutateAsync({ id: editingNotice.value.id, payload });
      toast.success("Notice updated");
    } else {
      await createMutation.mutateAsync(payload);
      toast.success("Notice created");
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
    toast.success("Notice deleted");
    deleteDialogOpen.value = false;
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
}
</script>

<template>
  <BasicPage title="Notices" sticky>
    <template #actions>
      <UiButton variant="outline" :disabled="isFetching" @click="refreshList">
        <RefreshCcw class="mr-2 size-4" />
        Refresh
      </UiButton>
      <UiButton @click="openCreate">
        <Plus class="mr-2 size-4" />
        New Notice
      </UiButton>
    </template>

    <div class="space-y-4">
      <UiCard>
        <UiCardContent class="py-4">
          <div class="grid gap-4 md:grid-cols-[1fr_auto_auto_auto] md:items-end">
            <div class="space-y-2">
              <UiLabel for="notice-title">Title</UiLabel>
              <UiInput id="notice-title" v-model="filters.title" placeholder="Search by title" />
            </div>
            <div class="space-y-2">
              <UiLabel for="notice-type">Type</UiLabel>
              <UiSelect v-model="filters.type" placeholder="All types">
                <UiSelectTrigger>
                  <UiSelectValue placeholder="All types" />
                </UiSelectTrigger>
                <UiSelectContent>
                  <UiSelectItem :value="0">通知</UiSelectItem>
                  <UiSelectItem :value="1">公告</UiSelectItem>
                </UiSelectContent>
              </UiSelect>
            </div>
            <div class="space-y-2">
              <UiLabel for="notice-status">Status</UiLabel>
              <UiSelect v-model="filters.status" placeholder="All status">
                <UiSelectTrigger>
                  <UiSelectValue placeholder="All status" />
                </UiSelectTrigger>
                <UiSelectContent>
                  <UiSelectItem :value="1">显示</UiSelectItem>
                  <UiSelectItem :value="0">隐藏</UiSelectItem>
                </UiSelectContent>
              </UiSelect>
            </div>
            <div class="flex gap-2">
              <UiButton variant="secondary" @click="applyFilters"> Search </UiButton>
              <UiButton variant="ghost" @click="resetFilters"> Reset </UiButton>
            </div>
          </div>
        </UiCardContent>
      </UiCard>

      <UiAlert v-if="isError" variant="destructive">
        <UiAlertTitle>Failed to load notices</UiAlertTitle>
        <UiAlertDescription>
          {{ listErrorMessage }}
        </UiAlertDescription>
      </UiAlert>

      <div class="overflow-x-auto">
        <NoticeDataTable
          :data="notices"
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
            {{ editingNotice ? "Edit Notice" : "New Notice" }}
          </UiDialogTitle>
          <UiDialogDescription>
            {{
              editingNotice ? "Update notice information." : "Create a new notice or announcement."
            }}
          </UiDialogDescription>
        </UiDialogHeader>
        <NoticeForm
          class="mt-4"
          :notice="editingNotice"
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
      <template #title> Delete notice? </template>
      <template #description>
        This will permanently remove "{{ deleteTargetTitle }}". This action cannot be undone.
      </template>
    </ConfirmDialog>
  </BasicPage>
</template>
