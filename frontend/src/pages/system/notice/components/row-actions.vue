<script setup lang="ts">
import { Ellipsis, FilePenLine, Trash2 } from "lucide-vue-next";

import type { Notice } from "@/services/api/system/notice/notices.api";

const props = defineProps<{
  notice: Notice;
}>();

const emits = defineEmits<{
  (e: "edit", notice: Notice): void;
  (e: "delete", notice: Notice): void;
}>();

function handleEdit() {
  emits("edit", props.notice);
}

function handleDelete() {
  emits("delete", props.notice);
}
</script>

<template>
  <UiDropdownMenu>
    <UiDropdownMenuTrigger as-child>
      <UiButton variant="ghost" class="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
        <Ellipsis class="size-4" />
        <span class="sr-only">Open menu</span>
      </UiButton>
    </UiDropdownMenuTrigger>
    <UiDropdownMenuContent align="end" class="w-[160px]">
      <UiDropdownMenuItem @click.stop="handleEdit">
        <span>Edit</span>
        <UiDropdownMenuShortcut>
          <FilePenLine class="size-4" />
        </UiDropdownMenuShortcut>
      </UiDropdownMenuItem>
      <UiDropdownMenuItem @click.stop="handleDelete">
        <span>Delete</span>
        <UiDropdownMenuShortcut>
          <Trash2 class="size-4" />
        </UiDropdownMenuShortcut>
      </UiDropdownMenuItem>
    </UiDropdownMenuContent>
  </UiDropdownMenu>
</template>
