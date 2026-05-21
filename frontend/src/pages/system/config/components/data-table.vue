<script setup lang="ts">
import type { DataTableProps } from "@/components/data-table/types";

import DataTable from "@/components/data-table/data-table.vue";
import { generateVueTable } from "@/components/data-table/use-generate-vue-table";

import type { SystemConfig } from "@/services/api/system/config/system-configs.api";

const props = defineProps<DataTableProps<SystemConfig>>();
const table = generateVueTable<SystemConfig>(props);
</script>

<template>
  <DataTable :columns :table :data :loading :server-pagination="serverPagination">
    <template #toolbar>
      <slot name="toolbar" :table="table" />
    </template>
  </DataTable>
</template>
