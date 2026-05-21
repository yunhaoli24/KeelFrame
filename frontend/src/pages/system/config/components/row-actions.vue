<script setup lang="ts">
import { Ellipsis, FilePenLine, Trash2 } from "lucide-vue-next";

import type { SystemConfig } from "@/services/api/system/config/system-configs.api";

const props = defineProps<{
  config: SystemConfig;
}>();

const emits = defineEmits<{
  (e: "edit", config: SystemConfig): void;
  (e: "delete", config: SystemConfig): void;
}>();

function handleEdit() {
  emits("edit", props.config);
}

function handleDelete() {
  emits("delete", props.config);
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
