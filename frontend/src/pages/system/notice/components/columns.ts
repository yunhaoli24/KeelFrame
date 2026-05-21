import type { ColumnDef } from "@tanstack/vue-table";

import { h } from "vue";

import DataTableColumnHeader from "@/components/data-table/column-header.vue";
import { Badge } from "@/components/ui/badge";
import type { Notice } from "@/services/api/system/notice/notices.api";

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

function getNoticeTypeLabel(type: number) {
  return type === 1 ? "公告" : "通知";
}

function getNoticeStatusLabel(status: number) {
  return status === 1 ? "显示" : "隐藏";
}

export function createColumns({
  onEdit,
  onDelete,
}: {
  onEdit: (notice: Notice) => void;
  onDelete: (notice: Notice) => void;
}): ColumnDef<Notice>[] {
  return [
    {
      accessorKey: "title",
      header: ({ column }) => h(DataTableColumnHeader<Notice>, { column, title: "Title" }),
      cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("title")),
    },
    {
      accessorKey: "type",
      header: ({ column }) => h(DataTableColumnHeader<Notice>, { column, title: "Type" }),
      cell: ({ row }) => {
        const type = row.original.type;
        return h(Badge, { variant: type === 1 ? "default" : "secondary" }, () =>
          getNoticeTypeLabel(type),
        );
      },
    },
    {
      accessorKey: "status",
      header: ({ column }) => h(DataTableColumnHeader<Notice>, { column, title: "Status" }),
      cell: ({ row }) => {
        const status = row.original.status;
        return h(Badge, { variant: status === 1 ? "default" : "outline" }, () =>
          getNoticeStatusLabel(status),
        );
      },
    },
    {
      accessorKey: "content",
      header: ({ column }) => h(DataTableColumnHeader<Notice>, { column, title: "Content" }),
      cell: ({ row }) => {
        const content = row.original.content;
        return h("div", { class: "max-w-[400px] truncate text-muted-foreground" }, content || "-");
      },
    },
    {
      accessorKey: "updated_time",
      header: ({ column }) => h(DataTableColumnHeader<Notice>, { column, title: "Updated" }),
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
          notice: row.original,
          onEdit,
          onDelete,
        }),
    },
  ];
}
