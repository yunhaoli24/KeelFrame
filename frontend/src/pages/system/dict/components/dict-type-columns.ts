import type { ColumnDef } from "@tanstack/vue-table";

import { h } from "vue";

import DataTableColumnHeader from "@/components/data-table/column-header.vue";
import type { DictType } from "@/services/api/system/dict/dict-types.api";

import DictTypeRowActions from "./dict-type-row-actions.vue";

function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

export function createDictTypeColumns({
  onEdit,
  onDelete,
}: {
  onEdit: (dictType: DictType) => void;
  onDelete: (dictType: DictType) => void;
}): ColumnDef<DictType>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => h(DataTableColumnHeader<DictType>, { column, title: "Name" }),
      cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("name")),
    },
    {
      accessorKey: "code",
      header: ({ column }) => h(DataTableColumnHeader<DictType>, { column, title: "Code" }),
      cell: ({ row }) => h("div", { class: "font-mono text-sm" }, row.getValue("code")),
    },
    {
      accessorKey: "remark",
      header: ({ column }) => h(DataTableColumnHeader<DictType>, { column, title: "Remark" }),
      cell: ({ row }) => {
        const remark = row.original.remark;
        return remark
          ? h("div", { class: "max-w-[220px] truncate text-muted-foreground" }, remark)
          : h("span", { class: "text-muted-foreground" }, "-");
      },
    },
    {
      accessorKey: "updated_time",
      header: ({ column }) => h(DataTableColumnHeader<DictType>, { column, title: "Updated" }),
      cell: ({ row }) =>
        h(
          "div",
          { class: "whitespace-nowrap text-muted-foreground" },
          formatDate(row.original.updated_time ?? row.original.created_time),
        ),
    },
    {
      id: "actions",
      cell: ({ row }) =>
        h(DictTypeRowActions, {
          dictType: row.original,
          onEdit,
          onDelete,
        }),
    },
  ];
}
