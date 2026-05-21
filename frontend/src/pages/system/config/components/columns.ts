import type { ColumnDef } from "@tanstack/vue-table";

import { h } from "vue";

import DataTableColumnHeader from "@/components/data-table/column-header.vue";
import { Badge } from "@/components/ui/badge";
import type { SystemConfig } from "@/services/api/system/config/system-configs.api";

import RowActions from "./row-actions.vue";

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

export function createColumns({
  onEdit,
  onDelete,
}: {
  onEdit: (config: SystemConfig) => void;
  onDelete: (config: SystemConfig) => void;
}): ColumnDef<SystemConfig>[] {
  return [
    {
      accessorKey: "name",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Name" }),
      cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("name")),
    },
    {
      accessorKey: "key",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Key" }),
      cell: ({ row }) => h("div", { class: "font-mono text-sm" }, row.getValue("key")),
    },
    {
      accessorKey: "value",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Value" }),
      cell: ({ row }) =>
        h("div", { class: "max-w-[260px] truncate text-muted-foreground" }, row.getValue("value")),
    },
    {
      accessorKey: "type",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Type" }),
      cell: ({ row }) => {
        const value = row.getValue("type") as string | null;
        return value
          ? h(Badge, { variant: "secondary" }, () => value)
          : h("span", { class: "text-muted-foreground" }, "-");
      },
    },
    {
      accessorKey: "is_frontend",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Frontend" }),
      cell: ({ row }) => {
        const isFrontend = row.original.is_frontend;
        return h(Badge, { variant: isFrontend ? "default" : "outline" }, () =>
          isFrontend ? "Yes" : "No",
        );
      },
    },
    {
      accessorKey: "remark",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Remark" }),
      cell: ({ row }) => {
        const remark = row.original.remark;
        return remark
          ? h("div", { class: "max-w-[220px] truncate text-muted-foreground" }, remark)
          : h("span", { class: "text-muted-foreground" }, "-");
      },
    },
    {
      accessorKey: "updated_time",
      header: ({ column }) => h(DataTableColumnHeader<SystemConfig>, { column, title: "Updated" }),
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
        h(RowActions, {
          config: row.original,
          onEdit,
          onDelete,
        }),
    },
  ];
}
