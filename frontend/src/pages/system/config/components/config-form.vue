<script setup lang="ts">
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";

import { FormField } from "@/components/ui/form";

import type {
  SystemConfig,
  SystemConfigPayload,
} from "@/services/api/system/config/system-configs.api";

const props = defineProps<{
  config: SystemConfig | null;
  loading?: boolean;
}>();

const emits = defineEmits<{
  (e: "submit", payload: SystemConfigPayload): void;
}>();

const formSchema = toTypedSchema(
  z.object({
    name: z.string().trim().min(1, "Please enter a name."),
    type: z.string().optional(),
    key: z.string().trim().min(1, "Please enter a key."),
    value: z.string().trim().min(1, "Please enter a value."),
    is_frontend: z.boolean(),
    remark: z.string().optional(),
  }),
);

function getInitialValues(config: SystemConfig | null) {
  return {
    name: config?.name ?? "",
    type: config?.type ?? "",
    key: config?.key ?? "",
    value: config?.value ?? "",
    is_frontend: config?.is_frontend ?? false,
    remark: config?.remark ?? "",
  };
}

const { handleSubmit, resetForm } = useForm({
  validationSchema: formSchema,
  initialValues: getInitialValues(props.config),
});

watch(
  () => props.config,
  (config) => {
    resetForm({ values: getInitialValues(config) });
  },
  { immediate: true },
);

const onSubmit = handleSubmit((values) => {
  const payload: SystemConfigPayload = {
    name: values.name.trim(),
    key: values.key.trim(),
    value: values.value.trim(),
    is_frontend: values.is_frontend,
    type: values.type?.trim() ? values.type.trim() : null,
    remark: values.remark?.trim() ? values.remark.trim() : null,
  };

  emits("submit", payload);
});
</script>

<template>
  <form class="space-y-6" @submit="onSubmit">
    <div class="grid gap-4 md:grid-cols-2">
      <FormField v-slot="{ componentField }" name="name">
        <UiFormItem>
          <UiFormLabel>Name</UiFormLabel>
          <UiFormControl>
            <UiInput v-bind="componentField" placeholder="Config name" :disabled="loading" />
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="type">
        <UiFormItem>
          <UiFormLabel>Type</UiFormLabel>
          <UiFormControl>
            <UiInput v-bind="componentField" placeholder="Optional type" :disabled="loading" />
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="key">
        <UiFormItem>
          <UiFormLabel>Key</UiFormLabel>
          <UiFormControl>
            <UiInput v-bind="componentField" placeholder="config.key" :disabled="loading" />
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="value">
        <UiFormItem class="md:col-span-2">
          <UiFormLabel>Value</UiFormLabel>
          <UiFormControl>
            <UiTextarea v-bind="componentField" placeholder="Config value" :disabled="loading" />
          </UiFormControl>
          <UiFormMessage />
        </UiFormItem>
      </FormField>
    </div>

    <FormField v-slot="{ handleChange, value }" type="checkbox" name="is_frontend">
      <UiFormItem class="flex items-center justify-between gap-4 rounded-lg border p-4">
        <div class="space-y-1">
          <UiFormLabel>Expose to frontend</UiFormLabel>
          <UiFormDescription>Allow the frontend to read this config.</UiFormDescription>
        </div>
        <UiFormControl>
          <UiSwitch :checked="value" :disabled="loading" @update:checked="handleChange" />
        </UiFormControl>
      </UiFormItem>
    </FormField>

    <FormField v-slot="{ componentField }" name="remark">
      <UiFormItem>
        <UiFormLabel>Remark</UiFormLabel>
        <UiFormControl>
          <UiTextarea v-bind="componentField" placeholder="Optional remark" :disabled="loading" />
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
