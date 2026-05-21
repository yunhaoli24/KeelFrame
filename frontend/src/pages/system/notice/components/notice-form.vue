<script setup lang="ts">
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";

import { FormField } from "@/components/ui/form";

import type { Notice, NoticePayload } from "@/services/api/system/notice/notices.api";

const props = defineProps<{
  notice: Notice | null;
  loading?: boolean;
}>();

const emits = defineEmits<{
  (e: "submit", payload: NoticePayload): void;
}>();

const formSchema = toTypedSchema(
  z.object({
    title: z.string().trim().min(1, "Please enter a title."),
    type: z.number().int().min(0).max(1),
    status: z.number().int().min(0).max(1),
    content: z.string().trim().min(1, "Please enter content."),
  }),
);

function getInitialValues(notice: Notice | null) {
  return {
    title: notice?.title ?? "",
    type: notice?.type ?? 0,
    status: notice?.status ?? 1,
    content: notice?.content ?? "",
  };
}

const { handleSubmit, resetForm } = useForm({
  validationSchema: formSchema,
  initialValues: getInitialValues(props.notice),
});

watch(
  () => props.notice,
  (notice) => {
    resetForm({ values: getInitialValues(notice) });
  },
  { immediate: true },
);

const onSubmit = handleSubmit((values) => {
  const payload: NoticePayload = {
    title: values.title.trim(),
    type: values.type as 0 | 1,
    status: values.status as 0 | 1,
    content: values.content.trim(),
  };

  emits("submit", payload);
});
</script>

<template>
  <form class="space-y-6" @submit="onSubmit">
    <FormField v-slot="{ componentField }" name="title">
      <UiFormItem>
        <UiFormLabel>Title</UiFormLabel>
        <UiFormControl>
          <UiInput v-bind="componentField" placeholder="Notice title" :disabled="loading" />
        </UiFormControl>
        <UiFormMessage />
      </UiFormItem>
    </FormField>

    <div class="grid gap-4 md:grid-cols-2">
      <FormField v-slot="{ componentField }" name="type">
        <UiFormItem>
          <UiFormLabel>Type</UiFormLabel>
          <UiFormControl>
            <UiSelect v-bind="componentField" :disabled="loading">
              <UiSelectTrigger>
                <UiSelectValue placeholder="Select type" />
              </UiSelectTrigger>
              <UiSelectContent>
                <UiSelectItem :value="0">通知</UiSelectItem>
                <UiSelectItem :value="1">公告</UiSelectItem>
              </UiSelectContent>
            </UiSelect>
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="status">
        <UiFormItem>
          <UiFormLabel>Status</UiFormLabel>
          <UiFormControl>
            <UiSelect v-bind="componentField" :disabled="loading">
              <UiSelectTrigger>
                <UiSelectValue placeholder="Select status" />
              </UiSelectTrigger>
              <UiSelectContent>
                <UiSelectItem :value="1">显示</UiSelectItem>
                <UiSelectItem :value="0">隐藏</UiSelectItem>
              </UiSelectContent>
            </UiSelect>
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>
    </div>

    <FormField v-slot="{ componentField }" name="content">
      <UiFormItem>
        <UiFormLabel>Content</UiFormLabel>
        <UiFormControl>
          <UiTextarea
            v-bind="componentField"
            placeholder="Notice content"
            rows="8"
            :disabled="loading"
          />
        </UiFormControl>
        <UiFormMessage />
      </UiFormItem>
    </FormField>

    <div class="flex justify-end gap-2">
      <UiButton type="submit" :disabled="loading">
        <UiSpinner v-if="loading" class="mr-2" />
        Save
      </UiButton>
    </div>
  </form>
</template>
